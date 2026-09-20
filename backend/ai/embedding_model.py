import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from data.text_extraction import extract_text, normalization_text
from transformers import AutoTokenizer
import xml.etree.ElementTree as ET
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
XML_DIR = BASE_DIR / "token_file"

device = "mps" if torch.mps.is_available() else "cpu"
model_name = "cl-nagoya/ruri-v3-310m"
model = SentenceTransformer(model_name, device=device)
tokenizer = AutoTokenizer.from_pretrained(model_name)

text = ""
result = []
for path in XML_DIR.rglob('*xml'):
    root = ET.parse(path).getroot()
    main = root.find('LawBody').find('MainProvision')
    for article in main.findall('.//Article'):
        text = normalization_text(extract_text(article))
        length = len(text)
        article_num = article.get('Num')
        encode = tokenizer.encode(text)
        result.append((path.stem, article_num, len(encode), len(encode)/length*100))

for r in sorted(result, key=lambda x: x[2]):
    print(r)

# print(text)
# print(len(text))
# encode = tokenizer.encode(text)
# print(len(encode))

# embeddings = model.encode(text, convert_to_tensor=True)
# print(embeddings.size())
# 
# similarities = F.cosine_similarity(
#     embeddings.unsqueeze(0),
#     embeddings.unsqueeze(1),
#     dim=2
#     )
# 
# print(similarities)
