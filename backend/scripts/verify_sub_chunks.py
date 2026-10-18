import pathlib

from src import config
from src.ingestion.chunk_splitting import load_current_chunks
from src.ingestion.sub_set import create_sub_chunks
from evaluation.rag.eval_data import convert_jsonl, convert_dict


def collect_must_law_ids(path: pathlib.Path) -> set[str]:
    """評価データのgoldに含まれる法令IDを集める"""
    eval_set = convert_dict(convert_jsonl(path))
    must_law_ids = set()
    for row in eval_set.values():
        for gold in row['gold']:
            must_law_ids.add(gold['law_id'])
    return must_law_ids


if __name__ == '__main__':
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD)
    must_law_ids = collect_must_law_ids(config.EVAL_SET_FILE)

    subset = create_sub_chunks(
        chunks, must_law_ids, config.SUBSET_TARGET_CHUNKS, config.SUBSET_SEED
    )
    chunk_ids = [chunk['chunk_id'] for chunk in subset]
    subset_law_ids = {chunk['law_id'] for chunk in subset}

    # 必ず含める法令が全て入っているか確認
    not_included = must_law_ids - subset_law_ids
    if not_included:
        raise AssertionError(f'必ず含める法令がかけています: {sorted(not_included)}')

    print(f'全チャンク数: {len(chunks)}')
    print(f'サブセットのチャンク数: {len(chunk_ids)}')
    print(f'サブセットの法令数: {len(subset_law_ids)}')
    print(f'必ず含める法令数: {len(must_law_ids)}')
    print(f'chunk_idの重複: {len(chunk_ids) - len(set(chunk_ids))}')

    for chunk_id in chunk_ids:
        print(chunk_id)
    # 以下をターミナルで打ち、差分が出るかを確認。
    # python3 -m scripts.verify_sub_chunks > run1.txt 
    # python3 -m scripts.verify_sub_chunks > run2.txt 
    # diff run1.txt run2.txt
