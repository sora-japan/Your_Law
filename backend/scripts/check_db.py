from src.store import db

if __name__ == '__main__':
    client = db.create_client()
    # collection = db.create_collection(client, 'test', 'cosine')
    collection = client.create_collection(
        name='test2',
        configuration={'hnsw': {'space': 'cosine', 'num_threads': 1}}
    )
    print(collection.configuration)
    # print(collection.metadata)
