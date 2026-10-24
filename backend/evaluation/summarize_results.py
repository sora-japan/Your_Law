import statistics

from evaluation.rag.eval_data import convert_jsonl, convert_dict
from src import config

def eval_summary(eval_dict: dict) -> dict:
    output_token_list = []
    eval_time_list = []
    eval_limit_list = []
    for record in eval_dict.values():
        output_token_list.append(record['output_token'])
        eval_time_list.append(record['generation_time'])
        eval_limit_list.append(record['token_limit'])
    median_token = statistics.median(output_token_list)
    sum_token = sum(output_token_list)
    max_token = max(output_token_list)
    true_limit = eval_limit_list.count(True)
    sum_generation_time = sum(eval_time_list)
    median_time = statistics.median(eval_time_list)
    tok_s = sum_token / sum_generation_time
    eval_result = {
        '出力トークンの中央値' : median_token,
        '出力トークンの合計': sum_token,
        '出力トークンの最大': max_token,
        'トークン上限まで達した数': f'{true_limit} / {len(eval_dict)}',
        '合計生成時間': sum_generation_time,
        '1問当たりの生成時間(中央値)': median_time,
        'tok/s': round(tok_s, 2),
    }
    return eval_result

if __name__ == '__main__':
    eval_rag_dict = convert_dict(convert_jsonl(config.RESULTS_DIR / 'generation_rag_20261020.jsonl'))
    eval_no_rag_dict = convert_dict(convert_jsonl(config.RESULTS_DIR / 'generation_norag_20261020.jsonl'))
    print('===RAGあり===')
    rag_result = eval_summary(eval_rag_dict)
    for k, v in rag_result.items():
        print(k, v)
    print('===RAGなし===')
    no_rag_result = eval_summary(eval_no_rag_dict)
    for k, v in no_rag_result.items():
        print(k, v)
