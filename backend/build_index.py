from src import config
from src.embedding.embedding import load_model
from src.ingestion.chunk_splitting import load_current_chunks
from src.store import db


def build_index(limit: int | None) -> None:
    """チャンクを読み、埋め込んで、Chroma に投入する。"""
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD)
    print(f'チャンク数: {len(chunks)}')

    target = chunks if limit is None else chunks[:limit]
    print(f'投入対象: {len(target)}')

    model = load_model(config.EMBEDDING_MODEL)
    client = db.create_client()
    collection = db.create_collection(
        client, config.COLLECTION_NAME, config.DISTANCE_SPACE
    )
    added = db.add_chunks(collection, target, model, config.BATCH_SIZE)
    count = collection.count()
    if count != added:
        print(f'警告: 投入{added}件に対しコレクションは{count}件。chunk_idが重複している可能性があります。')
    print(f'投入: {added} / コレクション数: {count}')


if __name__ == '__main__':
    build_index(10000)
