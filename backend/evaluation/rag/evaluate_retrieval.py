import json
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import time

from evaluation.rag.eval_data import load_eval_set
from src import config
from src.embedding.embedding import load_model
from src.store import db
from evaluation.rag.metrics import find_rank, calculate_recall_at_k, reciprocal_rank, calculate_mrr
from src.retrieval import bm25


def summarize(group: list[dict]) -> dict[str, float | int]:
    """問題ごとの結果をまとめて、グループ全体の Recall@k の平均と MRR を返す。"""
    rr_list = [reciprocal_rank(r['rank']) for r in group]
    result = {'question_num': len(group), 'mrr': calculate_mrr(rr_list)}
    for k in config.EVAL_K_LIST:
        recall_list = []
        for r in group:
            recall_list.append(r['recall'][str(k)])
        result[f'recall@{k}'] = sum(recall_list) / len(recall_list)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='保存済みコレクションから、検索の性能評価をする')
    parser.add_argument('name', help='評価するコレクションの名前')
    parser.add_argument('--method', default='vector', choices=['vector', 'bm25'], help='検索の仕方')
    args = parser.parse_args()

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    answerable = {k: v for k, v in eval_set.items() if v['gold']}
    print(f'評価した問題数 :{len(answerable)} / {len(eval_set)}')

    client = db.create_persistent_client(config.CHROMA_DIR)
    collection = db.get_collection(client, args.name)

    timestamp = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d-%H%M')
    file_name = f'retrieval_{args.name}_{args.method}_{timestamp}.jsonl'

    if args.method == 'vector':
        model = load_model(config.EMBEDDING_MODEL)
    elif args.method == 'bm25':
        start = time.perf_counter()
        chunk_ids, documents, metadatas = db.get_all_chunks(collection, config.BATCH_SIZE)
        bm25_index = bm25.create_index(chunk_ids, documents, metadatas)
        end = time.perf_counter()
        print(f'チャンクの取得と索引の構築: {end - start:.1f}秒')

    records = []
    for eval_id, row in answerable.items():
        if args.method == 'vector':
            retrieved = db.search(collection, model, row['question'], max(config.EVAL_K_LIST))
        elif args.method == 'bm25':
            retrieved = bm25.search(bm25_index, row['question'], max(config.EVAL_K_LIST))
        recall_result = {}
        for k in config.EVAL_K_LIST:
            recall = calculate_recall_at_k(row['gold'], retrieved, k)
            recall_result[str(k)] = recall
        records.append({
            'id': eval_id,
            'category': row['category'],
            'gold_num': len(row['gold']),
            'rank': find_rank(row['gold'], retrieved, max(config.EVAL_K_LIST)),
            'recall': recall_result,
        })
    with open(config.RESULTS_DIR / file_name, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    article = [r for r in records if r['category'] != 'situation']
    situation = [r for r in records if r['category'] == 'situation']
    print('条文型', summarize(article))
    print('状況型', summarize(situation))
