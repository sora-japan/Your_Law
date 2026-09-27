import xml.etree.ElementTree as ET
from src.ingestion.text_extraction import extract_text, normalization_text
import pathlib
from collections import Counter

BACKEND_DIR = pathlib.Path(__file__).parent.parent.parent
XML_DIR = BACKEND_DIR / 'data' / 'all_xml'
CHUNK_THRESHOLD = 1000
MIN_RATIO = 0.5

def xml_chunking(CHUNK_THRESHOLD: int, element: ET.Element) -> list[dict]:
    result = []
    text = normalization_text(extract_text(element))
    article_num = element.get('Num')
    if len(text) <= CHUNK_THRESHOLD:
        result.append({'level': 'Article', 'article_num': article_num, 'text': text})
        return result
    for paragraph in element.findall('Paragraph'):
        chunk = try_chunk(CHUNK_THRESHOLD, 'Paragraph', paragraph)
        if chunk:
            chunk['article_num'] = article_num
            result.append(chunk)
            continue
        paragraph_num = paragraph.get('Num')
        items = paragraph.findall('Item')
        if items:
            for item in items:
                chunk = try_chunk(CHUNK_THRESHOLD, 'Item', item)
                if chunk:
                    chunk['article_num'] = article_num
                    chunk['paragraph_num'] = paragraph_num
                    result.append(chunk)
                    continue
                text = normalization_text(extract_text(item))
                for i, split_text in enumerate(split_by_threshold(CHUNK_THRESHOLD, text)):
                    result.append({
                        'level': 'Split',
                        'article_num': article_num,
                        'paragraph_num': paragraph_num,
                        'item_num': item.get('Num'),
                        'text': split_text,
                        'split_index': i
                    })
        else:
            text = normalization_text(extract_text(paragraph))
            for i, split_text in enumerate(split_by_threshold(CHUNK_THRESHOLD, text)):
                result.append({
                    'level': 'Split',
                    'article_num': article_num,
                    'paragraph_num': paragraph_num,
                    'text': split_text,
                    'split_index': i
                })
    return result


def try_chunk(CHUNK_THRESHOLD: int, level: str, element: ET.Element) -> dict | None:
    text = normalization_text(extract_text(element))
    if len(text) <= CHUNK_THRESHOLD:
        return {'level': level, 'num': element.get('Num'), 'text': text}
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


if __name__ == '__main__':
    from collections import Counter
    import difflib

    # for threshold in [200, 500, 1000, 2000]:
    chunk_result = []
    for path in XML_DIR.rglob('335M50000400013_*.xml'):
        root = ET.parse(path).getroot()
        main = root.find('LawBody').find('MainProvision')
        for article in main.iter('Article'):
            if article.get('Num') != '22':
                continue
            # chunk_result.extend(xml_chunking(threshold, article))
            original = normalization_text(extract_text(article))
            chunks = xml_chunking(1000, article)
            joined = ''.join(c['text'] for c in chunks)
            # if len(original) != len(joined):
            #     print(article.get('Num'), len(original), len(joined))
            sm = difflib.SequenceMatcher(None, original, joined)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != 'equal':
                    print(tag, repr(original[i1:i2]), '→', repr(joined[j1:j2]))

    # print(Counter(c['level'] for c in chunk_result))
    # total_chars = sum(len(c['text']) for c in chunk_result)
    # print(total_chars)

    # for c in chunk_result:
    #     if c['article_num'] == '22' and c.get('paragraph_num') == '1':
    #         print(c['level'], c.get('split_index'), c['text'][:50])
