import random
from collections import defaultdict

from src import config
from src.ingestion.chunk_splitting import load_current_chunks


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
