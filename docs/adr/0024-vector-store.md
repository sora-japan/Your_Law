---
status: accepted
date: 2026-09-24
---

# ADR-0024: ベクトルDB に Chroma をローカルで使用し、マネージドサービスを採用しない

## Context and Problem Statement

チャンクのベクトルを保存し、類似度検索を行うためのデータベースを選ぶ必要がある。

候補として pgvector（PostgreSQL 拡張）、Chroma、Qdrant、Milvus、
および Zilliz Cloud や Azure のマネージドサービスを検討した。

調査の結果、選択の指針は以下のように整理されている。

* すでに PostgreSQL を使っている → pgvector
* **QPS が100未満なら pgvector で十分**
* ベクトルとメタデータに ACID トランザクションが必要 → pgvector
* ハイブリッド検索がネイティブに必要 → Qdrant
* 最も豊富なインデックス種別が必要 → Milvus

本プロダクトは個人利用規模であり、QPS は100を大きく下回る。
性能面ではいずれの選択肢でも差が出ない。

## Decision Drivers

* ADR-0023 により、利用フェーズで外部通信を発生させないこと
* 残り期間が短く、DB の移行や学習に時間を割けないこと
* 比較実験のために、埋め込みモデルの差し替えが容易であること

## Considered Options

1. Zilliz Cloud / Azure などのマネージドサービス
2. pgvector（Docker でローカルに PostgreSQL を立てる）
3. Chroma（ローカル）

## Decision Outcome

Chosen option: "Chroma（ローカル）", because
選択肢1は**採用できない**。マネージドサービスはベクトルが外部サーバーに保存される。
Chroma の `CloudClient` も既定で `api.trychroma.com`（AWS us-east-1）に接続する。
ADR-0023 で定めた「利用フェーズで外部通信を発生させない」設計と矛盾し、
ローカルLLM を採用した根拠そのものを崩す。

選択肢2（pgvector）は性能・機能とも十分であり、将来の移行先として有力である。
ただし現時点で移行する理由がない。残り期間で移行に時間を割くより、
評価と比較実験に充てるべきと判断した。

Chroma は `PersistentClient` を用い、保存先ディレクトリは `.gitignore` に登録する。
ベクトルDBの中身は法令XMLと埋め込みモデルから再生成できるため、
バージョン管理の対象としない。

類似度関数の設定は ADR-0021 を参照。

### Consequences

* Good: 外部通信が発生せず、ADR-0023 の設計と整合する
* Good: サーバーの構築が不要で、導入が軽い
* Good: 費用が発生しない
* Bad: ハイブリッド検索（BM25 との組み合わせ）がネイティブにサポートされていない。
  BM25 と統合は自前で実装する（ADR-0025 を参照）
* Bad: メタデータフィルタの表現力が SQL に劣る。
  `category` / `repeal_status` / 施行日 などでの複雑な絞り込みが必要になった場合、
  pgvector への移行を再検討する
* Bad: 距離関数の指定方法がバージョンによって異なる。
  pgvector へ移行する場合は演算子の選択が必要になる
