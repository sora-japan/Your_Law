import chromadb
from src.embedding.embedding import embed_documents, embed_query

# チャンクに必ず存在するキー、かけていたら前処理のバグなので、KeyErrorで落とす
REQUIRED_KEYS = (
    'level', 'provision', 'law_revision_id', 'enforce_date', 'is_current',
    'amend_law_id', 'is_extract', 'law_title', 'law_num', 'law_id', 'suppl_is_extract',
)

# 分割レベルによって存在しないキー。空文字で埋める
OPTIONAL_KEYS = ('article_num', 'paragraph_num', 'item_num', 'amend_law_num')


def create_client():
    """インメモリのクライアントを返す。プロセスが終われば中身は消える。"""
    return chromadb.Client()


def create_persistent_client(path):
    """ChromaDBのデータをローカルのディスク上に保存・読み込みする"""
    return chromadb.PersistentClient(path=path)


def collection_metadata(model_name: str, chunk_threshold: int, reference_date: str, chunk_count: int) -> dict:
    """コレクションの中身を決める値。名前の組み立てにも使用する。

    build_chunk_metadata はチャンク1件ごとのメタデータだが、これはコレクション全体に1つ。
    chunk_countは実際に投入した件数。名前の末尾の数字がそのまま中身の件数になる。
    """
    metadata = {
        'model_name': model_name,
        'chunk_threshold': chunk_threshold,
        'reference_date': reference_date,
        'chunk_count': chunk_count,
    }
    return metadata


def collection_name(metadata: dict) -> str:
    """コレクションの名前をコレクションのメタデータから作成"""
    model = metadata['model_name'].split('/')[-1]
    chunk_threshold = metadata['chunk_threshold']
    reference_date = metadata['reference_date']
    chunk_count = metadata['chunk_count']
    name = f'{model}_{chunk_threshold}_{reference_date}_{chunk_count}'
    return name


def create_collection(client, name: str, space: str, metadata: dict):
    """コレクションを新しく作る"""
    return client.create_collection(
        name=name,
        configuration={'hnsw': {'space': space}},
        metadata=metadata,
    )


def build_chunk_metadata(chunk: dict) -> dict:
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
            metadatas=[build_chunk_metadata(chunk) for chunk in batch],
        )
        added += len(batch)
    return added


def get_collection(client, name: str):
    """保存済みのコレクションを開く"""
    return client.get_collection(name=name)


def search(collection, model, query_text: str, k: int) -> list[dict]:
    """クエリに近いチャンクをk件返す。距離の小さい順。

    1件は chunk_id / text / distance とメタデータ15キーを持つ辞書。
    """
    query_embeddings = embed_query(model, query_text)
    results = collection.query(
        query_embeddings=[query_embeddings],
        n_results=k
    )
    query_ans = []
    # results['ids']は[[1つ目]の質問の結果], [2つ目の質問の結果], ...]という形。
    # 質問を1つしか投げていないので、[0]で1つ目の結果だけを取り出す。
    ids = results['ids'][0]
    documents = results['documents'][0]
    distances = results['distances'][0]
    metadatas = results['metadatas'][0]
    for chunk_id, document, distance, metadata in zip(ids, documents, distances, metadatas):
        query_ans.append({'chunk_id': chunk_id, 'text': document, 'distance': distance, **metadata})
    return query_ans


if __name__ == '__main__':
    from src import config
    from src.embedding.embedding import load_model
    from src.ingestion.chunk_splitting import load_current_chunks

    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'チャンク数: {len(chunks)}')

    limit = 10
    target = chunks if limit is None else chunks[:limit]
    print(f'投入対象: {len(target)}')

    meta = collection_metadata(config.EMBEDDING_MODEL, config.CHUNK_THRESHOLD, config.REFERENCE_DATE, len(target))
    name = collection_name(meta)

    model = load_model(config.EMBEDDING_MODEL)
    client = create_client()
    collection = create_collection(
        client, name, config.DISTANCE_SPACE, meta
    )
    print(collection.metadata)
    print(collection.configuration)
    added = add_chunks(collection, target, model, config.BATCH_SIZE)
    count = collection.count()
    if count != added:
        print(f'警告: 投入{added}件に対しコレクションは{count}件。chunk_idが重複している可能性があります。')
    print(f'投入: {added} / コレクション数: {count}')

    query_text = '訪問販売で契約した場合、クーリング・オフは何日以内にできますか'

    search_result = search(collection, model, query_text, 3)
    print(search_result)
