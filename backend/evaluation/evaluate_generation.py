import argparse
import json
from datetime import datetime

from transformers import set_seed

from src import config
from src import question_answering
from src.generation import llm
from src.generation.prompt import build_user_prompt, build_context, SYSTEM_PROMPT_NO_RAG, SYSTEM_PROMPT_RAG
from evaluation.rag.eval_data import load_eval_set
from evaluation.rag.metrics import reciprocal_rank, calculate_recall_at_k, find_rank, calculate_mrr


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='検索結果をLLMに渡し、回答を評価する')
    parser.add_argument('--collection', default=config.COLLECTION_NAME, type=str, help='使うコレクション名')
    parser.add_argument('--rag', action='store_true', help='付けると検索結果をLLMに渡す')
    args = parser.parse_args()

    eval_set = load_eval_set(config.EVAL_SET_FILE)

    if args.rag:
        resources = question_answering.load_resources(
            config.CHROMA_DIR,
            config.BATCH_SIZE,
            embedding_model_name=config.EMBEDDING_MODEL,
            cross_encoder_model_name=config.CROSS_ENCODER_MODEL,
            llm_model_name=config.LLM_MODEL,
            collection_name=args.collection,
        )
        tokenizer = resources.tokenizer
        llm_model = resources.llm_model
        print(f'コレクション: {args.collection} / {resources.collection.count()}件')
    else:
        tokenizer = llm.load_tokenizer(config.LLM_MODEL)
        llm_model = llm.load_model(config.LLM_MODEL)

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    if args.rag:
        filename = f'generation_rag_{args.collection}_{timestamp}.jsonl'
    else:
        filename = f'generation_norag_{timestamp}.jsonl'
    records = []
    result_path = config.RESULTS_DIR / filename
    with open(result_path, 'w', encoding='utf-8') as f:
        for eval_id, row in eval_set.items():
            query_text = row['question']
            gold_law_ids = sorted({gold['law_id'] for gold in row['gold']})
            if args.rag:
                search_results = question_answering.search(
                    resources, query_text, config.RETRIEVAL_K, config.GENERATION_K
                )
                context = build_context(search_results)
                prompt = build_user_prompt(query_text, context)
                set_seed(42)
                generated = llm.generate(llm_model, tokenizer, SYSTEM_PROMPT_RAG, prompt, config.GENERATE_PARAMS, False)
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
                generated = llm.generate(llm_model, tokenizer, SYSTEM_PROMPT_NO_RAG, prompt, config.GENERATE_PARAMS, False)
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
    if args.rag:
        rr_list = [reciprocal_rank(r['rank']) for r in answerable]
        recalls = [r['recall'] for r in answerable]
        print(f'検索MRR@{config.GENERATION_K}: {calculate_mrr(rr_list):.3f}')
        print(f'検索 Recall@{config.GENERATION_K}: {sum(recalls) / len(recalls):.3f}')
