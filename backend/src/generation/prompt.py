def build_context(search_results: list[dict]) -> str:
    """検索結果を、プロンプトに入れる文脈の文字列にする。

    1件ごとに通し番号と見出し(法令名・条番号・本則/附則)をつけて並べています。
    条番号を持たないチャンク(article_numが空文字)の時は、条番号を省いています。
    """
    prompt = ''
    prompt += '以下は検索された法令の条文です。\n'
    for i, search_result in enumerate(search_results, start=1):
        law_title = search_result['law_title']
        provision = search_result['provision']
        text = search_result['text']
        article_num = search_result.get('article_num')
        article_str = f'第{article_num}条' if article_num != '' else ''
        prompt += f"""
【{i}】{law_title} {article_str} ({provision})
{text}
"""
    return prompt


if __name__ == '__main__':
    from src import config
    from src.embedding.embedding import load_model
    from src.ingestion.chunk_splitting import load_current_chunks
    from src.store import db

    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'チャンク数: {len(chunks)}')

    limit = 10
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

    query_text = '訪問販売で契約した場合、クーリング・オフは何日以内にできますか'

    search_results = db.search(collection, model, query_text, 3)
    prompt = build_context(search_results)
    print(prompt)
