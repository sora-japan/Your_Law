"""保存済みのコレクションに対して、検索だけの性能を測る。

--method vector ベクトル検索のみ
--method bm25 BM25(文字2-gram)のみ
--method hybrid 両方を検索してRRFで統合
--method hybrid-rerank hybrid の結果をクロスエンコーダで並べ替える
--method vector-rerank vector の結果をクロスエンコーダーで並べ替える

-rerank が付く方式は、付かない方式と同じ候補集合を扱う。
hybrid-rerank は RRF の戻り値、vector-rerank は db.search の戻り値を
そのままリランカーに渡すので、違うのは並べ方だけになる。

不可答5問は検索で測るものがないので、goldのある45問だけを対象にしている。
条文型と状況型を分けて集計する。
状況型のgoldはlaw_idのみで、「正しい法令を引けたか」を測っており、条単位の条文型とは別の指標になる。

固定名で上書きすると、構成を変えた測定のファイルが消えてしまうため、
出力は結果ごとに1ファイル。コレクション名・検索方式・実行時刻を名前に入れる。

vector-rerank は、候補の集め方だけを hybrid から vector に変えたもの。
並べ替えが同じなので、hybrid-rerank との差は候補の集め方から来ている。
"""
import json
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import time

from evaluation.rag.eval_data import load_eval_set
from evaluation.rag.metrics import find_rank, calculate_recall_at_k, reciprocal_rank, calculate_mrr
from src import config
from src.embedding.embedding import load_model
from src.store import db
from src.retrieval import bm25
from src.retrieval.rrf import rrf
from src.retrieval.rerank import rerank, load_cross_encoder


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
    parser.add_argument('--method', default='vector', choices=['vector', 'bm25', 'hybrid', 'hybrid-rerank', 'vector-rerank'], help='検索の仕方')
    args = parser.parse_args()

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    answerable = {k: v for k, v in eval_set.items() if v['gold']}
    print(f'評価した問題数 :{len(answerable)} / {len(eval_set)}')

    client = db.create_persistent_client(config.CHROMA_DIR)
    collection = db.get_collection(client, args.name)

    timestamp = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d-%H%M')
    file_name = f'retrieval_{args.name}_{args.method}_{timestamp}.jsonl'

    if args.method in ('vector', 'hybrid', 'hybrid-rerank', 'vector-rerank'):
        model = load_model(config.EMBEDDING_MODEL)

    if args.method in ('bm25', 'hybrid', 'hybrid-rerank'):
        start = time.perf_counter()
        chunk_ids, documents, metadatas = db.get_all_chunks(collection, config.BATCH_SIZE)
        bm25_index = bm25.create_index(chunk_ids, documents, metadatas)
        print(f'チャンクの取得と索引の構築: {time.perf_counter() - start:.1f}秒')

    if args.method in ('hybrid-rerank', 'vector-rerank'):
        cross_encoder_model = load_cross_encoder(config.CROSS_ENCODER_MODEL)

    records = []
    with open(config.RESULTS_DIR / file_name, 'w', encoding='utf-8') as f:
        for eval_id, row in answerable.items():
            search_start = time.perf_counter()
            if args.method in ('vector', 'vector-rerank'):
                retrieved = db.search(collection, model, row['question'], max(config.EVAL_K_LIST))
            elif args.method == 'bm25':
                retrieved = bm25.search(bm25_index, row['question'], max(config.EVAL_K_LIST))
            elif args.method in ('hybrid', 'hybrid-rerank'):
                vector_result = db.search(collection, model, row['question'], max(config.EVAL_K_LIST))
                bm25_result = bm25.search(bm25_index, row['question'], max(config.EVAL_K_LIST))
                retrieved = rrf(vector_result, bm25_result)
            search_time = time.perf_counter() - search_start
            rerank_time = None
            if args.method in ('hybrid-rerank', 'vector-rerank'):
                rerank_start = time.perf_counter()
                retrieved = rerank(cross_encoder_model, row['question'], retrieved)
                rerank_time = time.perf_counter() - rerank_start
            recall_result = {}
            for k in config.EVAL_K_LIST:
                recall = calculate_recall_at_k(row['gold'], retrieved, k)
                recall_result[str(k)] = recall
            record = {
                'id': eval_id,
                'category': row['category'],
                'gold_num': len(row['gold']),
                'rank': find_rank(row['gold'], retrieved, max(config.EVAL_K_LIST)),
                'recall': recall_result,
                'search_time': search_time,
                'rerank_time': rerank_time,
            }
            records.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f'{eval_id}完了 ({len(records)} / {len(answerable)})')

    article = [r for r in records if r['category'] != 'situation']
    situation = [r for r in records if r['category'] == 'situation']
    print('条文型', summarize(article))
    print('状況型', summarize(situation))
