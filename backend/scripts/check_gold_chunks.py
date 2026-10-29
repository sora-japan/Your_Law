from src import config
from src.ingestion.chunk_splitting import find_current_version_paths, get_chunks_with_meta
from evaluation.rag.eval_data import load_eval_set, convert_dict, convert_jsonl
from evaluation.rag.metrics import is_match, find_rank, calculate_recall_at_k

RAG_RESULT_FILE = 'generation_rag_20261020.jsonl'

def collect_law_ids(eval_set: dict) -> set[str]:
    """評価セットのgoldに出てくる law_id を集める"""
    law_id_set = set()
    for row in eval_set.values():
        for gold in row['gold']:
            law_id_set.add(gold['law_id'])
    return law_id_set


def build_chunk_map(law_id_set: set[str]) -> dict:
    """対象法令だけをチャンクにして、chunk_idをキーにした辞書を返す。

    chunk_id は法令ファイルごとの連番なので、同じファイル・同じ閾値なら再現する。
    DBを引かずに、chunk_id からメタデータを復元できる。
    """
    chunk_map = {}
    for path in find_current_version_paths(config.XML_DIR, config.REFERENCE_DATE):
        file_law_id = path.stem.split('_')[0]
        if file_law_id not in law_id_set:
            continue
        for chunk in get_chunks_with_meta(path, config.CHUNK_THRESHOLD, config.REFERENCE_DATE):
            chunk_map[chunk['chunk_id']] = chunk
    return chunk_map


def resolve(chunk_ids: list[str], chunk_map: dict) -> list[dict]:
    """chunk_id のリストを、メタデータのリストに引き直す。"""
    resolved = []
    for chunk_id in chunk_ids:
        resolved.append(chunk_map.get(chunk_id, {}))
    return resolved


def format_location(meta: dict) -> str:
    """チャンクのメタデータを「項2号3」のような短い文字列にする"""
    parts = []
    paragraph_num = meta.get('paragraph_num', '')
    item_num = meta.get('item_num', '')
    if paragraph_num:
        parts.append(f'項{paragraph_num}')
    if item_num:
        parts.append(f'号{item_num}')
    if not parts:
        parts.append('条全体')
    return ''.join(parts)


if __name__ == '__main__':
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    rag_result = convert_dict(convert_jsonl(config.RESULTS_DIR / RAG_RESULT_FILE))
    chunk_map = build_chunk_map(collect_law_ids(eval_set))
    print(f'チャンク辞書: {len(chunk_map)}件')

    recall_list = []
    for eval_id, row in eval_set.items():
        if not row['gold']:
            continue
        resolved = resolve(rag_result[eval_id]['retrieved_chunk_ids'], chunk_map)
        recall = calculate_recall_at_k(row['gold'], resolved, config.GENERATION_K)
        recall_list.append(recall)
    mean_recall = sum(recall_list) / len(recall_list)
    print(f'条レベル Recall@{config.GENERATION_K}: {mean_recall:.3f} ({len(recall_list)}問)')
    print()

    for eval_id, row in eval_set.items():
        resolved = resolve(rag_result[eval_id]['retrieved_chunk_ids'], chunk_map)
        for gold in row['gold']:
            if not gold.get('article_num'):
                continue
            article_chunks = []
            for chunk in chunk_map.values():
                if is_match(gold, chunk):
                    article_chunks.append(chunk)
            arrived = []
            for rank, meta in enumerate(resolved, start=1):
                if is_match(gold, meta):
                    arrived.append(f'{rank}位:{format_location(meta)}')
            rank_value = find_rank([gold], resolved, config.GENERATION_K)
            print(f'{eval_id}\t{row['category']}\t第{gold['article_num']}条\t'
                  f'{len(article_chunks)}本\t順位{rank_value}\t{' '.join(arrived)}')
