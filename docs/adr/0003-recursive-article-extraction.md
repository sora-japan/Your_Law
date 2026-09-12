---
status: accepted
date: 2026-09-11
---

# ADR-0003: 条（`Article`）の取得を階層に対して再帰的に行う

## Context and Problem Statement

チャンクの基本単位を条とする方針のもと、`MainProvision` から条を取得する必要がある。
当初は「`MainProvision` の直下に `Article` が並ぶ」と想定していたが、
全10,702件を対象に `MainProvision` の直接の子要素を数えたところ、
実際には5種類のタグが存在した。

| タグ | 件数 |
|---|---|
| Article | 91,179 |
| Chapter | 23,249 |
| Paragraph | 1,819 |
| Part | 744 |
| Section | 6 |

編・章・節という区分階層が間に挟まる法令が存在し、
さらに下の階層には `Subsection`（12,804件）、`Division`（3,213件）も存在する。
階層の深さは法令によって異なる。

## Decision Drivers

* 条を1件も取りこぼさないこと
* 階層の深さが法令によって異なり、決め打ちできないこと
* 附則（`SupplProvision`）の条を混入させないこと

## Considered Options

1. `MainProvision` の直下のみを走査する
2. `root.iter('Article')` で全範囲から条を取得する
3. `MainProvision` を起点に、階層を再帰的に降りて条を取得する

## Decision Outcome

Chosen option: "`MainProvision` を起点に、階層を再帰的に降りて条を取得する", because
選択肢1では `Chapter` 配下の条（23,249件の章に含まれる条）をすべて取りこぼす。
選択肢2は附則側の条まで拾ってしまい、本則と附則の分離（ADR-0004）に反する。
起点を `MainProvision` に限定したうえで深さを問わず探索する方式が、
取りこぼしと混入の両方を避けられる唯一の方法である。

実装上は `MainProvision.findall('.//Article')` または再帰関数のいずれでもよい。

### Consequences

* Good: 階層構造を持つ法令でも条を取りこぼさない
* Good: 附則の条が混入しない
* Good: 将来スキーマに新たな区分階層が追加されても、探索の実装を変えずに済む
* Bad: 章・節などの所属情報が、探索結果からは直接得られない
  → 条のメタデータとして別途保持する必要がある（章名を保持する方針）
* Bad: `TableColumn` の子要素にも `Article` が定義されているため、
  表の中の条を拾う可能性がある。**未確認の課題として残る**
