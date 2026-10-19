import json

from src import config
from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from src.ingestion.sub_set import create_sub_chunks
from src.ingestion.chunk_splitting import load_current_chunks
from src.generation import llm
from src.generation.prompt import build_user_prompt, build_context, SYSTEM_PROMPT_NO_RAG, SYSTEM_PROMPT_RAG
from src.embedding import embedding
from src.store import db


if __name__ == '__main__':
    eval_set = load_eval_set(config.EVAL_SET_FILE)
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
    # gen_paramsは一旦仮置き(Qwen3-8Bの思考なしの推奨値
    gen_params = {
        'max_new_tokens': 512,
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.8,
        'top_k': 20,
    }
    result = []
    with open(config.RESULTS_DIR / 'generation_rag_20261020.jsonl', 'w', encoding='utf-8') as f:
        for eval_id, row in eval_set.items():
            query_text = row['question']
            search_results = db.search(collection, embed_model, query_text, 3)
            search_context = build_context(search_results)
            prompt = build_user_prompt(query_text, search_context)
            llm_generate = llm.generate(llm_model, tokenizer, SYSTEM_PROMPT_RAG, prompt, gen_params, False)
            result.append(llm_generate)
            # EVAL_RESULT_FILEは、RAGの保管場所になっている。これを、resultsの中にしたほうがいい気がする。
            # そもそもconfigの中身を変えるのはあり
            f.write(json.dumps(llm_generate, ensure_ascii=False) + '\n')
            break
    print(result)
