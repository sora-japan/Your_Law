"""閾値ごとのチャンク数を、全件と評価サブセットに分けて数える。

READMEに載せる数字を出すためのもの。
"""
from collections import Counter

from src import config
from src.ingestion.chunk_splitting import load_current_chunks
from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from src.ingestion.sub_set import load_subset_law_ids, select_sub_chunks


if __name__ == '__main__':
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    must_law_ids = collect_must_law_ids(eval_set)
    subset_definition = load_subset_law_ids(config.SUBSET_LAW_IDS_FILE)
    for threshold in [200, 500, 1000, 2000]:
        chunks = load_current_chunks(config.XML_DIR, threshold, config.REFERENCE_DATE)

        subset_chunks = select_sub_chunks(chunks, must_law_ids, subset_definition)

        print(f'閾値: {threshold}')
        print(f'全件: {len(chunks)}')
        print(f'サブセット: {len(subset_chunks)}')
        level_list_all = [chunk['level'] for chunk in chunks]
        print(f'levelの内訳(全件): {Counter(level_list_all)}')
        level_list_sub = [chunk['level'] for chunk in subset_chunks]
        print(f'levelの内訳(サブセット): {Counter(level_list_sub)}')
