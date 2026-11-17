import pathlib
from dataclasses import dataclass
from transformers import PreTrainedModel, PreTrainedTokenizerBase
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer, CrossEncoder

from src import config
from src.embedding import embedding
from src.store import db
from src.retrieval import bm25
from src.retrieval.rrf import rrf
from src.retrieval.rerank import rerank, load_cross_encoder
from src.generation import llm 
from src.generation.prompt import build_user_prompt, build_context, SYSTEM_PROMPT_RAG

RETRIEVAL_K = 100
COLLECTION_NAME = 'ruri-v3-310m_1000_20261013_50055_prefixed'


@dataclass
class Resources:
    collection: Collection
    embedding_model: SentenceTransformer
    bm25_index: bm25.Bm25Index
    cross_encoder_model: CrossEncoder
    tokenizer: PreTrainedTokenizerBase
    llm_model: PreTrainedModel


def load_resources(chroma_dir: pathlib.Path, batch_size: int, *, embedding_model_name: str, cross_encoder_model_name: str, llm_model_name: str, collection_name: str) -> Resources:
    """モデルと索引を読み込んで、Resources にまとめる。

    起動時に1回だけ呼ぶ。BM25索引の構築に時間がかかるので、質問ごとには呼ばない。
    """
    client = db.create_persistent_client(chroma_dir)
    collection = db.get_collection(client, collection_name)
    chunk_ids, documents, metadatas = db.get_all_chunks(collection, batch_size)
    embedding_model = embedding.load_model(embedding_model_name)
    bm25_index = bm25.create_index(chunk_ids, documents, metadatas)
    cross_encoder_model = load_cross_encoder(cross_encoder_model_name)
    tokenizer = llm.load_tokenizer(llm_model_name)
    llm_model = llm.load_model(llm_model_name)
    return Resources(
        collection=collection,
        embedding_model=embedding_model,
        bm25_index=bm25_index,
        cross_encoder_model=cross_encoder_model,
        tokenizer=tokenizer,
        llm_model=llm_model,
    )


def search(resources: Resources, question: str, retrieval_k: int, generation_k: int) -> list[dict]:
    """ベクトル検索とBM25をRRFで統合し、リランクして上位を返す。

    retrieval_k は各検索が取る候補。generation_k は最後に残す件数。
    返す前に generation_k 件で切る。
    """
    vector_result = db.search(resources.collection, resources.embedding_model, question, retrieval_k)
    bm25_result = bm25.search(resources.bm25_index, question, retrieval_k)
    rrf_result = rrf(vector_result, bm25_result)
    retrieved = rerank(resources.cross_encoder_model, question, rrf_result)[:generation_k]
    return retrieved


def generate(resources: Resources, question: str, gen_params: dict, retrieved: list[dict], system_prompt: str, enable_thinking: bool) -> dict:
    """検索結果を文脈にして LLM に渡し、回答を作る。

    retrieved は search の戻り値をそのまま渡す。
    戻り値は text / output_token / token_limit / generation_time を持つ辞書。
    """
    context = build_context(retrieved)
    prompt = build_user_prompt(question, context)
    generated = llm.generate(resources.llm_model, resources.tokenizer, system_prompt, prompt, gen_params, enable_thinking)
    return generated


if __name__ == '__main__':
    resources = load_resources(
        config.CHROMA_DIR,
        config.BATCH_SIZE,
        embedding_model_name=config.EMBEDDING_MODEL,
        cross_encoder_model_name=config.CROSS_ENCODER_MODEL,
        llm_model_name=config.LLM_MODEL,
        collection_name=COLLECTION_NAME,
    )
    question = '訪問販売で契約した場合、申込みの撤回（クーリング・オフ）ができるのは書面を受領した日から何日以内ですか？'
    print('===検索結果===')
    retrieved = search(resources, question, RETRIEVAL_K, config.GENERATION_K)
    for chunk in retrieved:
        print(chunk['law_title'], chunk['article_num'], round(chunk['rerank_score'], 4))
    print('===生成結果===')
    generated = generate(resources, question, config.GENERATE_PARAMS, retrieved, SYSTEM_PROMPT_RAG, False)
    print(generated)
