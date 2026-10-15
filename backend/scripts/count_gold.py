from evaluation.rag.evaluate_retrieval import convert_jsonl, convert_dict, JSONL_FILE 
from collections import Counter

eval_set = convert_dict(convert_jsonl(JSONL_FILE))
gold_value_dict = {}
gold_value_list_count = []
gold_counter = Counter()
for set_v in eval_set.values():
    gold_value_list_count.append(len(set_v['gold']))
    gold_counter[len(set_v['gold'])] += 1
    print(set_v['category'], len(set_v['gold']))
    if len(gold_value_dict) < len(set_v['gold']):
        gold_value_dict = set_v['gold']
print(len(gold_value_dict))
print(max(gold_value_list_count))
print(gold_value_list_count)
print('goldの要素数の分布: ', gold_counter)
