import argparse
import json
from datetime import datetime
import time

from transformers import set_seed

from src import config
from src import question_answering
from src.generation import llm
from src.generation.prompt import build_user_prompt, SYSTEM_PROMPT_NO_RAG, SYSTEM_PROMPT_RAG
from evaluation.rag.eval_data import load_eval_set
from evaluation.rag.metrics import reciprocal_rank, calculate_recall_at_k, find_rank, calculate_mrr, calculate_hit_rate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='検索結果をLLMに渡し、回答を評価する')
    parser.add_argument('--collection', default=config.COLLECTION_NAME, type=str, help='使うコレクション名')
    parser.add_argument('--rag', action='store_true', help='付けると検索結果をLLMに渡す')
    parser.add_argument('--method', default=config.RETRIEVAL_METHOD, choices=['vector', 'hybrid-rerank'], help='検索方式')
    parser.add_argument('--generation-k', default=config.GENERATION_K, type=int, help='LLMに渡す件数')
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
        filename = f'generation_rag_{args.method}_{args.generation_k}_{args.collection}_{timestamp}.jsonl'
    else:
        filename = f'generation_norag_{timestamp}.jsonl'
    records = []
    result_path = config.RESULTS_DIR / filename
    with open(result_path, 'w', encoding='utf-8') as f:
        for eval_id, row in eval_set.items():
            query_text = row['question']
            gold_law_ids = sorted({gold['law_id'] for gold in row['gold']})
            if args.rag:
                start = time.perf_counter()
                search_results = question_answering.search(
                    resources, query_text, config.RETRIEVAL_K, args.generation_k, args.method
                )
                search_time = time.perf_counter() - start
                set_seed(42)
                result = {}
                stream = question_answering.generate(
                    resources,
                    query_text,
                    config.GENERATE_PARAMS,
                    search_results,
                    SYSTEM_PROMPT_RAG,
                    False,
                    result,
                )
                text = ''.join(stream)
                latency = time.perf_counter() - start
                if row['gold']:
                    rank = find_rank(row['gold'], search_results, args.generation_k)
                    recall = calculate_recall_at_k(row['gold'], search_results, args.generation_k)
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
                    'text': text,
                    'search_time': round(search_time, 4),
                    'ttft': result['ttft'],
                    'total_time': result['total_time'],
                    'latency': round(latency, 4),
                    'output_token': result['output_token'],
                    'token_limit': result['token_limit'],
                }
            else:
                prompt = build_user_prompt(query_text, None)
                result = {}
                set_seed(42)
                stream = llm.generate_stream(
                    llm_model,
                    tokenizer,
                    SYSTEM_PROMPT_NO_RAG,
                    prompt,
                    config.GENERATE_PARAMS,
                    False,
                    result,
                )
                text = ''.join(stream)
                record = {
                    'id': eval_id,
                    'category': row['category'],
                    'gold_law_ids': gold_law_ids,
                    'text': text,
                    'ttft': result['ttft'],
                    'total_time': result['total_time'],
                    'output_token': result['output_token'],
                    'token_limit': result['token_limit'],
                }
            records.append(record)
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f'{eval_id}完了 ({len(records)} / {len(eval_set)})')
    print('===')
    answerable = [r for r in records if r['gold_law_ids']]
    hit_limit = [r for r in records if r['token_limit']]
    total_sum_time = sum(r['total_time'] for r in records)
    print(f'問題数: {len(records)} 可答問題数: {len(answerable)}')
    print(f'打ち切り: {len(hit_limit)} / {len(records)}')
    print(f'LLMの時間の合計: {total_sum_time:.1f}秒')
    if args.rag:
        article = [r for r in answerable if r['category'] != 'situation']
        situation = [r for r in answerable if r['category'] == 'situation']
        article_hit_list = [r['rank'] is not None for r in article]
        situation_hit_list = [r['rank'] is not None for r in situation]
        article_rr_list = [reciprocal_rank(r['rank']) for r in article]
        situation_rr_list = [reciprocal_rank(r['rank']) for r in situation]
        article_recalls = [r['recall'] for r in article]
        situation_recalls = [r['recall'] for r in situation]
        print(f'条文型：Hit@{args.generation_k}: {calculate_hit_rate(article_hit_list):.3f} ({sum(article_hit_list)} / {len(article_hit_list)})')
        print(f'状況型：Hit@{args.generation_k}: {calculate_hit_rate(situation_hit_list):.3f} ({sum(situation_hit_list)} / {len(situation_hit_list)})')
        print(f'条文型：MRR@{args.generation_k}: {calculate_mrr(article_rr_list):.3f}')
        print(f'状況型：MRR@{args.generation_k}: {calculate_mrr(situation_rr_list):.3f}')
        print(f'条文型：Recall@{args.generation_k}: {sum(article_recalls) / len(article_recalls):.3f}')
        print(f'状況型：Recall@{args.generation_k}: {sum(situation_recalls) / len(situation_recalls):.3f}')
