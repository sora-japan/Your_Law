import json
import pathlib

BACKEND_DIR = pathlib.Path(__file__).parent.parent.parent
JSONL_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'eval_set.jsonl'
PRE_FILE = BACKEND_DIR / 'evaluation' / 'rag' / 'dummy.jsonl'

# JSONファイルを読み込んで、Pythonの辞書型のリストを返す
def convert_jsonl(path: str) -> list[dict]:
    with open(path) as f:
        result = [json.loads(jsonl_line) for jsonl_line in f]
        return result

# リストを辞書へ
def convert_dict(convert_list: list[dict]) -> dict:
    result = {}
    for row in convert_list:
        result[row['id']] = row
    return result


def judgement(eval_set: dict, ans: dict) -> bool:
    for gold in eval_set['gold']:
        if gold in ans['retrieved_doc_ids']:
            return True
    return False


if __name__ == '__main__':
    eval_set = convert_dict(convert_jsonl(JSONL_FILE))
    dummy_set = convert_dict(convert_jsonl(PRE_FILE))
    eval_total = 0
    correct_answer = 0
    incorrect_ld = []
    for eval_id, eval_data in eval_set.items():
        ans_data = dummy_set.get(eval_id)
        if ans_data is None:
            continue
        judge_result = judgement(eval_data, ans_data)
        eval_total += 1
        if judge_result:
            correct_answer += 1
        else:
            incorrect_ld.append(ans_data)
    print(f"不正解: {incorrect_ld}")
    print(f"{eval_total}件中 {correct_answer}件正解")
    hit_rate = correct_answer / eval_total * 100
    print(f"ヒットレート: {hit_rate:.2f}")
