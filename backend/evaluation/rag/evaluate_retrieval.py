from evaluation.rag.eval_data import load_eval_set
from src import config
from src.embedding.embedding import load_model
from src.ingestion.chunk_splitting import load_current_chunks
from src.store import db
from src.ingestion.sub_set import create_sub_chunks


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

    query_text = '訪問販売で契約した場合、クーリング・オフは何日以内にできますか'

    r5 = db.search(collection, model, query_text, 5)
    r10 = db.search(collection, model, query_text, 10)

    r5_result = [c['chunk_id'] for c in r5]
    print(r5_result)
    r10_result = [c['chunk_id'] for c in r10[:5]]
    print(r10_result)
    is_result = (r5_result == r10_result)
    print('一致: ', is_result)
