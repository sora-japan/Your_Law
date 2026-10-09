import chromadb
from src.embedding.embedding import embed_documents

# チャンクに必ず存在するキー、かけていたら前処理のバグなので、KeyErrorで落とす
REQUIRED_KEYS = (
    'level', 'provision', 'law_revision_id', 'enforce_date', 'is_current',
    'amend_law_id', 'is_extract', 'law_title', 'law_num', 'law_id', 'suppl_is_extract',
)

# 分割レベルによって存在しないキー。空文字で埋める
OPTIONAL_KEYS = ('article_num', 'paragraph_num', 'item_num', 'amend_law_num')


def create_client():
    return chromadb.Client()


def create_collection(client, name: str, space: str):
    return client.create_collection(name=name, metadata={'hnsw:space': space})


def build_metadata(chunk: dict) -> dict:
    """チャンクからChromaに渡すメタデータを作る"""
    metadata = {key: chunk[key] for key in REQUIRED_KEYS}
    for key in OPTIONAL_KEYS:
        metadata[key] = chunk.get(key, '')
    return metadata


def add_chunks(collection, chunks: list[dict], model, batch_size: int) -> int:
    """チャンクを埋め込んで投入する。投入件数を返す"""
    added = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        documents = [chunk['text'] for chunk in batch]
        collection.add(
            ids=[chunk['chunk_id'] for chunk in batch],
            embeddings=embed_documents(model, documents),
            documents=documents,
            metadatas=[build_metadata(chunk) for chunk in batch],
        )
        added += len(batch)
    return added
