# 正解データと検索結果が合っているかの判定
def is_match(gold: dict, retrieved_meta: dict) -> bool:
    """goldに書かれているキーだけを比較する。

    goldがlaw_idのみなら法令単位、3フィールドあれば条単位の判定になる
    """
    match = all(value == retrieved_meta.get(key) for key, value in gold.items())
    return match

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

if __name__ == '__main__':
    # 状況型（goldがlaw_idのみ）
    g1 = {'law_id': '409AC0000000123'}
    m1 = {'law_id': '409AC0000000123', 'provision': '本則', 'article_num': '27'}
    print(is_match(g1, m1))   # True を期待（law_idだけ見るので条が違っても一致）
    
    m2 = {'law_id': '325AC0000000201', 'provision': '本則', 'article_num': '6'}
    print(is_match(g1, m2))   # False を期待
    
    # 条文型（gold 3フィールド）
    g2 = {'law_id': '325AC0000000201', 'provision': '本則', 'article_num': '6'}
    print(is_match(g2, m2))   # True を期待
    m3 = {'law_id': '325AC0000000201', 'provision': '本則', 'article_num': '7'}
    print(is_match(g2, m3))   # False を期待（条が違う）
    m4 = {'law_id': '325AC0000000201', 'provision': '附則', 'article_num': '6'}
    print(is_match(g2, m4))   # False を期待（本則/附則が違う）
