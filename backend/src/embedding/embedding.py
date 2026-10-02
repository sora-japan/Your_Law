import chromadb
import torch
from sentence_transformers import SentenceTransformer
from src.ingestion.chunk_splitting import get_chunks_with_meta
import xml.etree.ElementTree as ET
import pathlib
import time
from datetime import datetime
from zoneinfo import ZoneInfo

BACKEND_DIR = pathlib.Path(__file__).parent.parent.parent
XML_DIR = BACKEND_DIR / 'data' / 'all_xml'
CHUNK_THRESHOLD = 1000
BATCH_SIZE = 1000

device = "mps" if torch.backends.mps.is_available() else "cpu"
model_name = "cl-nagoya/ruri-v3-310m"
model = SentenceTransformer(model_name, device=device)

all_chunks = []
today = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')
current_paths = {}
for path in XML_DIR.rglob('*.xml'):
    parts = path.stem.split('_')
    if parts[1] > today:
        continue
    if parts[0] not in current_paths or parts[1] > current_paths[parts[0]][0]:
        current_paths[parts[0]] = (parts[1], path)
for _, (_, path) in current_paths.items():
    all_chunks.extend(get_chunks_with_meta(path, CHUNK_THRESHOLD))

TARGET = all_chunks[:10000]

chroma_client = chromadb.Client()

collection = chroma_client.create_collection(
    name="my_collection",
    metadata={"hnsw:space": "cosine"}
)

start = time.perf_counter()

for i in range(0, len(TARGET), BATCH_SIZE):
    ids = []
    metadata = []
    batches = TARGET[i:i + BATCH_SIZE]
    for chunk in batches:
        metadatas_dist = {
            'level': chunk['level'],
            'provision': chunk['provision'],
            'law_revision_id': chunk['law_revision_id'],
            'article_num': chunk.get('article_num', ''),
            'paragraph_num': chunk.get('paragraph_num', ''),
            'item_num': chunk.get('item_num', ''),
            'enforce_date': chunk['enforce_date'],
            'is_current': chunk['is_current'],
            'amend_law_id': chunk['amend_law_id'],
            'amend_law_num': chunk.get('amend_law_num', ''),
            'is_extract': chunk['is_extract'],
            'law_title': chunk['law_title'],
            'law_id': chunk['law_id'],
            'law_num': chunk['law_num'],
            'suppl_is_extract': chunk['suppl_is_extract'],
            }
        metadata.append(metadatas_dist)
        ids.append(chunk['chunk_id'])
    add_documents = [chunk['text'] for chunk in batches]
    texts = ["検索文書: " + chunk['text'] for chunk in batches]
    embeddings = model.encode(texts, normalize_embeddings=True)
    collection.add(
        embeddings=embeddings,
        ids=ids,
        documents=add_documents,
        metadatas=metadata
    )
    if i % 1000 == 0:
        print(f'{i}/{len(all_chunks)}')

end = time.perf_counter()
print('処理時間を計測: ', '{:.2f}'.format((end-start)))

query_text = "検索クエリ: 職員の身分証明書の様式は？"
query_embeddings = model.encode(query_text, normalize_embeddings=True)
results = collection.query(
    query_embeddings=query_embeddings,
    n_results=3
)
print(results)
