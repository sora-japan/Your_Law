from src import config
from src.ingestion.chunk_splitting import load_current_chunks
from collections import defaultdict

if __name__ == '__main__':
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD)
    print(f'チャンク数: {len(chunks)}')

    law_id_key_chunk = defaultdict(list)

    MUST_LAW_ID = '351AC0000000057'
    for chunk in chunks:
        get_law_id = chunk['law_id']
        law_id_key_chunk[get_law_id].append(chunk)
    print(len(law_id_key_chunk[MUST_LAW_ID]))
    print(len(law_id_key_chunk))
