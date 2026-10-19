from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedTokenizerBase, PreTrainedModel
import re
import time
from src import config


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


if __name__ == '__main__':
    tokenizer = load_tokenizer(config.LLM_MODEL)
    model = load_model(config.LLM_MODEL)
    prompt = '日本の民法における「契約」の成立要件について、簡潔に説明してください。'
    system_prompt = 'あなたは優秀な法的アシスタントです。ユーザーからの質問に対して、関連する法令や制度を踏まえ、正確かつ分かりやすい日本語で回答してください。'
    enable_thinking = False
    # gen_paramsは一旦仮置き
    gen_params = {
        'max_new_tokens': 512,
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.5,
    }
    result = generate(model, tokenizer, system_prompt, prompt, gen_params, enable_thinking)
    print(result)
