import pathlib

from src import config
from src.ingestion.chunk_splitting import load_current_chunks
from src.ingestion.sub_set import create_sub_chunks
from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from collections import Counter
from evaluation.rag.metrics import is_match


if __name__ == '__main__':
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    must_law_ids = collect_must_law_ids(eval_set)

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

    must_chunks = [chunk for chunk in subset if chunk['law_id'] in must_law_ids]
    print(f'必ず含める法令のチャンク数: {len(must_chunks)}')
    print(f'サブセットに占める割合: {len(must_chunks) / len(subset) * 100:.1f}%')

    must_law_id_list = [chunk['law_id'] for chunk in must_chunks]
    must_counts = Counter(must_law_id_list)
    for law_id, n in must_counts.most_common():
        print(f'{law_id}: {n}件')

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    for eval_id, row in eval_set.items():
        for gold in row['gold']:
            hit_chunk_num = 0
            for chunk in subset:
                if is_match(gold, chunk):
                    hit_chunk_num += 1
            article = gold.get('article_num', '法令全体')
            print(f'{eval_id} {row['category']} 第{article}条 的{hit_chunk_num}個')

    # for chunk_id in chunk_ids:
    #     print(chunk_id)
    # 以下をターミナルで打ち、差分が出るかを確認。
    # python3 -m scripts.verify_sub_chunks > run1.txt 
    # python3 -m scripts.verify_sub_chunks > run2.txt 
    # diff run1.txt run2.txt
