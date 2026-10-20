"""埋め込みは一致するのかを検証

同一プロセス内で二回埋め込んで一致するか
プロセスを分けて二回実行して一致するか
"""
from src.embedding.embedding import load_model, embed_documents, embed_query
from src import config


if __name__ == '__main__':
    model = load_model(config.EMBEDDING_MODEL)
    document1 = embed_documents(model, ['日本の首都は東京です'])
    document2 = embed_documents(model, ['日本の首都は東京です'])
    query1 = embed_query(model, '日本の首都はどこですか？')
    query2 = embed_query(model, '日本の首都はどこですか？')
    print(document1.tolist())
    print(document2.tolist())
    print(query1.tolist())
    print(query2.tolist())
    if (document1 == document2).all():
        print('document 一致しています')
    if (query1 == query2).all():
        print('query 一致しています')
