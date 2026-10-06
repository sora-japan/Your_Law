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

if __name__ == '__main__':
    # 正解データ（※複数正解があるケースを想定してリスト化）
    gold_dummy = [
        {"law_id": "123", "provision": "本則", "article_num": "2"}
    ]

    # 検索結果パターン1: 1位で正解
    retrieved_1st = [
        {"law_id": "123", "provision": "本則", "article_num": "2"}, # ←1位（正解）
        {"law_id": "999", "provision": "本則", "article_num": "1"}, # ←2位
        {"law_id": "888", "provision": "本則", "article_num": "5"}  # ←3位
    ]
    
    # 検索結果パターン2: 3位で正解
    retrieved_3rd = [
        {"law_id": "999", "provision": "本則", "article_num": "1"}, # ←1位
        {"law_id": "888", "provision": "本則", "article_num": "5"}, # ←2位
        {"law_id": "123", "provision": "本則", "article_num": "2"}  # ←3位（正解）
    ]
    
    rank1 = find_rank(gold_dummy, retrieved_1st, k=3)
    print(f"パターン1の順位: {rank1}")  # 期待値: 1
    
    rank3 = find_rank(gold_dummy, retrieved_3rd, k=3)
    print(f"パターン2の順位: {rank3}")  # 期待値: 3
    
    rank_miss = find_rank(gold_dummy, retrieved_3rd, k=2) 
    print(f"パターン3の順位: {rank_miss}")  # 期待値: None (正解は3位なので弾かれる)
