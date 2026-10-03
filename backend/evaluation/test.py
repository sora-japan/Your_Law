from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.streamers import BaseStreamer
import time
import psutil
import torch
import re
from itertools import product
import csv

class TimingStreamer(BaseStreamer):
    def __init__(self):
        self.start_time = 0.0
        self.ttft = 0.0
        self.token_counter = 0

    def put(self, value):
        if self.token_counter == 1:
            self.ttft = time.perf_counter() - self.start_time
        self.token_counter += 1

    def end(self):
        pass


def get_memory_usage():
    # 物理メモリ(RAM)消費量(GB換算)
    ram_gb = psutil.Process().memory_info().rss / (1024**3)
    # Apple shilicon GPU(MPS) 該当メモリ量(GB換算)
    mps_gb = torch.mps.current_allocated_memory() / (1024**3) if torch.backends.mps.is_available() else 0.0
    return ram_gb, mps_gb

init_ram, init_mps = get_memory_usage()
print(f"初期状態: RAM={init_ram:.2f}GB, MPS={init_mps:.2f}GB")

temperatures = [0.2, None]
top_ps = [0.5]
top_ks = [50]
rep_penalies = [1.1]

configs = [{"name": "Greedy", "do_sample": False}]
for temp, p, k, rep_pen in product(temperatures, top_ps, top_ks, rep_penalies):
    configs.append({
        "name": f"temperature: {temp}, top_p: {p}, top_k: {k}, repetition_penalty: {rep_pen}",
        "do_sample": True,
        "temperature": temp,
        "top_p": p,
        "top_k": k,
        "repetition_penalty": rep_pen
    })


model_name = "Qwen/Qwen3-8B"
# トークナイザーとモデルの読み込み
tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    pretrained_model_name_or_path=model_name,
    local_files_only=True,
).to('mps') # Apple SiliconのGPUを使用する

prompt = "訪問販売で契約した場合、クーリング・オフは何日以内にできますか。"
chat = [
    # これがないと、英語で回答してしまう
    {
        "role": "system",
        "content": "あなたは優秀な法的アシスタントです。質問に対する明確な回答本文のみを直接日本語で出力してください。"
    },
    {"role": "user", "content": prompt}
]

header = [
    "Name", "do_sample","temperature", "Top_p", "Top_k", "Repetition Penalty",
    "TTFT(ms)", "TPOT(ms)", "Latency(s)", "Speed(tok/s)",
    "Tokens", "RAM(GB)", "MPS(GB)", "Text"
]
with open('llm_benchmark.csv', 'w', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(header)

tokenized_input = tokenizer.apply_chat_template(chat, add_generation_prompt=True, tokenize=True, return_tensors="pt", return_dict=True).to(model.device)
# ウォームアップ
w_start = time.perf_counter()
_ = model.generate(
    **tokenized_input,
    max_new_tokens=256,
    do_sample=False
)
w_end = time.perf_counter()
w_time = w_end - w_start
print(w_time)

for config in configs:
    config_dict = {} 
    for k, v in config.items():
        if k == "name":
            continue
        if v is None:
            if k == "temperature":
                v = 1.0
            elif k == "top_p":
                v = 1.0
            elif k == "top_k":
                v = 0
            elif k == "repetition_penalty":
                v = 1.0
        config_dict.update({k: v})
    streamer = TimingStreamer()
    start = time.perf_counter()
    streamer.start_time = start
    generated_ids = model.generate(
        **tokenized_input,
        max_new_tokens=4096,
        streamer=streamer,
        **config_dict
    )
    end = time.perf_counter()
    load_ram, load_mps = get_memory_usage()

    output_ids = generated_ids[0][len(tokenized_input['input_ids'][0]):]
    output_text = tokenizer.decode(output_ids, skip_special_tokens=True)# decode側でskipするので、回答精度には影響しない
    clean_text = re.sub(r'<think>.*?</think>', '', output_text, flags=re.DOTALL).strip()
    latency = end - start
    ttft = streamer.ttft
    ttft_ms = ttft * 1000
    get_token = len(output_ids)
    if get_token > 1:
        tpot = ((latency - ttft) / (get_token - 1)) * 1000
    else:
        tpot = 0.0
    speed = get_token / latency

    data_raw = [
        config.get('name', ''), config_dict.get('do_sample', ''), config_dict.get('temperature', ''),
        config_dict.get('top_p', ''), config_dict.get('top_k', ''), config_dict.get('repetition_penalty', ''),
        round(ttft_ms, 1), round(tpot, 1), round(latency, 2), round(speed, 1),
        get_token, round(load_ram, 2), round(load_mps, 2), clean_text,
    ]
    with open ('llm_benchmark.csv', 'a', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(data_raw)

    print("===RAM・MPS / 処理時間=== ")
    print(f"モデルロード後: RAM={load_ram:.2f}GB, MPS={load_mps:.2f}GB")
    print(f"処理時間(レイテンシ)：{latency}秒")
    print(f"TTFT: {ttft_ms:.1f}ms")
    print(f"TPOT: {tpot:.1f}ms")
    print(f"Speed: {speed:.1f}tok/s")# １秒間に何トークン出せるか
    print("===テキスト=== ")
    print(clean_text)
    torch.mps.empty_cache()


gen_ram, gen_mps = get_memory_usage()
print(f"生成終了後: RAM={gen_ram:.2f}GB, MPS={gen_mps:.2f}GB")
