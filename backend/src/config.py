import pathlib

BACKEND_DIR = pathlib.Path(__file__).parent.parent

XML_DIR = BACKEND_DIR / 'data' / 'all_xml'

# チャンク分割
CHUNK_THRESHOLD = 1000
MIN_RATIO = 0.5

# 埋め込み
EMBEDDING_MODEL = 'cl-nagoya/ruri-v3-310m'
BATCH_SIZE = 1000

# ベクトルDB
COLLECTION_NAME = 'my_collection'
DISTANCE_SPACE = 'cosine'

# サブセットの目標チャンク数とシード値
SUBSET_TARGET_CHUNKS = 10000
SUBSET_SEED = 42

# 評価用
EVAL_SET_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'eval_set.jsonl'
EVAL_RESULT_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'eval_result.jsonl'
EVAL_K_LIST = (1, 3, 5, 10)
