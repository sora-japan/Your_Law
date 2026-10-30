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
DISTANCE_SPACE = 'cosine'
# クロマDBの保存先パス
CHROMA_DIR = BACKEND_DIR / 'chroma'

# サブセットの目標チャンク数とシード値
SUBSET_TARGET_CHUNKS = 50000
SUBSET_SEED = 42

# 評価用
RESULTS_DIR = BACKEND_DIR / 'evaluation' / 'results'
EVAL_SET_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'eval_set.jsonl'
EVAL_RESULT_FILE = RESULTS_DIR / 'eval_result.jsonl'
EVAL_K_LIST = (1, 3, 5, 10)


# どの時点で施行済みの版を「現行版」とするかの基準日。
# 比較実験の間コーパスを固定するために定数にしています(ADR-0040)。
# 本番では今日の日付を渡す。
REFERENCE_DATE = '20261013'

# LLM
LLM_MODEL = "Qwen/Qwen3-8B"

# LLMのプロンプトに入れるチャンク数
# 評価用のEVAL_K_LISTとは別物で、こちらは本番の構成の一部
# 増やすとRecallは上がるが、無関係な条文も増えて生成が悪化する可能性がある。
GENERATION_K = 10
