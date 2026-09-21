import chromadb
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from data.text_extraction import extract_text, normalization_text
import xml.etree.ElementTree as ET
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
XML_DIR = BASE_DIR / "token_file"

device = "mps" if torch.backends.mps.is_available() else "cpu"
model_name = "cl-nagoya/ruri-v3-310m"
model = SentenceTransformer(model_name, device=device)

result_text = []
result_file_name = []
result_article_num = []
for path in XML_DIR.rglob('*xml'):
    root = ET.parse(path).getroot()
    main = root.find('LawBody').find('MainProvision')
    for article in main.findall('.//Article'):
        text = normalization_text(extract_text(article))
        article_num = article.get('Num')
        result_text.append(text)
        result_file_name.append(path.stem + "-" + article_num)
        result_article_num.append(article_num)

encode_text = ["検索文書: " + r for r in result_text]
embeddings = model.encode(encode_text)

metadatas_article_num = [{"article_num": v} for v in result_article_num]

chroma_client = chromadb.Client()

collection = chroma_client.create_collection(name="my_collection")

collection.add(
    embeddings=embeddings,
    ids=result_file_name,
    documents=result_text,
    metadatas=metadatas_article_num
)

query_text = "検索クエリ: 職員の身分証明書の様式は？"

query_embeddings = model.encode(query_text)

results = collection.query(
    query_embeddings=query_embeddings,
    n_results=3
)
print(results)
