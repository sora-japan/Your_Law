"""保存済みの検索評価の結果ファイルから、時間と順位の指標を集計する。

evaluate_retrieval.py が出したjsonlを、方式ごとに並べて渡す。

k を引数で受け取るのは、evaluate_retrieval.pyが出すMRRが
max(EVAL_K_LIST)に依存するためである。
EVAL_K_LIST が (1, 3, 5, 10, 20, 30, 50, 100) なら出てくるのはMRR@100で、
6位以降にある正解も 1/順位 として計算されている。
生成に渡すのが5件なら、その正解はプロンプトに入らない。
保存済みの rank を k で切り直すことで、測り直さずに本番の件数での値が出せる。

既定の k は config.GENERATION_K で、本番で渡す件数と揃えている。
--k 100 で走らせると evaluate_retrieval.py が出した MRR と一致するため、
検算に使える。

Hit@k は「1件でも正解を引けた問題の割合」で、Recall@k の2値版。
Recall は部分点があるため、gold 2条の問題で1条だけ引けると 0.5 になるが、
生成には「片方の根拠しかない状態」で渡ることになる。
どちらが生成に効くかは測っていない。

Recall@k は、1問ごとの「引けた正解 ÷ その問題の正解数」を問題数で平均した値で、
evaluate_retrieval.py と同じ定義である。問題を等しく重く扱うため、
gold が2条ある問題で1条だけ引けると、その問題は 0.5 として平均に入る。

MRR と Hit は rank から計算するのでどの k でも動くが、
Recall@k は jsonl に保存された値を読むため、
EVAL_K_LIST に無い k を指定すると KeyError になる。
現在使えるのは 1 / 3 / 5 / 10 / 20 / 30 / 50 / 100 である。

時間は中央値と平均を並べて出す。
ベクトルを使う方式は初回の時間が遅く、平均がそれに引っ張られる。
並べればどちらを判断に使うべきかわかりやすい。

実行コマンドの例:
python3 -m evaluation.compare_retrieval --k 5 \
  evaluation/results/retrieval_ruri-v3-310m_1000_20261013_50055_prefixed_*.jsonl
"""
import argparse
import pathlib
import statistics

from evaluation.rag.eval_data import convert_jsonl
from evaluation.rag.metrics import reciprocal_rank, calculate_mrr, calculate_hit_rate
from src import config


def summarize(rows: list[dict], k: int) -> dict:
    """1グループ分の行から、指標をまとめた辞書を返す。

    見やすくするために、時間はミリ秒に変換してから返す。

    rerank_time はリランキングをした方式にしか入らない。
    1件も無ければ rerank の3つを付けずに返すので、返る辞書は方式によって変わる。

    キーが無いファイルと None が入っているファイルの両方があるため .get()で取る。
    どちらも「リランクしてない」という同じ意味になる。

    rank は gold の中で最も良い順位で、圏外なら None が入っている。
    k より大きい順位は None に置き換えてから渡すので、
    k 件の外にある正解は MRR でも Hit でも 0 になる。
    """
    if not rows:
        raise ValueError('空のグループは集計できません')
    search_times = []
    rerank_times = []
    rr_list = []
    hit_list = []
    recall_list = []
    for row in rows:
        search_times.append(row['search_time'] * 1000)
        rerank_time = row.get('rerank_time')
        if rerank_time is not None:
            rerank_times.append(rerank_time * 1000)
        rank = row['rank']
        recall_list.append(row['recall'][str(k)])
        if rank is not None and rank > k:
            rank = None
        rr_list.append(reciprocal_rank(rank))
        hit_list.append(rank is not None)
    result = {
        'question_num': len(rows),
        'time_median': round(statistics.median(search_times), 1),
        'time_mean': round(statistics.mean(search_times), 1),
        'time_max': round(max(search_times), 1),
        f'mrr@{k}': calculate_mrr(rr_list),
        f'hit@{k}': calculate_hit_rate(hit_list),
        f'recall@{k}': sum(recall_list) / len(recall_list),
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
    parser = argparse.ArgumentParser(description='時間と順位の集計を行う')
    parser.add_argument('path', type=pathlib.Path, nargs='+', help='表にするjsonlファイルのpath')
    parser.add_argument('--k', default=config.GENERATION_K, type=int,  help='生成に渡す件数。この件数での指標を出す')
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
        article_summary = summarize(article_rows, args.k)
        situation_summary = summarize(situation_rows, args.k)
        result.append({'method': method, 'group': '条文型', **article_summary})
        result.append({'method': method, 'group': '状況型', **situation_summary})

    for row in result:
        print(row)
