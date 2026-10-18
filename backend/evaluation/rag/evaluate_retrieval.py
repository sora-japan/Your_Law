from evaluation.rag.eval_data import convert_jsonl, convert_dict
from src import config


if __name__ == '__main__':
    eval_set = convert_dict(convert_jsonl(config.EVAL_SET_FILE))
    print(f'評価データ: {len(eval_set)}')
