import argparse

from src import config
from src.embedding.embedding import load_model
from src.ingestion.chunk_splitting import load_current_chunks
from src.store import db


def build_index(client, model, chunks: list[dict]):
    """渡されたチャンクを埋め込んでコレクションに投入し、コレクションを返す。

    どのチャンクを入れるか、どのクライアントを使うかは呼び出し側が決める。
    """
    meta = db.collection_metadata(config.EMBEDDING_MODEL, config.CHUNK_THRESHOLD, config.REFERENCE_DATE, len(chunks))
    name = db.collection_name(meta)
    collection = db.create_collection(client, name, config.DISTANCE_SPACE, meta)
    added = db.add_chunks(collection, chunks, model, config.BATCH_SIZE)
    count = collection.count()
    if count != added:
        print(f'警告: 投入{added}件に対しコレクションは{count}件。chunk_idが重複している可能性があります。')
    print(f'投入: {added} / コレクション数: {count}')
    return collection


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='法令チャンクを埋め込んでChromaに投入し、検索インデックスを構築する')
    # 引数なしで実行しても全件投入にならないようにdefault=10000にしています
    parser.add_argument('--limit', default=10000, type=int, help='投入するチャンク数の上限。全件投入は--limit 0')
    parser.add_argument('--save', action='store_true', help='Chromaに永続化する。指定しなければインメモリで、保存されない')
    args = parser.parse_args()

    model = load_model(config.EMBEDDING_MODEL)
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'チャンク数: {len(chunks)}')
    target = chunks if args.limit == 0 else chunks[:args.limit]
    print(f'投入対象: {len(target)}件 / 保存: {"する" if args.save else "しない(インメモリ)"}')
    client = db.create_persistent_client(config.CHROMA_DIR) if args.save else db.create_client()
    build_index(client, model, target)
