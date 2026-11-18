from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedTokenizerBase, PreTrainedModel, TextIteratorStreamer
import re
import time
from src import config
from threading import Thread
from collections.abc import Iterator

def load_tokenizer(model_name: str) -> PreTrainedTokenizerBase:
    """トークナイザーの読み込み"""
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    return tokenizer


def load_model(model_name: str) -> PreTrainedModel:
    """LLMモデルを読み込む"""
    model = AutoModelForCausalLM.from_pretrained(
        pretrained_model_name_or_path=model_name,
        local_files_only=True,
    ).to('mps') # Apple SiliconのGPUを使用する
    return model


def generate(model, tokenizer, system_prompt: str, prompt: str, gen_params: dict, enable_thinking: bool) -> dict:
    """生成が終わってから、回答の全文と計測値を返す。

    text は <think> から </think> までを除いたもの。
    generation_time は model.generate() だけを囲んだ時間で、
    トークン化とデコードを含まない。
    generate_stream の total_time とは測る範囲が違う。
    """
    chat = [
        {
            "role": "system",
            "content": system_prompt
        },
        {"role": "user", "content": prompt}
    ]
    tokenized_input = tokenizer.apply_chat_template(
        chat,
        enable_thinking=enable_thinking,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
    ).to(model.device)
    start = time.perf_counter()
    generated_ids = model.generate(
        **tokenized_input,
        **gen_params,
    )
    end = time.perf_counter()
    generation_time = end - start
    output_ids = generated_ids[0][len(tokenized_input['input_ids'][0]):]
    output_text = tokenizer.decode(output_ids, skip_special_tokens=True)
    clean_text = re.sub(r'<think>.*?</think>', '', output_text, flags=re.DOTALL).strip()
    output_length = len(output_ids)
    token_limit = output_length >= gen_params['max_new_tokens']
    result = {
        'text': clean_text,
        'output_token': output_length,
        'token_limit': token_limit,
        'generation_time': round(generation_time, 2),
    }
    return result


def generate_stream(model, tokenizer, system_prompt: str, prompt: str, gen_params: dict, enable_thinking: bool, result: dict) -> Iterator[str]: 
    """生成しながら、回答を少しずつ返す。

    回し終わると result に ttft / total_time / tokenize_time /
    output_token / token_limit が入る。
    生成が失敗した場合は、その例外をそのまま raise する。
    """
    chat = [
        {
            "role": "system",
            "content": system_prompt
        },
        {"role": "user", "content": prompt}
    ]
    start = time.perf_counter()
    tokenized_input = tokenizer.apply_chat_template(
        chat,
        enable_thinking=enable_thinking,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
    ).to(model.device)
    result['tokenize_time'] = round(time.perf_counter() - start, 3)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    generate_kwargs = {**tokenized_input, 'streamer': streamer, **gen_params}
    def run():
        try:
            result['generated_ids'] = model.generate(**generate_kwargs)
        except Exception as e:
            result['error'] = e
            streamer.end()
    thread = Thread(target=run)
    first_piece = True
    thread.start()
    for piece in streamer:
        if first_piece:
            result['ttft'] = round(time.perf_counter() - start, 3)
            first_piece = False
        yield piece
    result['total_time'] = round(time.perf_counter() - start, 3)
    thread.join()
    if result.get('error') is not None:
        raise result['error']
    input_length = len(tokenized_input['input_ids'][0])
    output_ids = result['generated_ids'][0][input_length:]
    result['output_token'] = len(output_ids)
    result['token_limit'] = result['output_token'] >= gen_params['max_new_tokens']


if __name__ == '__main__':
    tokenizer = load_tokenizer(config.LLM_MODEL)
    model = load_model(config.LLM_MODEL)
    print(model.dtype)
    prompt = '日本の民法における「契約」の成立要件について、簡潔に説明してください。'
    system_prompt = 'あなたは優秀な法的アシスタントです。ユーザーからの質問に対して、関連する法令や制度を踏まえ、正確かつ分かりやすい日本語で回答してください。'
    enable_thinking = False
    # gen_paramsは一旦仮置き
    gen_params = {
        'max_new_tokens': 512,
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 20,
    }
    KEYS = ['ttft', 'total_time', 'tokenize_time', 'output_token', 'token_limit', 'generated_ids', 'error']
    results = []
    for i in range(2):
        run_result = dict.fromkeys(KEYS)
        stream = generate_stream(model, tokenizer, system_prompt, prompt, gen_params, enable_thinking, run_result)
        for piece in stream:
            print(piece, end='', flush=True)
        print()
        results.append(run_result)
    print(results)
