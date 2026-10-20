import json
from transformers import set_seed

from src import config
from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from evaluation.rag.metrics import reciprocal_rank, calculate_recall_at_k, find_rank, calculate_mrr 
from src.ingestion.sub_set import create_sub_chunks
from src.ingestion.chunk_splitting import load_current_chunks
from src.generation import llm
from src.generation.prompt import build_user_prompt, build_context, SYSTEM_PROMPT_NO_RAG, SYSTEM_PROMPT_RAG
from src.embedding import embedding
from src.store import db

USE_RAG = False

if __name__ == '__main__':
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    if USE_RAG:
        must_law_ids = collect_must_law_ids(eval_set)
        chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
        subset = create_sub_chunks(
            chunks, must_law_ids, config.SUBSET_TARGET_CHUNKS, config.SUBSET_SEED
        )
        embed_model = embedding.load_model(config.EMBEDDING_MODEL)
        client = db.create_client()
        collection = db.create_collection(
            client, config.COLLECTION_NAME, config.DISTANCE_SPACE
        )
        added = db.add_chunks(collection, subset, embed_model, config.BATCH_SIZE)
        count = collection.count()
        if count != added:
            print(f'警告: 投入{added}件に対しコレクションは{count}件。chunk_idが重複している可能性があります。')
        print(f'投入: {added} / コレクション数: {count}')

    tokenizer = llm.load_tokenizer(config.LLM_MODEL)
    llm_model = llm.load_model(config.LLM_MODEL)
    # Qwen3-8Bの思考なしの推奨値、set_seedで再現性を確保
    gen_params = {
        'max_new_tokens': 2048,
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 20,
    }
    records = []
    if USE_RAG:
        result_path = config.RESULTS_DIR / 'generation_rag_20261020.jsonl'
    else:
        result_path = config.RESULTS_DIR / 'generation_norag_20261020.jsonl'
    with open(result_path, 'w', encoding='utf-8') as f:
        for eval_id, row in eval_set.items():
            query_text = row['question']
            gold_law_ids = sorted({gold['law_id'] for gold in row['gold']})
            if USE_RAG:
                search_results = db.search(collection, embed_model, query_text, config.GENERATION_K)
                context = build_context(search_results)
                prompt = build_user_prompt(query_text, context)
                set_seed(42)
                generated = llm.generate(llm_model, tokenizer, SYSTEM_PROMPT_RAG, prompt, gen_params, False)
                if row['gold']:
                    rank = find_rank(row['gold'], search_results, config.GENERATION_K)
                    recall = calculate_recall_at_k(row['gold'], search_results, config.GENERATION_K)
                else:
                    rank = None
                    recall = None
                retrieved_chunk_ids = [c['chunk_id'] for c in search_results]
                record = {
                    'id': eval_id,
                    'category': row['category'],
                    'gold_law_ids': gold_law_ids,
                    'rank': rank,
                    'recall': recall,
                    'retrieved_chunk_ids': retrieved_chunk_ids,
                    **generated,
                }
            else:
                prompt = build_user_prompt(query_text, None)
                set_seed(42)
                generated = llm.generate(llm_model, tokenizer, SYSTEM_PROMPT_NO_RAG, prompt, gen_params, False)
                record = {
                    'id': eval_id,
                    'category': row['category'],
                    'gold_law_ids': gold_law_ids,
                    **generated,
                }
            records.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f'{eval_id}完了 ({len(records)} / {len(eval_set)})')
    print('===')
    answerable = [r for r in records if r['gold_law_ids']]
    hit_limit = [r for r in records if r['token_limit']]
    total_time = sum(r['generation_time'] for r in records)
    print(f'問題数: {len(records)} 可答問題数: {len(answerable)}')
    print(f'打ち切り: {len(hit_limit)} / {len(records)}')
    print(f'生成時間の合計: {total_time:.1f}秒')
    if USE_RAG:
        rr_list = [reciprocal_rank(r['rank']) for r in answerable]
        recalls = [r['recall'] for r in answerable]
        print(f'検索MRR@{config.GENERATION_K}: {calculate_mrr(rr_list):.3f}')
        print(f'検索 Recall@{config.GENERATION_K}: {sum(recalls) / len(recalls):.3f}')
