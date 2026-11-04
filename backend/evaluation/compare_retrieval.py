"""保存済みの検索評価の結果ファイルから、検索時間を集計する。

evaluate_retrieval.py が出したjsonlを、方式ごとに並べて渡す。

MRRとRecallは、evaluate_retrieval.pyが実行ごとにprintしているので、
本スクリプトでは、検索時間だけを集計している。

中央値と平均を並べて出す。
ベクトルを使う方式は初回の時間が遅く、平均がそれに引っ張られる。
並べればどちらを判断に使うべきかわかりやすい。

実行コマンドの例:
python3 -m evaluation.compare_retrieval \
  evaluation/results/retrieval_ruri-v3-310m_1000_20261013_50055_vector_20261103-1855.jsonl \
  evaluation/results/retrieval_ruri-v3-310m_1000_20261013_50055_bm25_20261103-1855.jsonl \
  evaluation/results/retrieval_ruri-v3-310m_1000_20261013_50055_hybrid_20261103-1856.jsonl
"""
import argparse
import pathlib
import statistics

from evaluation.rag.eval_data import convert_jsonl


def summarize(rows: list[dict]) -> dict:
    """1グループ分の行から、指標をまとめた辞書を返す。

    見やすくするために、時間はミリ秒に変換してから返す。
    """
    if not rows:
        raise ValueError('空のグループは集計できません')
    search_times = []
    for row in rows:
        search_times.append(row['search_time'] * 1000)
    result = {
        'question_num': len(rows),
        'time_median': round(statistics.median(search_times), 1),
        'time_mean': round(statistics.mean(search_times), 1),
        'time_max': round(max(search_times), 1)
    }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='検索時間の集計を行う')
    parser.add_argument('path', type=pathlib.Path, nargs='+', help='表にするjsonlファイルのpath')
    args = parser.parse_args()

    result = []
    for path in args.path:
        rows = convert_jsonl(path)
        method = path.stem.split('_')[-2]
        article_rows = []
        situation_rows = []
        for row in rows:
            if row['category'] == 'situation':
                situation_rows.append(row)
            else:
                article_rows.append(row)
        article_summary = summarize(article_rows)
        situation_summary = summarize(situation_rows)
        result.append({'method': method, 'group': '条文型', **article_summary})
        result.append({'method': method, 'group': '状況型', **situation_summary})

    for row in result:
        print(row)
