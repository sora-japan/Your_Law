from collections import defaultdict

def rrf(vector_result: list[dict], bm25_result: list[dict], rrf_k: int = 60) -> list[dict]:
    """2つの計算結果を順位で統合し、新しい順位のリストを返す。

    score(文書) = Σ 1 / (rrf_k + 順位)

    スコアではなく順位を使う。BM25のスコアとベクトルの距離は単位が違い、
    質問ごとにスケールも変わるため、足し合わせられない。
    順位ならどちらの方式でも単位(1位など)の意味が同じになる。

    rrf_k は順位の効きを鈍らせる定数で、慣例は60。
    大きいほど上位の優位が薄まり「両方のリストに出ているか」が効く。
    """

    scores = defaultdict(float)
    hits = defaultdict(dict)
    for result in [vector_result, bm25_result]:
        for rank, hit in enumerate(result, start=1):
            chunk_id = hit['chunk_id']
            scores[chunk_id] += 1 / (rrf_k + rank)
            hits[chunk_id].update(hit)
    sorted_score = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    fused = []
    for chunk_id, score in sorted_score:
        fused.append({**hits[chunk_id], 'rrf_score': score})
    return fused


if __name__ == '__main__':
    vector_result = [
        {'chunk_id': 'a', 'law_id': 'X', 'provision': '本則', 'article_num': '1'},
        {'chunk_id': 'b', 'law_id': 'Y'},
        {'chunk_id': 'c', 'law_id': 'Z'},
    ]
    bm25_result = [
        {'chunk_id': 'c', 'law_id': 'Z'},
        {'chunk_id': 'a', 'law_id': 'X'},
        {'chunk_id': 'g', 'law_id': 'Y'},
    ]
    rrf_result = rrf(vector_result, bm25_result)
    print(rrf_result)
