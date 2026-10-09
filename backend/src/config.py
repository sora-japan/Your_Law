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
