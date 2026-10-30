"""保存済みコレクションの健全性を検査する。

構築し直さずに検査だけを回せるようにしてある。
比較実験では構成ごとにコレクションを作るので、名前を渡すだけで同じ検査が使える。

検査するのは設定に依存しない性質だけ。
順位やRecallは閾値やモデルを変えれば変わるので、ここでは見ない。
"""
import math
import itertools
import argparse

from evaluation.rag.eval_data import load_eval_set, collect_must_law_ids
from src.embedding.embedding import load_model
from src.store import db
from src import config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='保存済みコレクションが問題ないかを調査する')
    parser.add_argument('name', help='調査するコレクションの名前')
    args = parser.parse_args()
    eval_set = load_eval_set(config.EVAL_SET_FILE)
    must_law_ids = collect_must_law_ids(eval_set)

    model = load_model(config.EMBEDDING_MODEL)

    client = db.create_persistent_client(config.CHROMA_DIR)
    collection = db.get_collection(client, args.name)

    chunk_id_sets = {}
    nan_eval_ids = []
    for eval_id in eval_set:
        search_result = db.search(collection, model, eval_set[eval_id]['question'], config.GENERATION_K)
        chunk_id_sets[eval_id] = {hit['chunk_id'] for hit in search_result}
        # 検査1 ベクトルが壊れると距離がNaNになり、順位が意味を持たなくなる
        nan_count = 0
        for hit in search_result:
            distance = hit['distance']
            if math.isnan(distance):
                nan_count += 1
        if nan_count > 0:
            nan_eval_ids.append(eval_id)
    if nan_eval_ids:
        print(f'検査1 失敗: distanceがNaNです。クエリか文書のベクトルが壊れています: {nan_eval_ids}')
    else:
        print('検査1 通過: distanceにNaNはありません')
    # 検査2 異なる質問が同じ結果を返すのは、インデックスが壊れている可能性がある
    #       10/29bでts005とts024が完全に同じ10件を返した
    #       順序が違っても、中身が全く同じなら異常なので、集合で比べる
    same_pairs = []
    for id_a, id_b in itertools.combinations(chunk_id_sets, 2):
        if chunk_id_sets[id_a] == chunk_id_sets[id_b]:
            same_pairs.append((id_a, id_b))
    if same_pairs:
        print(f'検査2 失敗: 異なる質問が全く同じ検索結果を返しています: {len(same_pairs)}組')
        for id_a, id_b in same_pairs[:10]:
            print(f'{id_a}と{id_b}')
        if len(same_pairs) > 10:
            print(f'ほか{len(same_pairs) - 10}組')
    else:
        print(f'検査2 通過: {len(chunk_id_sets)}問の検索結果は全て異なります')
    # 検査3 サブセットから必須法令が漏れると、その法令の問題が全部圏外になる
    #       エラーが出ないので Recallが静かに下がってしまう
    missing_law_ids = []
    for law_id in must_law_ids:
        result = collection.get(where={'law_id': law_id}, limit=1)
        if not result['ids']:
            missing_law_ids.append(law_id)
    if missing_law_ids:
        print(f'検査3 失敗: 必須法令のチャンクがありません: {missing_law_ids}')
    else:
        print(f'検査3 通過: 必須法令 {len(must_law_ids)}件全てのチャンクがあります')
