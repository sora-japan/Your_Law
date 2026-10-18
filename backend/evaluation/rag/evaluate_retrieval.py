import json

from evaluation.rag.eval_data import load_eval_set
from src import config
from src.embedding.embedding import load_model
from src.ingestion.chunk_splitting import load_current_chunks
from src.store import db
from src.ingestion.sub_set import create_sub_chunks
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
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    answerable = {k: v for k, v in eval_set.items() if v['gold']}
    print(f'評価した問題数 :{len(answerable)} / {len(eval_set)}')

    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    must_law_ids = set()
    for row in eval_set.values():
        for gold in row['gold']:
            must_law_ids.add(gold['law_id'])
    subset = create_sub_chunks(chunks, must_law_ids, config.SUBSET_TARGET_CHUNKS, config.SUBSET_SEED)
    model = load_model(config.EMBEDDING_MODEL)
    client = db.create_client()
    collection = db.create_collection(
        client, config.COLLECTION_NAME, config.DISTANCE_SPACE
    )
    added = db.add_chunks(collection, subset, model, config.BATCH_SIZE)
    count = collection.count()
    if count != added:
        print(f'警告: 投入{added}件に対しコレクションは{count}件。chunk_idが重複している可能性があります。')
    print(f'投入: {added} / コレクション数: {count}')

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
    with open(config.EVAL_RESULT_FILE, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    article = [r for r in records if r['category'] != 'situation']
    situation = [r for r in records if r['category'] == 'situation']
    print('条文型', summarize(article))
    print('状況型', summarize(situation))
