from collections import Counter
from src import config
from src.ingestion.chunk_splitting import load_current_chunks


def with_law_title_and_suppl(chunk: dict) -> str:
    amend_law_num = chunk.get('amend_law_num', '')
    law_title = chunk['law_title']
    text = chunk['text']
    return f'{law_title} {amend_law_num} {text}'


def check_duplication(counter: Counter) -> dict:
    """文字列ごとの出現回数から、重複の状況をまとめた辞書を返す。

    種類の数は「2回以上出てくる文字列が何通りあるか」
    重複するチャンク数は、その文字列たちが占めるチャンクの合計。
    削除可能数は、種類ごとに1件だけ残した時に消える数。
    """
    kinds = 0
    duplication_chunks = 0
    for text, count in counter.items():
        if count < 2:
            continue
        kinds += 1
        duplication_chunks += count
    total = sum(counter.values())
    unique = len(counter)
    result = {
        '総数': total,
        'ユニーク数': unique,
        '種類の数': kinds,
        '重複するチャンク数': duplication_chunks,
        '削減可能数': total - unique,
    }
    return result


def show_duplicate_sources(chunks: list[dict], counter: Counter) -> None:
    """重複している文字列の上位10件を、出どころのチャンクと並べて表示する。

    件数だけでは、重複しているチャンクが同じ法令から来ているのか、
    別々の法令から来ているのかが分からない。
    別々の法令なら、法令名が一意でないということになる。

    文字列が長いので、本文は先頭だけを出す。
    """
    duplication_list = []
    for text, count in counter.most_common(10):
        if count < 2:
            break
        duplication_list.append(text)
    sources = {}
    for dup in duplication_list:
        sources[dup] = []
    for chunk in chunks:
        key = with_law_title_and_suppl(chunk)
        if key in sources:
            sources[key].append(chunk)
    for text in duplication_list:
        print('===' * 10)
        print(f'{counter[text]}件 {text[:70]}')
        for chunk in sources[text]:
            law_id = chunk['law_id']
            provision = chunk['provision']
            level = chunk['level']
            paragraph_num = chunk.get('paragraph_num', '')
            item_num = chunk.get('item_num', '')
            print(f'law_id = {law_id} {provision} {level} 項 = {paragraph_num} 号 = {item_num}')


if __name__ == '__main__':
    chunks = load_current_chunks(config.XML_DIR, config.CHUNK_THRESHOLD, config.REFERENCE_DATE)
    print(f'閾値 {config.CHUNK_THRESHOLD} / チャンク数 {len(chunks)}')
    embed_text_list = []
    for chunk in chunks:
        # embed_text = chunk['text']
        embed_text = with_law_title_and_suppl(chunk)
        embed_text_list.append(embed_text)
    counter = Counter(embed_text_list)
    result = check_duplication(counter)
    print(result)
    show_duplicate_sources(chunks, counter)
