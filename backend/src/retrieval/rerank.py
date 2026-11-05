from sentence_transformers import CrossEncoder
import numpy as np

from src import config
from src.embedding.embedding import select_device


def load_cross_encoder(model_name: str):
    """リランキング用のクロスエンコーダの読み込み"""
    return CrossEncoder(model_name, device=select_device())


def rerank(model, query: str, candidates: list[dict]) -> list[dict]:
    """質問と候補の本文をクロスエンコーダに通し、関連度の高い順に並べ替える。

    1件は candidates の辞書に rerank_score を足したもの。
    db.searchやrrfと形が揃っているので、そのまま次に渡せる。

    スコアは大きいほど関連が高いので、降順に並べる。
    件数では切らない。切るのは呼び出し側の仕事で、rrfと同じにしてある。
    """
    inputs = []
    for candidate in candidates:
        text = candidate['text']
        query_and_text = [query, text]
        inputs.append(query_and_text)
    scores = model.predict(inputs)
    top_index = np.argsort(-scores)
    rerank_ans = []
    for i in top_index:
        rerank_ans.append({**candidates[i], 'rerank_score': float(scores[i])})
    return rerank_ans


if __name__ == '__main__':
    model = load_cross_encoder(config.CROSS_ENCODER_MODEL)

    query = "瑠璃色はどんな色？"
    results = [
        {'text': "瑠璃色（るりいろ）は、紫みを帯びた濃い青。名は、半貴石の瑠璃（ラピスラズリ、英: lapis lazuli）による。JIS慣用色名では「こい紫みの青」（略号 dp-pB）と定義している[1][2]。"},
        {'text': "ワシ、タカ、ハゲワシ、ハヤブサ、コンドル、フクロウが代表的である。これらの猛禽類はリンネ前後の時代(17~18世紀)には鷲類・鷹類・隼類及び梟類に分類された。ちなみにリンネは狩りをする鳥を単一の目(もく)にまとめ、vultur(コンドル、ハゲワシ)、falco(ワシ、タカ、ハヤブサなど)、strix(フクロウ)、lanius(モズ)の4属を含めている。"},
    ]
    reranked = rerank(model, query, results)
    print(reranked)
