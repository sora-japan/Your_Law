from transformers import AutoModelForCausalLM, AutoTokenizer
import time
import psutil
import torch
import re

def get_memory_usage():
    # 物理メモリ(RAM)消費量(GB換算)
    ram_gb = psutil.Process().memory_info().rss / (1024**3)
    # Apple shilicon GPU(MPS) 該当メモリ量(GB換算)
    mps_gb = torch.mps.current_allocated_memory() / (1024**3) if torch.backends.mps.is_available() else 0.0
    return ram_gb, mps_gb


init_ram, init_mps = get_memory_usage()
print(f"初期状態: RAM={init_ram:.2f}GB, MPS={init_mps:.2f}GB")

model_name = "Qwen/Qwen3-8B"
# トークナイザーとモデルの読み込み
tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    pretrained_model_name_or_path=model_name,
    local_files_only=True,
).to('mps') # Apple SiliconのGPUを使用する

prompt = "日本の民法における「契約」の成立要件について、簡潔に説明してください。"
chat = [
    # これがないと、英語で回答しちゃう
    {
        "role": "system",
        # "content": "あなたは日本の法律の専門家です。思考プロセス（<think>～</think>内）も含め、すべての出力を日本語で行ってください。"
        "content": "あなたは優秀な法的アシスタントです。思考プロセス（<think>）を出力せず、質問に対する明確な回答本文のみを直接日本語で出力してください。"
    },
    {"role": "user", "content": prompt}
]
start = time.perf_counter()

tokenized_input = tokenizer.apply_chat_template(chat, add_generation_prompt=True, tokenize=True, return_tensors="pt").to(model.device)
generated_ids = model.generate(
    **tokenized_input,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.7,
    top_p=0.5
)

end = time.perf_counter()
output_ids = generated_ids[0][len(tokenized_input['input_ids'][0]):]
output_text = tokenizer.decode(output_ids, skip_special_tokens=True)# decode側でskipするので、回答精度などは問題ない
clean_text = re.sub(r'<think>.*?</think>', '', output_text, flags=re.DOTALL).strip()
print(clean_text)

load_ram, load_mps = get_memory_usage()
print(f"モデルロード後: RAM={load_ram:.2f}GB, MPS={load_mps:.2f}GB")

seconds = end - start
print(f"処理時間：{seconds}秒")
gen_ram, gen_mps = get_memory_usage()
print(f"生成終了後: RAM={gen_ram:.2f}GB, MPS={gen_mps:.2f}GB")

# encoded_input = tokenizer(text, return_tensors='pt').to(model.device)
# output = model.generate(
#     **encoded_input,
#     max_new_tokens=128, # 生成するトークンの最大数
#     do_sample=True, # Trueに設定すると、「Multinomial Sampling」「Beam-Search Multinomial Sampling」「Top-K Sampling」「Top-p Sampling」などの戦略を有効にします。
#     temperature=0.7,
#     top_p=0.5,
# )
# 
# print("===")
# print(tokenizer.decode(output[0]))
# print("===encoded_input 出力結果===")
# print("全体のトークン数: ", len(output[0]))
# print("入力のトークン数: ", len(encoded_input['input_ids'][0]))
# generate_token = len(output[0]) - len(encoded_input['input_ids'][0])
# print("生成されたトークン数: ", generate_token)
# print("１秒あたりに生成されたトークン: ", generate_token / seconds)



# text = "日本の首都は"
# print(text)
# token_ids = tokenizer.encode(text)
# print(token_ids)
# for token_id in token_ids:
#     print(f"{token_id}: {repr(tokenizer.decode([token_id]))}")

# text = tokenizer.encode("大規模言語モデル")
# for token_id in text:
#     print(f"{token_id}: {repr(tokenizer.decode([token_id]))}")
# 
# print(tokenizer.vocab_size)
# 
# print(tokenizer.decode([0]))
# print(tokenizer.decode([50256]))
# 
# # Token embeddings
# token_id = 0
# print(tokenizer.decode([token_id]))
# embedding_table = model.get_input_embeddings().weight
# single_token_embedding = embedding_table[token_id]
# print(single_token_embedding.shape)
# print(single_token_embedding)
# 
# print("======")
# print(embedding_table)
