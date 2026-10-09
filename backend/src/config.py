import pathlib

BACKEND_DIR = pathlib.Path(__file__).parent.parent

# 実験に影響する値
CHUNK_THRESHOLD = 1000
MIN_RATIO = 0.5

EMBEDDING_MODEL = 'cl-nagoya/ruri-v3-310m'
DISTANCE_SPACE = 'cosine'

# 実験に影響しない
XML_DIR = BACKEND_DIR / 'data' / 'all_xml'
COLLECTION_NAME = 'my_collection'
BATCH_SIZE = 1000
