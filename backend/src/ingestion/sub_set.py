import random
from collections import defaultdict
import json
import pathlib


def group_chunks_by_law_id(chunks: list[dict]) -> dict[str, list[dict]]:
    """法令IDごとにチャンクをまとめる"""
    chunks_by_law_ids = defaultdict(list)
    for chunk in chunks:
        law_id = chunk['law_id']
        chunks_by_law_ids[law_id].append(chunk)
    return dict(chunks_by_law_ids)


def create_sub_chunks(chunks: list[dict], must_law_ids: set[str], target_num: int, seed: int) -> list[dict]:
    """target_num を目標件数とし、サブセットを作成する。

    選択の単位は法令にし、指定した法令は必ず含まれるようにしています。
    同じ入力・同じseedなら必ず同じ結果になるように
    候補の法令IDをsorted()で並べ、random.Random(seed)でサンプリングする。
    注意点として、件数は目標値ちょうどにはなりません。
    """
    chunks_by_law_ids = group_chunks_by_law_id(chunks)
    chunks_law_id_keys = chunks_by_law_ids.keys()
    # コーパスに存在しない gold があれば、ここで止める
    missing = must_law_ids - chunks_law_id_keys
    if missing:
        raise ValueError(f'goldの法令がコーパスにありません: {sorted(missing)}')
    result = []
    for law_id in sorted(must_law_ids):
        result.extend(chunks_by_law_ids[law_id])
    candidate_law_ids = chunks_law_id_keys - must_law_ids
    rng = random.Random(seed)
    shuffled_law_ids = rng.sample(sorted(candidate_law_ids), len(candidate_law_ids))
    for law_id in shuffled_law_ids:
        if len(result) >= target_num:
            break
        result.extend(chunks_by_law_ids[law_id])
    return result


def load_subset_law_ids(path: pathlib.Path) -> dict:
    """評価用コーパスに入れる法令IDのリストを読む。"""
    with open(path, 'r', encoding='utf-8') as f:
        subset_law_ids = json.load(f)
    return subset_law_ids


def select_sub_chunks(chunks: list[dict], must_law_ids: set[str], subset_definition: dict) -> list[dict]:
    """固定された法令IDのリストを使って、評価用のサブセットを作る。

    create_sub_chunks が法令をランダムに選ぶ側で、こちらは選ばれた結果を使う側。
    リストを固定するのは、閾値を変えた比較で評価コーパスの中身が動かないようにするため。
    """
    chunks_by_law_ids = group_chunks_by_law_id(chunks)
    chunks_law_id_keys = chunks_by_law_ids.keys()
    must_law_ids_missing = must_law_ids - chunks_law_id_keys
    if must_law_ids_missing:
        raise ValueError(f'goldの法令がコーパスにありません: {sorted(must_law_ids_missing)}')
    non_gold_law_ids = set(subset_definition['non_gold_law_ids'])
    non_gold_missing = non_gold_law_ids - chunks_law_id_keys
    if non_gold_missing:
        raise ValueError(
            f'subset_law_ids.jsonにある法令がコーパスにありません: {len(non_gold_missing)}件 '
            f'(先頭10件: {sorted(non_gold_missing)[:10]}) '
            'XMLの構成か基準日が変わった可能性があります。'
        )
    law_ids = must_law_ids | non_gold_law_ids
    result = []
    for law_id in sorted(law_ids):
        result.extend(chunks_by_law_ids[law_id])
    return result


if __name__ == '__main__':
    from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
    from src import config
    from src.ingestion.chunk_splitting import load_current_chunks

    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'チャンク数: {len(chunks)}')
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    must_law_ids = collect_must_law_ids(eval_set)

    target_num_sub_chunks = create_sub_chunks(chunks, must_law_ids, config.SUBSET_TARGET_CHUNKS, config.SUBSET_SEED)
    print(f'TARGET_NUMのチャンクの数: {len(target_num_sub_chunks)}')

    subset_definition = load_subset_law_ids(config.SUBSET_LAW_IDS_FILE)
    law_ids_sub_chunks = select_sub_chunks(chunks, must_law_ids, subset_definition)
    print(f'law_idsで引く形のチャンクの数：{len(law_ids_sub_chunks)}')

    old_chunk_ids = set()
    for chunk in target_num_sub_chunks:
        old_chunk_ids.add(chunk['chunk_id'])
    new_chunk_ids = set()
    for chunk in law_ids_sub_chunks:
        new_chunk_ids.add(chunk['chunk_id'])
    print(f'chunk_idの集合が一致: {old_chunk_ids == new_chunk_ids}')
