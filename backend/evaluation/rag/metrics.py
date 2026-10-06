# 正解データと検索結果が合っているかの判定
def is_match(gold: dict, retrieved_meta: dict) -> bool:
    law_id_match = (gold.get('law_id') == retrieved_meta.get('law_id'))
    provision_match = (gold.get('provision') == retrieved_meta.get('provision'))
    article_num_match = (gold.get('article_num') == retrieved_meta.get('article_num'))
    return law_id_match and provision_match and article_num_match

# 検索してきたリストと、正解データを比べて一致するものがあるか。あれば順位を返し、なければNoneを返す
def find_rank(gold_list: list[dict], retrieved_list: list[dict], k: int) -> int | None:
    for rank, retrieved_item in enumerate(retrieved_list[:k], start=1):
        for gold in gold_list:
            if is_match(gold, retrieved_item):
                return rank
    return None


def reciprocal_rank(rank: int | None) -> float:
    if rank is None:
        return 0.0
    return 1.0 / rank

# MRRを計算する関数
def calculate_mrr(rr_list: list[float]) -> float:
    if len(rr_list) == 0:
        return 0.0
    return sum(rr_list) / len(rr_list)

# Hit Rate@kを計算する関数
def calculate_hit_rate(hit_list: list[bool]) -> float:
    if len(hit_list) == 0:
        return 0.0
    return sum(hit_list) / len(hit_list)

def calculate_recall_at_k(gold_list: list[dict], retrieved_list: list[dict], k: int) -> float:
    gold_list_length = len(gold_list)
    if gold_list_length == 0:
        return 0.0
    hits = 0
    for gold in gold_list:
        for retrieved_item in retrieved_list[:k]:
            if is_match(gold, retrieved_item):
                hits += 1
                break
    return hits / gold_list_length 
