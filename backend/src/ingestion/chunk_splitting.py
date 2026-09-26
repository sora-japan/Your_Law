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
                skipped += 1
    return result

def try_chunk(CHUNK_THRESHOLD: int, level: str, element: ET.Element) -> dict | None:
    text = normalization_text(extract_text(element))
    if len(text) <= CHUNK_THRESHOLD:
        return {'level': level, 'num': element.get('Num'), 'text': text}
    else:
        return None


if __name__ == '__main__':
    chunk_result = []
    for path in BASE_DIR.rglob('335M50000400013_*.xml'):
        root = ET.parse(path).getroot()
        main = root.find('LawBody').find('MainProvision')
        for article in main.iter('Article'):
            chunk_result.extend(xml_chunking(CHUNK_THRESHOLD, article))
    print(chunk_result)
