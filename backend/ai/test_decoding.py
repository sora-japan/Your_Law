import torch
import matplotlib.pyplot as plt
import japanize_matplotlib
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-8B"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    pretrained_model_name_or_path=model_name,
).to('mps') # Apple SiliconのGPUを使用する


text = "日本の首都は東京です"
encode_input = tokenizer(text, return_tensors='pt').to(model.device)

# model.forwardで次トークン予測のロジットを取得する
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
plt.figure(figsize=(10, 4))
plt.bar(range(len(top_vals)), top_vals)
plt.xticks(range(len(top_vals)), lebels, rotation=45, ha='right')
plt.ylabel('Probability')
plt.title('Top-10 token_ids')
plt.tight_layout()
plt.show()
