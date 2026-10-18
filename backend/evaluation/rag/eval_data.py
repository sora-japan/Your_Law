import json
import pathlib

def convert_jsonl(path: pathlib.Path) -> list[dict]:
    """JSONLファイルを読み込んで、Pythonの辞書型のリストを返す"""
    with open(path) as f:
        result = [json.loads(jsonl_line) for jsonl_line in f]
        return result


def convert_dict(convert_list: list[dict]) -> dict:
    """リストを辞書に変換する"""
    result = {}
    for row in convert_list:
        result[row['id']] = row
    return result
