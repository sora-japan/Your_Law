import xml.etree.ElementTree as ET
from src.ingestion.text_extraction import extract_text, normalization_text
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

BACKEND_DIR = pathlib.Path(__file__).parent.parent.parent
XML_DIR = BACKEND_DIR / 'data' / 'all_xml'
CHUNK_THRESHOLD = 1000
MIN_RATIO = 0.5


def xml_chunking(CHUNK_THRESHOLD: int, element: ET.Element) -> list[dict]:
    result = []
    text = normalization_text(extract_text(element))
    article_num = element.get('Num', '')
    article_heading = get_child_text(element, 'ArticleCaption') + get_child_text(element, 'ArticleTitle')
    if len(text) <= CHUNK_THRESHOLD:
        result.append({'level': 'Article', 'article_num': article_num, 'text': text})
        return result
    for paragraph in element.findall('Paragraph'):
        result.extend(paragraph_chunking(CHUNK_THRESHOLD, paragraph, article_num, article_heading))
    return result


def paragraph_chunking(CHUNK_THRESHOLD: int, paragraph: ET.Element, article_num: str = '', article_heading: str = '') -> list[dict]:
    result = []
    chunk = try_chunk(CHUNK_THRESHOLD, 'Paragraph', paragraph)
    if chunk:
        chunk['text'] = article_heading + chunk['text']
        chunk['article_num'] = article_num
        result.append(chunk)
        return result
    paragraph_num = paragraph.get('Num', '')
    items = paragraph.findall('Item')
    if items:
        for item in items:
            chunk = try_chunk(CHUNK_THRESHOLD, 'Item', item)
            if chunk:
                chunk['text'] = article_heading + chunk['text']
                chunk['article_num'] = article_num
                chunk['paragraph_num'] = paragraph_num
                result.append(chunk)
                continue
            text = article_heading + normalization_text(extract_text(item))
            for i, split_text in enumerate(split_by_threshold(CHUNK_THRESHOLD, text)):
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
        for i, split_text in enumerate(split_by_threshold(CHUNK_THRESHOLD, text)):
            result.append({
                'level': 'Split',
                'article_num': article_num,
                'paragraph_num': paragraph_num,
                'text': split_text,
                'split_index': i
            })
    return result


def get_child_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    if child is None:
        return ''
    return normalization_text(extract_text(child))


def try_chunk(CHUNK_THRESHOLD: int, level: str, element: ET.Element) -> dict | None:
    text = normalization_text(extract_text(element))
    if len(text) <= CHUNK_THRESHOLD:
        return {'level': level, 'num': element.get('Num', ''), 'text': text}
    else:
        return None


def split_by_threshold(CHUNK_THRESHOLD: int, text: str) -> list[str]:
    result = []
    start_index = 0
    length = len(text)
    while start_index < length:
        if length - start_index <= CHUNK_THRESHOLD:
            result.append(text[start_index:])
            break
        long_text = text[start_index: start_index + CHUNK_THRESHOLD]
        targets = ['。', '、']
        chunk_indexs = [long_text.rfind(t, int(CHUNK_THRESHOLD * MIN_RATIO)) for t in targets]
        for chunk_index in chunk_indexs:
            if -1 != chunk_index:
                result.append(text[start_index: start_index + chunk_index + 1])
                start_index += chunk_index + 1
                break
        else:
            result.append(text[start_index: start_index + CHUNK_THRESHOLD])
            start_index += CHUNK_THRESHOLD
    return result


def get_chunks_with_meta(path: pathlib.Path, CHUNK_THRESHOLD: int) -> list[dict]:
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
        'is_extract': is_extract
    }
    if main is not None:
        articles = main.findall('.//Article')
        if articles:
            for article in articles:
                for chunk in xml_chunking(CHUNK_THRESHOLD, article):
                    chunk.update(law_meta)
                    chunk['provision'] = '本則'
                    chunk_result.append(chunk)
        else:
            for paragraph in main.findall('Paragraph'):
                for chunk in paragraph_chunking(CHUNK_THRESHOLD, paragraph):
                    chunk.update(law_meta)
                    chunk['provision'] = '本則'
                    chunk_result.append(chunk)
    for suppl in body.findall('SupplProvision'):
        amend_law_num = suppl.get('AmendLawNum', '')
        suppl_is_extract = (suppl.get('Extract') == 'true')
        articles = suppl.findall('.//Article')
        if articles:
            for article in articles:
                for chunk in xml_chunking(CHUNK_THRESHOLD, article):
                    chunk.update(law_meta)
                    chunk['provision'] = '附則'
                    chunk['amend_law_num'] = amend_law_num
                    chunk['suppl_is_extract'] = suppl_is_extract
                    chunk_result.append(chunk)
        else:
            for paragraph in suppl.findall('Paragraph'):
                for chunk in paragraph_chunking(CHUNK_THRESHOLD, paragraph):
                    chunk.update(law_meta)
                    chunk['provision'] = '附則'
                    chunk['amend_law_num'] = amend_law_num
                    chunk['suppl_is_extract'] = suppl_is_extract
                    chunk_result.append(chunk)
    return chunk_result


if __name__ == '__main__':
    from collections import Counter
    import time
    from datetime import datetime
    from zoneinfo import ZoneInfo

    all_chunks = []
    today = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')
    start = time.perf_counter()
    current_paths = {}
    for path in XML_DIR.rglob('*.xml'):
        parts = path.stem.split('_')
        if parts[1] > today:
            continue
        if parts[0] not in current_paths or parts[1] > current_paths[parts[0]][0]:
            current_paths[parts[0]] = (parts[1], path)
    for law_id, (enforce_date, path) in current_paths.items():
        all_chunks.extend(get_chunks_with_meta(path, CHUNK_THRESHOLD))
    end = time.perf_counter()
    level_counter = Counter()
    provision_counter = Counter()
    for c in all_chunks:
        level_counter[c.get('level')] += 1
        provision_counter[c.get('provision')] += 1
    print(level_counter)
    print(provision_counter)
    print('処理時間を計測: ', '{:.2f}'.format((end-start)))
