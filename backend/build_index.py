import argparse

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
    parser = argparse.ArgumentParser(description='法令チャンクを埋め込んでChromaに投入し、検索インデックスを構築する')

    # 引数なしで実行しても全件投入にならないようにdefault=10000にしています
    parser.add_argument('--limit', default=10000, type=int, help='投入するチャンク数の上限。全件投入は--limit 0')
    args = parser.parse_args()
    # build_indexはNoneを全件の意味で受け取るので、0をNoneに変換する
    limit = None if args.limit == 0 else args.limit
    build_index(limit)
