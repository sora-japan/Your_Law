from transformers import AutoModelForCausalLM, AutoTokenizer
import time
import psutil
import torch
import re
from itertools import product


def get_memory_usage():
    # 物理メモリ(RAM)消費量(GB換算)
    ram_gb = psutil.Process().memory_info().rss / (1024**3)
    # Apple shilicon GPU(MPS) 該当メモリ量(GB換算)
    mps_gb = torch.mps.current_allocated_memory() / (1024**3) if torch.backends.mps.is_available() else 0.0
    return ram_gb, mps_gb

init_ram, init_mps = get_memory_usage()
print(f"初期状態: RAM={init_ram:.2f}GB, MPS={init_mps:.2f}GB")

temperatures = [0.2, None]
top_ps = [0.5, None]

configs = [{"name": "Greedy", "do_sample": False}]
for temp, p, in product(temperatures, top_ps):
    configs.append({
        "name": f"temperature: {temp}, top_p: {p}",
        "do_sample": True,
        "temperature": temp,
        "top_p": p,
    })


model_name = "Qwen/Qwen3-8B"
# トークナイザーとモデルの読み込み
tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    pretrained_model_name_or_path=model_name,
    local_files_only=True,
).to('mps') # Apple SiliconのGPUを使用する

prompt = "日本の民法における「契約」の成立要件について、簡潔に説明してください。"
chat = [
    # これがないと、英語で回答してしまう
    {
        "role": "system",
        "content": "あなたは優秀な法的アシスタントです。質問に対する明確な回答本文のみを直接日本語で出力してください。"
    },
    {"role": "user", "content": prompt}
]

tokenized_input = tokenizer.apply_chat_template(chat, add_generation_prompt=True, tokenize=True, return_tensors="pt", return_dict=True).to(model.device)
for config in configs:
    config_dict = {k: v for k, v in config.items() if k != "name" and v is not None}
    start = time.perf_counter()
    generated_ids = model.generate(
        **tokenized_input,
        max_new_tokens=4096,
        **config_dict
    )
    load_ram, load_mps = get_memory_usage()
    end = time.perf_counter()

    output_ids = generated_ids[0][len(tokenized_input['input_ids'][0]):]
    output_text = tokenizer.decode(output_ids, skip_special_tokens=True)# decode側でskipするので、回答精度には影響しない
    clean_text = re.sub(r'<think>.*?</think>', '', output_text, flags=re.DOTALL).strip()
    seconds = end - start

    print("===RAM・MPS / 処理時間=== ")
    print(f"モデルロード後: RAM={load_ram:.2f}GB, MPS={load_mps:.2f}GB")
    print(f"処理時間：{seconds}秒")
    print("===テキスト=== ")
    print(clean_text)


gen_ram, gen_mps = get_memory_usage()
print(f"生成終了後: RAM={gen_ram:.2f}GB, MPS={gen_mps:.2f}GB")
