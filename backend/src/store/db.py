import chromadb

chroma_client = chromadb.Client()

collection = chroma_client.create_collection(name="my_collection")


collection.add(
    embeddings=
    ids=["id1", "id2"],
    documents=[
        "日本の首都は東京です",
        "今日はバナナを2本食べました"
    ]
)

results = collection.query(
    query_texts=["日本の首都はどこですか"],
    n_results=2
)
print(results)
