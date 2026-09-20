import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer

device = "mps" if torch.mps.is_available() else "cpu"
model = SentenceTransformer("cl-nagoya/ruri-v3-310m", device=device)

sentences = [
    "川べりでサーフボードを持った人たちがいます",
    "サーファーたちが川べりに立っています",
    "トピック: 瑠璃色のサーファー",
    "検索クエリ: 瑠璃色はどんな色？",
    "検索文書: 瑠璃色（るりいろ）は、紫みを帯びた濃い青。名は、半貴石の瑠璃（ラピスラズリ、英: lapis lazuli）による。JIS慣用色名では「こい紫みの青」（略号 dp-pB）と定義している[1][2]。",
]

embeddings = model.encode(sentences, convert_to_tensor=True)
print(embeddings.size())

similarities = F.cosine_similarity(
    embeddings.unsqueeze(0),
    embeddings.unsqueeze(1),
    dim=2
    )

print(similarities)
