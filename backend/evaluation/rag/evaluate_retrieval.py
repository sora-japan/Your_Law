import json
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).parent.parent.parent
# JSONL_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'eval_set.jsonl'
PRE_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'dummy.jsonl'

# JSONファイルを読み込んで、Pythonの辞書型のリストを返す
def convert_jsonl(path: str) -> list[dict]:
    with open(path) as f:
        result = [json.loads(jsonl_line) for jsonl_line in f]
        return result

# リストを辞書へ
def convert_dict(eval_set: list[dict]) -> dict:
    result = {}
    for row in eval_set:
        result[row['id']] = row
    return result

if __name__ == '__main__':
    eval_set = convert_jsonl(PRE_FILE)
    result = convert_dict(eval_set)
    print(result)
