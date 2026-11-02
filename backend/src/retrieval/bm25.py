import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import CountVectorizer


@dataclass
class Bm25Index:
    chunk_ids: list[str]
    matrix: csr_matrix
    vocabulary: dict[str, int]
    idf: np.ndarray
    documents_len: np.ndarray
    avgdl: float
    k1: float
    b: float


def bigram(text: str) -> list[str]:
    normalized_text = unicodedata.normalize('NFKC', text)
    clean_text = re.split('[、。・()「」]', normalized_text)
    result = []
    for clean in clean_text:
        result_text = [clean[i: i + 2] for i in range(len(clean) - 1)]
        result.extend(result_text)
    return result


def build_count_matrix(documents: list[str]):
    """文書を2-gramに分けて、文書×語の出現回数の疎行列を返す"""
    vectorizer = CountVectorizer(analyzer=bigram)
    matrix = vectorizer.fit_transform(documents)
    return vectorizer, matrix


def compute_idf(matrix) -> np.ndarray:
    """語ごとのIDFを返す。列の順番は matrix と同じ。

    df が N の半分を超えると比が1を下回り、logが負になるので、+1をしてそれを防いでいる。
    0.5は平滑化で、df が小さいときの値を鈍らせる。
    """
    df = np.asarray((matrix > 0).sum(axis=0)).ravel()
    N = matrix.shape[0]
    idf = np.log((N - df + 0.5) / (df + 0.5) + 1)
    return idf


def compute_doc_lengths(matrix) -> tuple[np.ndarray, float]:
    """文書ごとの語数と、その平均を返す。

    行方向に足すと、その文書に入っている語の総数になる。
    csr_matrix の sum は2次元で返るので、ravelで1次元にする。
    """
    documents_len = np.asarray(matrix.sum(axis=1)).ravel()
    avgdl = documents_len.mean()
    return documents_len, avgdl


if __name__ == '__main__':
    text = ['販売販売販売', '通信販売', '消防設備']
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
