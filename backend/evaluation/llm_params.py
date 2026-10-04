from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
from transformers.generation.streamers import BaseStreamer
import time
import psutil
import torch
from itertools import product
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

MAX_NEW_TOKENS = 4096

class TimingStreamer(BaseStreamer):
    def __init__(self, think_end_id):
        self.start_time = 0.0
        self.ttft = 0.0
        self.token_counter = 0
        self.ttfo = None
        self.think_end_id = think_end_id
        self.think_flag = False
        self.think_token_counter = 0

    def put(self, value):
        if self.token_counter == 0:
            self.token_counter += 1
            return
        now = time.perf_counter()
        token_id = value.item()
        if self.token_counter == 1:
            self.ttft = now - self.start_time
        if self.think_flag and self.ttfo is None:
            self.ttfo = now - self.start_time
        if token_id == self.think_end_id:
            self.think_flag = True
            self.think_token_counter = self.token_counter
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


temperatures = [0.2, 0.7, 1.2, None]
top_ps = [0.5, 0.9, None]
top_ks = [10, 50, 100, None]
rep_penalies = [0.9, 1.2, 1.5, None]

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
        "content": "あなたは優秀な法的アシスタントです。ユーザーからの質問に対して、関連する法令や制度を踏まえ、正確かつ分かりやすい日本語で回答してください。"
    },
    {"role": "user", "content": prompt}
]

header = [
    "Name", "do_sample","temperature", "Top_p", "Top_k", "Repetition Penalty",
    "TTFT(ms)", "TPOT(ms)", "TTFO(s)", "Latency(s)", "Total Tokens", "Think Tokens", "Answer Tokens", "Speed(tok/s)",
    "Hit Limit", "RAM(GB)", "MPS(GB)", "Think Text", "Answer Text"
]
today_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
file_name = "llm_benchmark" + "_" + today_str + ".csv"
with open(file_name, 'w', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(header)

tokenized_input = tokenizer.apply_chat_template(chat, add_generation_prompt=True, tokenize=True, return_tensors="pt", return_dict=True).to(model.device)
think_end_id = tokenizer.convert_tokens_to_ids("</think>")
# ウォームアップ
_ = model.generate(
    **tokenized_input,
    max_new_tokens=64,
    do_sample=False
)

for config in configs:
    set_seed(42)
    config_dict = {} 
    for k, v in config.items():
        if k == "name":
            continue
        if v is None:
            if k in ("temperature", "top_p", "repetition_penalty"):
                v = 1.0
            elif k == "top_k":
                v = 0
        config_dict.update({k: v})
    streamer = TimingStreamer(think_end_id)
    start = time.perf_counter()
    streamer.start_time = start
    try:
        generated_ids = model.generate(
            **tokenized_input,
            max_new_tokens=MAX_NEW_TOKENS,
            streamer=streamer,
            **config_dict
        )
    except Exception as e:
        end = time.perf_counter()
        error_message = f"ERROR: {type(e)}: {e}"
        error_row = [
            config.get('name', ''), config_dict.get('do_sample', ''), config_dict.get('temperature', ''),
            config_dict.get('top_p', ''), config_dict.get('top_k', ''), config_dict.get('repetition_penalty', ''),
            "", "", "", round(end - start, 2), "", "", "", "",
            "", "", "", "", error_message,
        ]
        with open (file_name, 'a', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(error_row)
        print(f"===エラー=== {config.get('name', '')}")
        print(error_message)
        torch.mps.empty_cache()
        continue
    end = time.perf_counter()
    load_ram, load_mps = get_memory_usage()

    output_ids = generated_ids[0][len(tokenized_input['input_ids'][0]):]
    total_token = len(output_ids)

    hit_limit = total_token >= MAX_NEW_TOKENS
    if streamer.think_flag:
        think_tokens = streamer.think_token_counter
        answer_ids = output_ids[think_tokens:]
        clean_text = tokenizer.decode(answer_ids, skip_special_tokens=True).strip()
        think_ids = output_ids[:think_tokens]
        think_text = tokenizer.decode(think_ids, skip_special_tokens=True).strip()
    else:
        think_text = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        think_tokens = total_token
        clean_text = "(思考の途中で上限に到達)"
    answer_tokens = total_token - think_tokens
    latency = end - start
    ttft = streamer.ttft
    ttft_ms = ttft * 1000
    if total_token > 1:
        tpot = ((latency - ttft) / (total_token - 1)) * 1000
    else:
        tpot = 0.0
    speed = total_token / latency
    ttfo = round(streamer.ttfo, 2) if streamer.ttfo is not None else ""
    data_raw = [
        config.get('name', ''), config_dict.get('do_sample', ''), config_dict.get('temperature', ''),
        config_dict.get('top_p', ''), config_dict.get('top_k', ''), config_dict.get('repetition_penalty', ''),
        round(ttft_ms, 1), round(tpot, 1), ttfo, round(latency, 2), total_token, think_tokens, answer_tokens, round(speed, 1),
        hit_limit, round(load_ram, 2), round(load_mps, 2), think_text, clean_text,
    ]
    with open (file_name, 'a', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(data_raw)

    print("===RAM・MPS / 処理時間=== ")
    print(f"モデルロード後: RAM={load_ram:.2f}GB, MPS={load_mps:.2f}GB")
    print(f"処理時間(レイテンシ)：{latency}秒")
    print(f"TTFT: {ttft_ms:.1f}ms")
    print(f"TPOT: {tpot:.1f}ms")
    print(f"Speed: {speed:.1f}tok/s")# １秒間に何トークン出せるか
    print(f"TTFO: {ttfo}s")
    print(f"think token: {think_tokens}")
    print("===テキスト=== ")
    print(clean_text)
    torch.mps.empty_cache()


gen_ram, gen_mps = get_memory_usage()
print(f"生成終了後: RAM={gen_ram:.2f}GB, MPS={gen_mps:.2f}GB")
