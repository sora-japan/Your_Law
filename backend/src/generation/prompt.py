SYSTEM_PROMPT_NO_RAG = """あなたは優秀な法令アシスタントです。
回答には根拠となる法令名と条番号を示してください。
確実でない場合は、わからないと答えてください。"""

SYSTEM_PROMPT_RAG = """あなたは優秀な法令アシスタントです。
与えられた条文のみに基づいて答えてください。
回答には根拠となる法令名と条番号を示してください。
確実でない場合は、わからないと答えてください。"""


def build_context(search_results: list[dict]) -> str:
    """検索結果を、プロンプトに入れる文脈の文字列にする。

    1件ごとに通し番号と見出し(法令名・条項号・本則/附則)をつけて並べています。
    条項号は空でない階層だけを繋ぐ。チャンクは条・項・号・機械分割の
    4レベルに分かれており、条全体が1チャンクなら項番号が空になるため。

    項番号まで渡すのは、渡さないとモデルが本文中の「第一項」等の参照を
    そのチャンク自身の項番号と誤読するため。
    """
    prompt = ''
    prompt += '以下は検索された法令の条文です。\n'
    for i, search_result in enumerate(search_results, start=1):
        law_title = search_result['law_title']
        provision = search_result['provision']
        text = search_result['text']
        parts = []
        article_num = search_result.get('article_num')
        paragraph_num = search_result.get('paragraph_num')
        item_num = search_result.get('item_num')
        if article_num != '':
            article_str = f'第{article_num}条'
            parts.append(article_str)
        if paragraph_num != '':
            paragraph_str = f'第{paragraph_num}項'
            parts.append(paragraph_str)
        if item_num != '':
            item_str = f'第{item_num}号'
            parts.append(item_str)
        number_str = ''.join(parts)
        prompt += f"""
【{i}】{law_title} {number_str} ({provision})
{text}
"""
    return prompt


def build_user_prompt(question: str, context: str | None) -> str:
    """質問と文脈を1つのユーザープロンプトにする。contextがNoneならRAGはなし。

    contextにデフォルト値をつけないのは、渡し忘れが静かにRAGなしとして通る経路を作らないため。"""
    if context is None:
        return question
    prompt = f"""{context}
ユーザーの質問: {question}
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
    search_context = build_context(search_results)
    prompt = build_user_prompt(query_text, search_context)
    print(prompt)
