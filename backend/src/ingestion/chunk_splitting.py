import xml.etree.ElementTree as ET
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

from src.ingestion.text_extraction import extract_text, normalization_text
from src.config import MIN_RATIO


def xml_chunking(chunk_threshold: int, element: ET.Element) -> list[dict]:
    """条(Article)1件をチャンクのリストにする

    閾値以内なら条のまま1チャンクにし、超える場合だけ項に降りる。
    降りる時は条見出しを渡し、分割後のチャンクにも見出しが残るようにする。
    """
    result = []
    text = normalization_text(extract_text(element))
    article_num = element.get('Num', '')
    article_heading = get_child_text(element, 'ArticleCaption') + get_child_text(element, 'ArticleTitle')
    if len(text) <= chunk_threshold:
        result.append({'level': 'Article', 'article_num': article_num, 'text': text})
        return result
    for paragraph in element.findall('Paragraph'):
        result.extend(paragraph_chunking(chunk_threshold, paragraph, article_num, article_heading))
    return result


def paragraph_chunking(chunk_threshold: int, paragraph: ET.Element, article_num: str = '', article_heading: str = '') -> list[dict]:
    """項(Paragraph) 1件をチャンクのリストにする。

    閾値以内なら項のまま1チャンク。超えるなら号へ、号でも超えるなら句点分割へ降りる。
    号を持たない項は句点分割に直接かける。
    article_num / article_heading は条の情報で、xml_chunking から呼ばれた時だけ渡る。
    条を持たない法令・附則からは項が直接渡されるため、空文字になる。
    """
    result = []
    chunk = try_chunk(chunk_threshold, 'Paragraph', paragraph, 'paragraph_num')
    if chunk:
        chunk['text'] = article_heading + chunk['text']
        chunk['article_num'] = article_num
        result.append(chunk)
        return result
    paragraph_num = paragraph.get('Num', '')
    items = paragraph.findall('Item')
    if items:
        for item in items:
            chunk = try_chunk(chunk_threshold, 'Item', item, 'item_num')
            if chunk:
                chunk['text'] = article_heading + chunk['text']
                chunk['article_num'] = article_num
                chunk['paragraph_num'] = paragraph_num
                result.append(chunk)
                continue
            text = article_heading + normalization_text(extract_text(item))
            for i, split_text in enumerate(split_by_threshold(chunk_threshold, text)):
                result.append({
                    'level': 'Split',
                    'article_num': article_num,
                    'paragraph_num': paragraph_num,
                    'item_num': item.get('Num', ''),
                    'text': split_text,
                    'split_index': i
                })
    else:
        text = article_heading + normalization_text(extract_text(paragraph))
        for i, split_text in enumerate(split_by_threshold(chunk_threshold, text)):
            result.append({
                'level': 'Split',
                'article_num': article_num,
                'paragraph_num': paragraph_num,
                'text': split_text,
                'split_index': i
            })
    return result


def get_child_text(element: ET.Element, tag: str) -> str:
    """直下の子要素 tag のテキストを正規化して返す。子がなければ空文字を返す。"""
    child = element.find(tag)
    if child is None:
        return ''
    return normalization_text(extract_text(child))


def try_chunk(chunk_threshold: int, level: str, element: ET.Element, num_key: str) -> dict | None:
    """閾値以内ならチャンクを作って返し、超えていればNoneを返す。

    番号を入れるキー名を num_key で受け取る。Num 属性はlevelによって
    項番号・号番号として意味が変わるため、共通の num キーには入れない
    """
    text = normalization_text(extract_text(element))
    if len(text) <= chunk_threshold:
        return {'level': level, num_key: element.get('Num', ''), 'text': text}
    else:
        return None


def split_by_threshold(chunk_threshold: int, text: str, min_ratio: float = MIN_RATIO) -> list[str]:
    """テキストを閾値以内の断片に分割して返す。

    切れ目は閾値の手前から後ろ向きに探し、「。」を優先、見つからなければ「、」を使う。
    探索範囲を閾値の min_ratio より後ろに限ることで、極端に短い断片を作らない。
    どちらも見つからなければ閾値の位置で機械的に切る。
    """
    result = []
    start_index = 0
    length = len(text)
    while start_index < length:
        if length - start_index <= chunk_threshold:
            result.append(text[start_index:])
            break
        long_text = text[start_index: start_index + chunk_threshold]
        targets = ['。', '、']
        chunk_indexs = [long_text.rfind(t, int(chunk_threshold * min_ratio)) for t in targets]
        for chunk_index in chunk_indexs:
            if chunk_index != -1:
                result.append(text[start_index: start_index + chunk_index + 1])
                start_index += chunk_index + 1
                break
        else:
            result.append(text[start_index: start_index + chunk_threshold])
            start_index += chunk_threshold
    return result


