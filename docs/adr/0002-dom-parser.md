---
status: accepted
date: 2026-09-11
---

# ADR-0002: XMLパースに DOM 方式（`xml.etree.ElementTree`）を採用する

## Context and Problem Statement

法令XMLは一括ダウンロード全体で約300MB、10,702ファイルある。
XMLのパース方式には DOM（全体をメモリにツリー展開）、SAX（イベント駆動）、
StAX（ストリーミング）があり、メモリ効率とアクセス方法にそれぞれ特性が異なる。

## Decision Drivers

* 法令の条文構造は編・章・節・条・項・号と階層が深く、深さも法令によって異なる
* 条を取得するには階層を行き来するランダムアクセスが必要
* 300MBは合計であり、1ファイルは数百KB程度に収まる
* 標準ライブラリで完結させ、依存を増やしたくない

## Considered Options

1. DOM 方式（`xml.etree.ElementTree`）
2. DOM 方式（`lxml`）
3. SAX / ストリーミング方式

## Decision Outcome

Chosen option: "DOM 方式（`xml.etree.ElementTree`）", because
1ファイル単位での処理となるためメモリ上の制約がなく、
条・項・号を行き来するランダムアクセスが必要な本用途では DOM が適している。
標準ライブラリで完結するため追加依存も発生しない。

`lxml` は高速だが外部依存となるため、速度が問題になった時点で再検討する。
SAX / ストリーミングはメモリ効率に優れるが、階層を遡る処理に向かず、
状態管理が複雑になるため採用しない。

### Consequences

* Good: 標準ライブラリのみで完結し、環境構築の手間がない
* Good: `find()` / `findall()` / `iter()` によるランダムアクセスが自然に書ける
* Good: 全10,702件のパースに失敗0件で成功しており、実用上の問題が確認されていない
* Bad: 全法令を一度に処理する場合、`lxml` より処理時間がかかる可能性がある
* Bad: XPath のサポートが限定的（`lxml` に比べて使える構文が少ない）
