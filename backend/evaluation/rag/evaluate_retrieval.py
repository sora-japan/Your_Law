import json
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from evaluation.rag.eval_data import load_eval_set
from src import config
from src.embedding.embedding import load_model
from src.store import db
from evaluation.rag.metrics import find_rank, calculate_recall_at_k, reciprocal_rank, calculate_mrr


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
    args = parser.parse_args()

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    answerable = {k: v for k, v in eval_set.items() if v['gold']}
    print(f'評価した問題数 :{len(answerable)} / {len(eval_set)}')

    model = load_model(config.EMBEDDING_MODEL)
    client = db.create_persistent_client(config.CHROMA_DIR)
    collection = db.get_collection(client, args.name)

    method = 'vector'
    timestamp = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d-%H%M')
    file_name = f'retrieval_{args.name}_{method}_{timestamp}.jsonl'
    records = []
    for eval_id, row in answerable.items():
        retrieved = db.search(collection, model, row['question'], max(config.EVAL_K_LIST))
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
