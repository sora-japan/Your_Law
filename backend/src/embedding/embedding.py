import torch
from sentence_transformers import SentenceTransformer


def select_device() -> str:
    """利用可能なデバイスを返す"""
    return 'mps' if torch.backends.mps.is_available() else 'cpu'


def load_model(model_name: str) -> SentenceTransformer:
    """エンべディングモデルの読み込み。初回時はモデルのダウンロードが発生する"""
    return SentenceTransformer(model_name, device=select_device())


def embed_documents(model: SentenceTransformer, texts: list[str]):
    """文書側のテキストをベクトル化。プレフィックスと正規化を行う"""
    prefixed = ['検索文書: ' + text for text in texts]
    return model.encode(prefixed, normalize_embeddings=True)


def embed_query(model: SentenceTransformer, text: str):
    """クエリ側のテキストをベクトル化。プレフィックスと正規化を行う。"""
    return model.encode('検索クエリ: ' + text, normalize_embeddings=True)


if __name__ == '__main__':
    from src.config import EMBEDDING_MODEL

    model = load_model(EMBEDDING_MODEL)
    doc_vectors = embed_documents(model, ["これは本文です。", "これも本文"])
    query_vector = embed_query(model, "本文について教えてください。")
    print(doc_vectors)
    print("文書ベクトル:", doc_vectors.shape)
    print("クエリベクトル:", query_vector.shape)
