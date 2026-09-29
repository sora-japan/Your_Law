from transformers import AutoModelForCausalLM, AutoTokenizer
import time

model_name = "Qwen/Qwen3-8B"
# トークナイザーとモデルの読み込み
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    pretrained_model_name_or_path=model_name,
).to('mps') # Apple SiliconのGPUを使用する

text = "日本の首都は"
encoded_input = tokenizer(text, return_tensors='pt').to(model.device)
start = time.perf_counter()
output = model.generate(
    **encoded_input,
    max_new_tokens=128, # 生成するトークンの最大数
    do_sample=True, # Trueに設定すると、「Multinomial Sampling」「Beam-Search Multinomial Sampling」「Top-K Sampling」「Top-p Sampling」などの戦略を有効にします。
    temperature=0.7,
    top_p=0.5,
)

end = time.perf_counter()
seconds = end - start
print(f"処理時間：{seconds}秒")
print(tokenizer.decode(output[0]))
print("===encoded_input 出力結果===")
print("全体のトークン数: ", len(output[0]))
print("入力のトークン数: ", len(encoded_input['input_ids'][0]))
generate_token = len(output[0]) - len(encoded_input['input_ids'][0])
print("生成されたトークン数: ", generate_token)
print("１秒あたりに生成されたトークン: ", generate_token / seconds)

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

