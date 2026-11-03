import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer


@dataclass
class Bm25Index:
    chunk_ids: list[str]
    metadatas: list[dict]
    matrix: csr_matrix
    vocabulary: dict[str, int]
    idf: np.ndarray
    documents_len: np.ndarray
    avgdl: float
    k1: float
    b: float


def bigram(text: str) -> list[str]:
    """文字列を2文字ずつに区切ったリストを返す。

    法令用語が辞書にない場合、変に区切られるため、
    形態素解析ではなく、文字2-gramを採用した。
    3-gramにすると「工事」「契約」のような2文字の熟語が索引を引けなくなる。

    句読点をまたぐ2-gram(「売。」など)はどの語の一部でもなく、文書長を水増しするので、
    先に切ってから作る。出現回数が必要なので、重複は取り除かない。
    """
    normalized_text = unicodedata.normalize('NFKC', text)
    clean_text = re.split('[、。・()「」]', normalized_text)
    result = []
    for clean in clean_text:
        # -1がないと、末尾に1文字だけの要素('す'など)が混ざる
        # 1文字のかたまりはrange(0)になり、何も作られずに消える
        result_text = [clean[i: i + 2] for i in range(len(clean) - 1)]
        result.extend(result_text)
    return result


def build_count_matrix(documents: list[str]) -> tuple[CountVectorizer, csr_matrix]:
    """文書を2-gramに分けて、文書×語の出現回数の疎行列を返す"""
    vectorizer = CountVectorizer(analyzer=bigram)
    matrix = vectorizer.fit_transform(documents)
    return vectorizer, matrix


def compute_idf(matrix: csr_matrix) -> np.ndarray:
    """語ごとのIDFを返す。列の順番は matrix と同じ。

    df が N の半分を超えると比が1を下回り、logが負になるので、+1をしてそれを防いでいる。
    0.5は平滑化で、df が小さいときの値を鈍らせる。
    """
    df = np.asarray((matrix > 0).sum(axis=0)).ravel()
    N = matrix.shape[0]
    idf = np.log((N - df + 0.5) / (df + 0.5) + 1)
    return idf


def compute_doc_lengths(matrix: csr_matrix) -> tuple[np.ndarray, float]:
    """文書ごとの語数と、その平均を返す。

    行方向に足すと、その文書に入っている語の総数になる。
    csr_matrix の sum は2次元で返るので、ravelで1次元にする。
    """
    documents_len = np.asarray(matrix.sum(axis=1)).ravel()
    avgdl = documents_len.mean()
    return documents_len, avgdl


def create_index(chunk_ids: list[str], documents: list[str], metadatas: list[dict], k1: float = 1.2, b: float = 0.75) -> Bm25Index:
    """文書からBM25の索引を作る。

    chunk_ids と documents と metadatas は、同じ位置が同じチャンクに対応している必要がある。
    ズレると検索結果が全く別のチャンクを指すため、構築時に止める。
    """
    if not (len(chunk_ids) == len(documents) == len(metadatas)):
        raise ValueError('chunk_idsの数とドキュメントとメタデータの数が合いません')
    vectorizer, matrix = build_count_matrix(documents)
    vocabulary = vectorizer.vocabulary_
    idf = compute_idf(matrix)
    documents_len, avgdl = compute_doc_lengths(matrix)
    return Bm25Index(
        chunk_ids=chunk_ids,
        metadatas=metadatas,
        matrix=matrix,
        vocabulary=vocabulary,
        idf=idf,
        documents_len=documents_len,
        avgdl=avgdl,
        k1=k1,
        b=b,
    )


def search(index: Bm25Index, query: str, k: int) -> list[dict]:
    """質問に近い文書を、スコアの大きい順にk件返す。

    1件はchunk_idとscoreとmetadataを持つ辞書。db.searchと形を揃えてあり、RRFで統合できる。

    質問を2-gramにし、語彙にある語の列だけを抜き出してから疎行列を密行列にする。

    スコア0は「質問の語が1つも含まれない」という意味で、同点が大量に並ぶ。
    スコア0の同点の順位は配列の位置で決まり、検索の結果になっていないため、除外する。
    降順に並べてあるので、0に当たった時点で以降も全て0になり、打ち切れる。
    """
    q_bigrams = bigram(query)
    cols = []
    for q_bigram in q_bigrams:
        col = index.vocabulary.get(q_bigram)
        if col is not None:
            cols.append(col)
    if not cols:
        return []
    tf = index.matrix[:, cols].toarray()
    numerator = tf * (index.k1 + 1)
    denominator = tf + index.k1 * (1 - index.b + index.b * index.documents_len[:, None] / index.avgdl)
    term_scores = index.idf[cols] * numerator / denominator
    scores = term_scores.sum(axis=1)
    top_index = np.argsort(-scores)[:k]
    query_ans = []
    for i in top_index:
        chunk_id = index.chunk_ids[i]
        score = scores[i]
        if score == 0.0:
            break
        query_ans.append({'chunk_id': chunk_id, 'score': float(score), **index.metadatas[i]})
    return query_ans


if __name__ == '__main__':
    text = ['販売販売販売', '通信販売', '消防設備']
    metadatas = [{'law_id': 'A'}, {'law_id': 'B'}, {'law_id': 'C'}]
    vectorizer, matrix = build_count_matrix(text)
    print(type(vectorizer))
    print(vectorizer.get_feature_names_out())
    idf = compute_idf(matrix)
    print('idf', idf)
    print(matrix.toarray())
    print(matrix)
    print(matrix > 0)
    df = np.asarray((matrix > 0).sum(axis=0)).ravel()
    print(df)
    print(df.shape)
    documents_len, avgdl = compute_doc_lengths(matrix)
    print(documents_len)
    print(avgdl)
    index = create_index(['a', 'b', 'c'], text, metadatas)
    print(index)
    query_ans = search(index, '販売について', k=10)
    print(query_ans)
