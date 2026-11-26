"""2つの構成の生成結果を並べた、人手判定ようのcsvを作る。

1行1回答の100行にすると、条文を引く作業が2倍になるため、
1行に1問、同じ質問への2つの回答を列で並べる。

判定列は空にしておき、判定が終わったら別名で保存する。

順位は rank から作る。 gold を持たない問題は「対象外(不可答)」、
渡した件数の中に gold が入らなかった問題は「圏外(検索失敗)」とする。

読み込む jsonl は判定ごとに書き換える。
"""
import csv

from src import config
from evaluation.rag.eval_data import load_eval_set, convert_jsonl, convert_dict

HEADER = ['ID', '種別', '質問', '正解', '順位V', '回答V', '判定V', '順位H', '回答H', '判定H', 'メモ']

LAW_TITLE = {
    '322AC0000000233': '食品衛生法', 
    '323AC1000000186': '消防法',
    '325AC0000000201': '建築基準法',
    '343AC0000000100': '都市計画法',
    '351AC0000000057': '特定商取引法',
    '409AC0000000123': '介護保険法',
}


def build_gold_str(gold_list: list[dict]) -> str:
    """gold を「法令名 第N条」の形にして並べる。

    状況型は article_num を持たないので、法令名だけになる。
    """
    parts = []
    for gold in gold_list:
        law_title = LAW_TITLE[gold['law_id']]
        article_num = gold.get('article_num')
        if article_num:
            parts.append(f'{law_title} 第{article_num}条')
        else:
            parts.append(law_title)
    gold_str = ' / '.join(parts)
    return gold_str


if __name__ == '__main__':
    file_name = 'generate_compare_vector10_hybrid-rerank5_20261126.csv'
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    vector_file = convert_dict(convert_jsonl(config.RESULTS_DIR / 'generation_rag_vector_10_ruri-v3-310m_500_20261013_64593_prefixed_v2_20261126-174827.jsonl'))
    hybrid_rerank_file = convert_dict(convert_jsonl(config.RESULTS_DIR / 'generation_rag_hybrid-rerank_5_ruri-v3-310m_500_20261013_64593_prefixed_v2_20261126-181738.jsonl'))

    with open(config.RESULTS_DIR / file_name, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for eval_id, row in eval_set.items():
            vector = vector_file[eval_id]
            hybrid_rerank = hybrid_rerank_file[eval_id]
            gold_str = build_gold_str(row['gold'])
            if vector['recall'] is None:
                vector_ranking = '対象外(不可答)'
            elif vector['rank'] is None:
                vector_ranking = '圏外(検索失敗)'
            else:
                vector_ranking = vector['rank']
            if hybrid_rerank['recall'] is None:
                hybrid_rerank_ranking = '対象外(不可答)'
            elif hybrid_rerank['rank'] is None:
                hybrid_rerank_ranking = '圏外(検索失敗)'
            else:
                hybrid_rerank_ranking = hybrid_rerank['rank']
            writer.writerow({
                'ID': eval_id,
                '種別': row['category'],
                '質問': row['question'],
                '正解': gold_str,
                '順位V': vector_ranking,
                '回答V': vector['text'],
                '判定V': '',
                '順位H': hybrid_rerank_ranking,
                '回答H': hybrid_rerank['text'],
                '判定H': '',
                'メモ': '',
            })
