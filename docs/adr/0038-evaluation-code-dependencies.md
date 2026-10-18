---
status: accepted
date: 2026-10-19
---

# ADR-0038: 評価コードの依存関係を一方向にする

## Context and Problem Statement

`evaluation/rag/evaluate_retrieval.py` が `__main__` を持つ実行スクリプト
でありながら、他のモジュールから道具として import されていた。

```python
# scripts/verify_sub_chunks.py
# scripts/count_gold.py
from evaluation.rag.evaluate_retrieval import convert_jsonl, convert_dict, JSONL_FILE
```

**スクリプトがスクリプトを借りる形**になっていた。1つのファイルが
「実行するもの」と「道具箱」の2役を兼ねている状態である。

### 製品コードが評価コードを import していた

より深刻な違反が見つかった。

```python
# src/ingestion/sub_set.py の5行目
from evaluation.rag.evaluate_retrieval import convert_jsonl, convert_dict, JSONL_FILE
```

```
src/ingestion/sub_set.py  ──→  evaluation/rag/evaluate_retrieval.py
（製品コード）                  （評価コード）
```

**矢印が逆を向いている。** 評価コードを削除すると製品コードが動かなくなる。

### 改名が検出器として働いた

この import は**使われていなかった。** `create_sub_chunks` を
`must_law_ids` を引数で受け取る形に直した時点で不要になっていたが、
`JSONL_FILE` が存在していたため import は成功し、そのまま通っていた。

`JSONL_FILE` を `EVAL_SET_FILE` に改名したことで初めて `ImportError` に
なり、発覚した。

```
ImportError: cannot import name 'JSONL_FILE' from 'evaluation.rag.evaluate_retrieval'
```

**使われていない import は、名前が変わるか消えるまで見つからない。**
今回は偶然、改名が検出器になった。

## Decision Drivers

* import された時点で `__main__` の外にある処理が走る。スクリプトを
  道具として借りると、意図しない実行が起きうる
* 製品コードが評価コードに依存すると、評価を消せなくなる
* 評価データの検証（ADR-0034）を**呼び忘れる経路を作らない**ために、
  読み込みを1箇所に集めたい

## Considered Options

1. 現状維持（スクリプトから import する）
2. 読み込みを `eval_data.py` に切り出し、層を3つに分ける
3. 検証だけを `scripts/` に置く

## Decision Outcome

Chosen option: **「読み込みを `eval_data.py` に切り出し、層を3つに分ける」**

```
実行する側（スクリプト）
    evaluate_retrieval.py  verify_sub_chunks.py  count_gold.py  build_index.py
                              │
                              ↓
道具（ライブラリ）
    eval_data.py  metrics.py  db.py  sub_set.py  chunk_splitting.py
                              │
                              ↓
設定
    config.py
```

規則は1つ。**上から下へのみ呼ぶ。同じ層の中では呼ばない。**

変更前との違いは、`evaluate_retrieval.py` が**上の層と中の層に同時に
居た**ことである。層に1つの箱が2回現れるのが複雑さの正体で、それを
解消した。ファイル数は1つ増えるが、「スクリプト→スクリプト」という
矢印の種類が消える。

選択肢3を却下したのは、`scripts/` に置くと「実行するのを忘れる」経路が
できるためである。検証を読み込みの経路の中に置かないと、ADR-0034 の
「データが壊れていたら停止する」を仕組みで保証できない。

### パス定数は `config.py` に置いた

当初は `eval_data.py` に置いて `config.BACKEND_DIR` を借りる案だったが、
`config.py` が既に `XML_DIR` というデータのパスを持っているため、
評価データのパスだけ別の場所にあるのは一貫しない。

副作用として **`eval_data.py` は標準ライブラリ以外に依存しなくなった。**
`json` と `pathlib` だけを import する。矢印が1本減る。

あわせて `JSONL_FILE` を `EVAL_SET_FILE` に改名した。「どの JSONL か」が
名前から分からなかったため。呼び出し箇所をすべて触るタイミングだった。

### 読み込みの入口を1つにした

```python
def load_eval_set(path: pathlib.Path) -> dict:
    """評価データを読み込んで検証し、idをキーにした辞書を返す"""
```

`convert_jsonl` → `convert_dict` → 検証 の3工程をまとめ、**検証を通らないと
データが手に入らない形**にした。`load_current_chunks` が「ファイル探索 →
パース → チャンク化」をまとめた入口になっているのと同じ形（ADR-0022）。

`convert_jsonl` と `convert_dict` は部品として残るが、通常の経路は
`load_eval_set` だけになる。

## 未使用のコードが4件見つかった

このリファクタリングの過程で、使われていない import と変数が4件見つかった。

| 場所 | 対象 | 見つかった経緯 |
|---|---|---|
| `sub_set.py` | `evaluate_retrieval` からの import | **改名で `ImportError`** |
| `sub_set.py` | `load_current_chunks` の import | **`grep` で発見** |
| `sub_set.py` | `from src import config` | **コードを読んで発見** |
| `eval_data.py` | `seen_ids` 変数（`Counter` に切り替えた残骸） | **コードを読んで発見** |

**3件が同じファイル（`sub_set.py`）に溜まっていた。** いずれも
`create_sub_chunks` を引数で受け取る形に直した時点で不要になったもので、
壊れないため残り続けていた。

発見の経緯が3通りに分かれているのが要点である。偶然壊れたもの、検索して
見つけたもの、目で読んで気づいたもの。**体系的に探す手段がなかった。**

### 静的解析を導入する

手で4件探したものは、`ruff` が1コマンドで全部出す。

```
ruff check .
```

* `F401` 未使用の import → 3件
* `F841` 未使用のローカル変数 → 1件

導入は `pip install ruff` と `ruff check .` だけで、設定ファイルも要らない。
**1人開発でも入れている方が少ない部分であり、入れた理由として実例4件を
提示できる。**

## Consequences

* Good: 依存の矢印が一方向になった。製品コードが評価コードを参照する
  状態が解消された
* Good: 評価データの読み込みが1箇所に集まり、検証を飛ばす経路が消えた
  （ADR-0034 の実装を仕組みで保証）
* Good: `eval_data.py` が標準ライブラリ以外に依存しない
* Good: 層の規則が1つ（上から下へのみ）で言えるようになった。
  ADR-0024 でクリーンアーキテクチャのフル適用を却下したため、
  層はこの3つで十分
* Good: 改名が未使用 import の検出器になった実例が残った。**使われて
  いないものは壊れるまで見つからない**という性質を、具体例で語れる
* Bad: `build_index.py` がリポジトリ直下にあり、`scripts/` に入っていない。
  実行する側の層に属するが、置き場所が他と揃っていない。整理は未着手
* Bad: `config.py` が `src/` の下にある。XML のパスやチャンク閾値は
  プロジェクト全体の設定であり `src` の持ち物ではないが、移すと全ての
  import が変わるため据え置いた
* Bad: import の書き方が `from src import config` と
  `from src.config import XML_DIR, ...` の2通り混在している。前者に
  寄せる方針だが未実施。後者は使わなくなった名前が import 行に残り続け、
  本ADRで見つけた問題を増やす形になる
* Bad: `scripts/must_chunk_num.py` が、`verify_sub_chunks.py` に追加した
  gold 法令の測定と重複している可能性がある。未確認
