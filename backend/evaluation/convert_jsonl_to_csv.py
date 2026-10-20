import csv
from datetime import datetime
from zoneinfo import ZoneInfo

from src import config
from evaluation.rag.eval_data import load_eval_set, convert_jsonl, convert_dict

header = ['ID', '種別', '正解', '順位', 'RAGありの判定', 'RAGなしの判定', '質問', 'RAGありの回答', 'RAGなしの回答']

today_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
file_name = "generate_eval" + "_" + today_str + ".csv"

eval_set = load_eval_set(config.EVAL_SET_FILE)
rag_file = convert_dict(convert_jsonl(config.RESULTS_DIR / 'generation_rag_20261020.jsonl'))
no_rag_file = convert_dict(convert_jsonl(config.RESULTS_DIR / 'generation_norag_20261020.jsonl'))

LAW_TITLE = {
    '322AC0000000233': '食品衛生法', 
    '323AC1000000186': '消防法',
    '325AC0000000201': '建築基準法',
    '343AC0000000100': '都市計画法',
    '351AC0000000057': '特定商取引法',
    '409AC0000000123': '介護保険法',
}

with open(config.RESULTS_DIR / file_name, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    for eval_id, row in eval_set.items():
        rag = rag_file[eval_id]
        no_rag = no_rag_file[eval_id]
        parts = []
        for gold in row['gold']:
            law_title = LAW_TITLE[gold['law_id']]
            article_num = gold.get('article_num')
            if article_num:
                parts.append(f'{law_title} 第{article_num}条')
            else:
                parts.append(law_title)
        gold_str = ' / '.join(parts)
        if rag['recall'] is None:
            ranking = '対象外(不可答)'
        elif rag['rank'] is None:
            ranking = '圏外(検索失敗)'
        else:
            ranking = rag['rank']
        writer.writerow({
            'ID': eval_id,
            '種別': row['category'],
            '質問': row['question'],
            '正解': gold_str,
            '順位': ranking,
            'RAGありの回答': rag['text'],
            'RAGなしの回答': no_rag['text'],
            'RAGありの判定': '',
            'RAGなしの判定': '',
        })
