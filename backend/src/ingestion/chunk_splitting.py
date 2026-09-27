import xml.etree.ElementTree as ET
from src.ingestion.text_extraction import extract_text, normalization_text
import pathlib
from collections import Counter

BASE_DIR = pathlib.Path(__file__).parent
XML_FILE = BASE_DIR / 'all_xml'
CHUNK_THRESHOLD = 1000
# LEVELS = ['Article', 'Paragraph', 'Item']

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
        for item in paragraph.findall('Item'):
            chunk = try_chunk(CHUNK_THRESHOLD, 'Item', item)
            if chunk:
                chunk['article_num'] = article_num
                chunk['paragraph_num'] = paragraph_num
                result.append(chunk)
                continue
            else:
                text = normalization_text(extract_text(item))
                start_index = 0
                length = len(text)
                while start_index < length:
                    if length - start_index <= CHUNK_THRESHOLD:
                        result.append({
                            'level': 'Item',
                            'article_num': article_num,
                            'paragraph_num': paragraph_num,
                            'item_num': item.get('Num'),
                            'text': text[start_index:]
                        })
                        break
                    long_text = text[start_index: start_index + CHUNK_THRESHOLD]
                    targets = ['。', '、']
                    chunk_indexs = [long_text.rfind(t) for t in targets]
                    for chunk_index in chunk_indexs:
                        if -1 != chunk_index:
                            result.append({
                                'level': 'Item',
                                'article_num': article_num,
                                'paragraph_num': paragraph_num,
                                'item_num': item.get('Num'),
                                'text': text[start_index: start_index + chunk_index + 1]
                            })
                            start_index += chunk_index + 1
                            break
                    else:
                        result.append({
                            'level': 'Item',
                            'article_num': article_num,
                            'paragraph_num': paragraph_num,
                            'item_num': item.get('Num'),
                            'text': text[start_index: start_index + CHUNK_THRESHOLD]
                        })
                        start_index += CHUNK_THRESHOLD
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
    MIN_RATIO = 0.5
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
    chunk_result = []
    for path in BASE_DIR.rglob('335M50000400013_*.xml'):
        root = ET.parse(path).getroot()
        main = root.find('LawBody').find('MainProvision')
        for article in main.iter('Article'):
            chunk_result.extend(xml_chunking(CHUNK_THRESHOLD, article))
    print(chunk_result)

    print(split_by_threshold(100, "あ。"*305))
    print([len(p) for p in split_by_threshold(100, "あ。"*305)])
