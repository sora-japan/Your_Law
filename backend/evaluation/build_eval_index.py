import argparse

from build_index import build_index
from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from src.embedding.embedding import load_model
from src.ingestion.chunk_splitting import load_current_chunks
from src.ingestion.sub_set import create_sub_chunks
from src.store import db
from src import config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='法令チャンクを埋め込んでChromaに投入し、検索インデックスを構築する')
    parser.add_argument('--save', action='store_true', help='Chromaに永続化する。指定しなければインメモリで、保存されない')
    args = parser.parse_args()

    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'チャンク数: {len(chunks)}')

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    must_law_ids = collect_must_law_ids(eval_set)
    sub_chunks = create_sub_chunks(chunks, must_law_ids, config.SUBSET_TARGET_CHUNKS, config.SUBSET_SEED)

    print(f'投入対象: {len(sub_chunks)}件 / 保存: {"する" if args.save else "しない(インメモリ)"}')
    client = db.create_persistent_client(config.CHROMA_DIR) if args.save else db.create_client()

    model = load_model(config.EMBEDDING_MODEL)
    collection = build_index(client, model, sub_chunks)
    print(f'コレクション名: {collection.name}')
