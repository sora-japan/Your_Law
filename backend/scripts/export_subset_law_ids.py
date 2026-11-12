"""評価コーパスに入れる法令のIDを書き出す。1回だけ走らせるスクリプト。

閾値を変えた比較をする際、評価コーパスの中身が閾値で動いてしまう問題があった。
create_sub_chunks はチャンク数が目標に届くまで法令を足すため、閾値を上げると
1法令あたりのチャンクが減り、入る法令が増える。

法令IDを一度だけ確定させ、以降はそのリストでコーパスを決める。
リストは閾値1000で作る。この閾値で測った結果がすでにあり、
同じ法令集合になれば、その結果を使い続けられる。

評価セットを変えたときに、このリストを作り直さずに済むために
goldの法令は入れない。
"""
import json

from src.ingestion.sub_set import create_sub_chunks
from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from src import config
from src.ingestion.chunk_splitting import load_current_chunks

if __name__ == '__main__':
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'チャンク数: {len(chunks)}')

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    must_law_ids = collect_must_law_ids(eval_set)
    sub_chunks = create_sub_chunks(chunks, must_law_ids, config.SUBSET_TARGET_CHUNKS, config.SUBSET_SEED)
    law_id_set = set()
    for sub_chunk in sub_chunks:
        law_id_set.add(sub_chunk['law_id'])
    subset_law_ids = law_id_set - must_law_ids
    sorted_law_ids = sorted(subset_law_ids)
    print(f'法令の数: {len(sorted_law_ids)}')
    subset_definition = {
        'chunk_threshold': config.CHUNK_THRESHOLD,
        'reference_date': config.REFERENCE_DATE,
        'seed': config.SUBSET_SEED,
        'subset_target_chunks': config.SUBSET_TARGET_CHUNKS,
        'non_gold_law_ids': sorted_law_ids,
    }
    with open(config.SUBSET_LAW_IDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subset_definition, f, indent=2, ensure_ascii=False)

