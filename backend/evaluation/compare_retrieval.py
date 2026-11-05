"""保存済みの検索評価の結果ファイルから、検索時間とリランク時間を集計する。

evaluate_retrieval.py が出したjsonlを、方式ごとに並べて渡す。

MRRとRecallは、evaluate_retrieval.pyが実行ごとにprintしているので、
本スクリプトでは、時間だけを集計している。

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

    rerank_time はリランキングをした方式にしか入らない。
    1件も無ければ rerank の3つを付けずに返すので、返る辞書は方式によって変わる。

    キーが無いファイルと None が入っているファイルの両方があるため .get()で取る。
    どちらも「リランクしてない」という同じ意味になる。
    """
    if not rows:
        raise ValueError('空のグループは集計できません')
    search_times = []
    rerank_times = []
    for row in rows:
        search_times.append(row['search_time'] * 1000)
        rerank_time = row.get('rerank_time')
        if rerank_time is None:
            continue
        rerank_times.append(rerank_time * 1000)
    result = {
        'question_num': len(rows),
        'time_median': round(statistics.median(search_times), 1),
        'time_mean': round(statistics.mean(search_times), 1),
        'time_max': round(max(search_times), 1)
    }
    if not rerank_times:
        return result
    rerank_times_dict = {
        'rerank_median': round(statistics.median(rerank_times), 1),
        'rerank_mean': round(statistics.mean(rerank_times), 1),
        'rerank_max': round(max(rerank_times), 1)
    }
    result.update(rerank_times_dict)
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
