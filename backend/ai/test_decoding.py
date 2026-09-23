import torch
import matplotlib.pyplot as plt
import japanize_matplotlib
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-8B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    pretrained_model_name_or_path=model_name,
).to('mps') # Apple SiliconのGPUを使用する


text = "日本の首都は"
encode_input = tokenizer(text, return_tensors='pt').to(model.device)

# model.forwardで次トークン予測のロジットを取得する
# テスト中は勾配を計算しないため、with torch.no_grad():をつける
with torch.no_grad():
    outputs = model.forward(**encode_input)
    last_logits = outputs.logits[0, -1]
    probabilities = torch.softmax(last_logits, dim=0)

# Top-10 token_ids
top_vals, top_ids = probabilities.topk(10)
top_vals = top_vals.detach().cpu().float().numpy()
top_ids = top_ids.detach().cpu().tolist()
lebels = [f"{tid}: {repr(tokenizer.decode([tid]))}" for tid in top_ids]

# Plot
# plt.figure(figsize=(10, 4))
# plt.bar(range(len(top_vals)), top_vals)
# plt.xticks(range(len(top_vals)), lebels, rotation=45, ha='right')
# plt.ylabel('Probability')
# plt.title('Top-10 token_ids')
# plt.tight_layout()
# plt.show()

# Compute top-10 distributions at two temperatures without re-running the model
temps = [0.8, 1.0, 2.0]
top_vals_list = []
labels_list = []

for T in temps:
    probs_T = (last_logits / T).softmax(dim=0)
    vals_T, ids_T = probs_T.topk(10)
    top_vals_list.append(vals_T.detach().cpu().float().numpy())
    labels_list.append([f"{tid}: {repr(tokenizer.decode([tid]))}" for tid in ids_T.detach().cpu().tolist()])

# Plot
fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
for ax, T, vals, labs in zip(axes, temps, top_vals_list, labels_list):
    ax.bar(range(len(vals)), vals)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labs, rotation=45, ha='right')
    ax.set_ylabel('Probability')
    ax.set_title(f'Top-10 token_ids (temperature={T})')

fig.tight_layout()
plt.show()