def get_chunks_with_meta(path: pathlib.Path, chunk_threshold: int) -> list[dict]:
    """法令XML 1ファイルを読み、メタデータ付きのチャンクのリストを返す。

    本則(MainProvision)と附則(SupplProvision)を別々に処理し、provisionで区別する。
    条を持たない法令・附則では、項を単位として処理する。
    chunk_id は law_revision_id#連番 で版ごとに0から振り直す。
    LawBody を持たないファイルは空リストを返す。
    """
    chunk_result = []
    root = ET.parse(path).getroot()
    body = root.find('LawBody')
    if body is None:
        return chunk_result
    main = body.find('MainProvision')
    law_title_text = get_child_text(body, 'LawTitle')
    law_num_text = root.findtext('LawNum') or ''
    file_name = path.stem
    file_name_list = file_name.split('_')
    today_str = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')
    is_current = file_name_list[1] <= today_str
    is_extract = False
    if main is not None:
        is_extract = (main.get('Extract') == 'true')
    law_meta = {
        'law_id': file_name_list[0],
        'law_revision_id': file_name,
        'amend_law_id': file_name_list[2],
        'law_title': law_title_text,
        'law_num': law_num_text,
        'enforce_date': file_name_list[1],
        'is_current': is_current,
        'is_extract': is_extract,
        'suppl_is_extract': False,
    }
    if main is not None:
        articles = main.findall('.//Article')
        if articles:
            for article in articles:
                for chunk in xml_chunking(chunk_threshold, article):
                    chunk.update(law_meta)
                    chunk['provision'] = '本則'
                    chunk_result.append(chunk)
        else:
            for paragraph in main.findall('Paragraph'):
                for chunk in paragraph_chunking(chunk_threshold, paragraph):
                    chunk.update(law_meta)
                    chunk['provision'] = '本則'
                    chunk_result.append(chunk)
    for suppl in body.findall('SupplProvision'):
        amend_law_num = suppl.get('AmendLawNum', '')
        suppl_is_extract = (suppl.get('Extract') == 'true')
        articles = suppl.findall('.//Article')
        if articles:
            for article in articles:
                for chunk in xml_chunking(chunk_threshold, article):
                    chunk.update(law_meta)
                    chunk['provision'] = '附則'
                    chunk['amend_law_num'] = amend_law_num
                    chunk['suppl_is_extract'] = suppl_is_extract
                    chunk_result.append(chunk)
        else:
            for paragraph in suppl.findall('Paragraph'):
                for chunk in paragraph_chunking(chunk_threshold, paragraph):
                    chunk.update(law_meta)
                    chunk['provision'] = '附則'
                    chunk['amend_law_num'] = amend_law_num
                    chunk['suppl_is_extract'] = suppl_is_extract
                    chunk_result.append(chunk)
    for i, chunk in enumerate(chunk_result):
        chunk['chunk_id'] = f'{file_name}#{i}'
    return chunk_result


def find_current_version_paths(xml_dir: pathlib.Path) -> list[pathlib.Path]:
    """法令IDごとに、施行済みのうち最も新しい施行日のファイルを1つ選ぶ"""
    today = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')
    latest = {}
    for path in xml_dir.rglob('*.xml'):
        parts = path.stem.split('_')
        law_id = parts[0]
        enforce_date = parts[1]
        if enforce_date > today:
            continue
        if law_id not in latest or enforce_date > latest[law_id][0]:
            latest[law_id] = (enforce_date, path)
    current_version_paths = [path for _, path in latest.values()]
    return current_version_paths


def load_current_chunks(xml_dir: pathlib.Path, chunk_threshold: int) -> list[dict]:
    """現行版の全法令をチャンクにして返す"""
    chunks = []
    for path in find_current_version_paths(xml_dir):
        chunks.extend(get_chunks_with_meta(path, chunk_threshold))
    return chunks


if __name__ == '__main__':
    from src.config import XML_DIR, CHUNK_THRESHOLD

    chunks = load_current_chunks(XML_DIR, CHUNK_THRESHOLD)
    print(len(chunks))
    print(len(find_current_version_paths(XML_DIR)))
