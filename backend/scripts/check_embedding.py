"""埋め込みが壊れていないかを検証

1029bの実行で、ts005, ts024が同じ10件を返した。
その10件のベクトルが壊れていないかを調査する。
"""
import numpy as np

from src.embedding.embedding import load_model, embed_documents, embed_query
from src import config
from scripts.check_gold_chunks import build_chunk_map
from evaluation.rag.eval_data import load_eval_set


SUSPECT_CHUNK_IDS = [
    "325M50010000029_20190401_431M60000200023#6",
    "325M50010000029_20190401_431M60000200023#9",
    "420M60000080027_20080821_000000000000000#2",
    "342M50000010012_19790331_354M50000010016#9",
    "333M50000040019_20210901_503M60000040052#3",
    "362M50000100050_20260401_508M60000100051#58",
    "339M50001000016_20260615_508M60000008077#13",
    "339M50001000016_20260615_508M60000008077#18",
    "339M50001000016_20260615_508M60000008077#29",
    "427M60000100016_20251001_507M60000100086#65",
   ]


def report(labels: list[str], embeddings) -> None:
    """ベクトルが壊れていないかを調べ、該当した行の名前を出す"""
    has_nan = np.isnan(embeddings).any(axis=1)
    has_inf = np.isinf(embeddings).any(axis=1)
    norms = np.linalg.norm(embeddings, axis=1)
    off_norm = np.abs(norms - 1.0) > 0.01
    print(f'NaNを含む行: {has_nan.sum()} / {len(labels)}')
    print(f'Infを含む行: {has_inf.sum()} / {len(labels)}')
    print(f'ノルムが1.0からハズレ: {off_norm.sum()} / {len(labels)}')
    for n, label in enumerate(labels):
        if has_nan[n] or has_inf[n] or off_norm[n]:
            print(f'壊れている: {label} ノルム={norms[n]}')


if __name__ == '__main__':
    law_id_set = {chunk_id.split('_')[0] for chunk_id in SUSPECT_CHUNK_IDS}
    chunk_map = build_chunk_map(law_id_set)
    print(f'対象法令{len(law_id_set)}件 / チャンク辞書{len(chunk_map)}件')

    labels = []
    texts = []
    for chunk_id in SUSPECT_CHUNK_IDS:
        chunk = chunk_map.get(chunk_id)
        if chunk is None:
            print(f'辞書にない: {chunk_id}')
            continue
        labels.append(chunk_id)
        texts.append(chunk['text'])
    model = load_model(config.EMBEDDING_MODEL)

    print('怪しい10件の文書ベクトル')
    report(labels, embed_documents(model, texts))

    print('クエリ50問')
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    q_labels = []
    q_vectors = []
    for eval_id, row in eval_set.items():
        q_labels.append(eval_id)
        q_vectors.append(embed_query(model, row['question']))
    report(q_labels, np.array(q_vectors))

    seen = {}
    for label, vector in zip(q_labels, q_vectors):
        key = vector.tobytes()
        if key in seen:
            print(f'ベクトルが完全一致: {seen[key]} と {label}')
        seen[key] = label
