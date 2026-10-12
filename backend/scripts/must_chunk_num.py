from src import config
from src.ingestion.chunk_splitting import load_current_chunks
from collections import defaultdict
from evaluation.rag.evaluate_retrieval import convert_jsonl, convert_dict, JSONL_FILE 

if __name__ == '__main__':
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD)
    print(f'チャンク数: {len(chunks)}')

    # 法令IDごとにチャンクをまとめる
    chunks_by_law_id = defaultdict(list)
    for chunk in chunks:
        law_id = chunk['law_id']
        chunks_by_law_id[law_id].append(chunk)
    print(f'法令数: {len(chunks_by_law_id)}')

    # 評価データの gold から、必ず含める法令IDを集める
    eval_set = convert_dict(convert_jsonl(JSONL_FILE))
    must_law_ids = set()
    for _, v in eval_set.items():
        for gold in v['gold']:
            must_law_ids.add(gold['law_id'])

    # コーパスに存在しない gold があれば、ここで止める
    missing = must_law_ids - chunks_by_law_id.keys()
    if missing:
        raise ValueError(f'goldの法令がコーパスにありません: {sorted(missing)}')

    # 内訳と合計
    total = 0
    for law_id in sorted(must_law_ids):
        n = len(chunks_by_law_id[law_id])
        print(f'{law_id}: {n}')
        total += n
    print(f'必ず含めるチャンク数: {total}')
