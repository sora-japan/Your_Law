"""Legal Link の画面

実行した時点でモデルの読み込みが始まり、数十秒かかる。
"""
from collections.abc import Iterator
import gradio as gr

from src import config
from src.generation.prompt import SYSTEM_PROMPT_RAG
from src.question_answering import load_resources, search, generate

resources = load_resources(
    config.CHROMA_DIR,
    config.BATCH_SIZE,
    embedding_model_name=config.EMBEDDING_MODEL,
    cross_encoder_model_name=config.CROSS_ENCODER_MODEL,
    llm_model_name=config.LLM_MODEL,
    collection_name=config.COLLECTION_NAME,
)


def answer(question: str) -> Iterator[str]:
    """質問を受けて、回答を少しずつ返す。

    Gradio が送信ボタンから呼ぶ。
    Gradio は受け取ったもので置き換えるので、新しく出た分だけを返すと前の文が消える。
    そのため full += piece で足してから返す。
    計測値は画面に出さず、ターミナルに出力する。
    """
    if not question.strip():
        yield 'お手数ですが、具体的な質問内容をご提示ください。'
        return
    yield '検索中...'
    retrieved = search(resources, question, config.RETRIEVAL_K, config.GENERATION_K)
    yield '条文を読み込み中...'
    result = {}
    stream = generate(resources, question, config.GENERATE_PARAMS, retrieved, SYSTEM_PROMPT_RAG, False, result)
    full = ''
    for piece in stream:
        full += piece
        yield full
    print()
    for key in ['ttft', 'total_time', 'output_token', 'token_limit']:
        print(f'{key}: {result[key]}')


if __name__ == '__main__':
    with gr.Blocks(title='Legal Link') as demo:
        gr.Markdown('# Legal Link')
        gr.Markdown('あなたと法律をつなぐ')
        with gr.Group():
            question_box = gr.Textbox(label='質問', placeholder='訪問販売で契約した場合、申込みの撤回（クーリング・オフ）ができるのは書面を受領した日から何日以内ですか？')
            send = gr.Button('送信', variant='primary')
        gr.Markdown('### 回答')
        answer_box = gr.Markdown()
        send.click(answer, inputs=question_box, outputs=answer_box)
    demo.launch(server_port=26302)
