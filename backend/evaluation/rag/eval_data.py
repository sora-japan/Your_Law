import json
import pathlib
from collections import Counter

ALLOWED_GOLD_SHAPES = (
    set({'law_id'}),
    set({'law_id', 'provision', 'article_num'})
)


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


def load_eval_set(path: pathlib.Path) -> dict:
    """評価データを読み込んで検証し、idをキーにした辞書を返す"""
    validation_list = convert_jsonl(path)
    # 検証
    errors = []
    ids = [row['id'] for row in validation_list]
    counts = Counter(ids)
    for eval_id, n in counts.items():
        if n > 1:
            errors.append(f'idが重複しています: {eval_id} ({n}件)')
    rows = convert_dict(validation_list)
    for k, v in rows.items():
        if (v['answerable'] and len(v['gold']) == 0) or (not v['answerable'] and len(v['gold']) > 0):
            errors.append(f'answerableとgoldを確認してください: {k}')
        for gold in v['gold']:
            if set(gold) not in ALLOWED_GOLD_SHAPES:
                errors.append(f'goldの形が合っていません: {k} {gold}')
    if errors:
        errors_message = '\n'.join(errors)
        raise ValueError(errors_message)
    return rows


def collect_must_law_ids(eval_set: dict) -> set[str]:
    """評価データのgoldに含まれる法令IDを集める"""
    must_law_ids = set()
    for row in eval_set.values():
        for gold in row['gold']:
            must_law_ids.add(gold['law_id'])
    return must_law_ids


if __name__ == '__main__':
    from src import config

    eval_set = load_eval_set(config.EVAL_SET_FILE)
    print(f'正常: {len(eval_set)}')

    broken_path = config.BACKEND_DIR / 'evaluation' / 'rag' / 'broken_eval_set.jsonl'
    try:
        load_eval_set(broken_path)
    except ValueError as e:
        print(e)
    else:
        raise AssertionError('壊れたデータが検証を通ってしまいました')
