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
    article_heading = get_child_text(element, 'ArticleCaption') + get_child_text(element, 'ArticleTitle')
    if len(text) <= CHUNK_THRESHOLD:
        result.append({'level': 'Article', 'article_num': article_num, 'text': text})
        return result
    for paragraph in element.findall('Paragraph'):
        chunk = try_chunk(CHUNK_THRESHOLD, 'Paragraph', paragraph)
        if chunk:
            chunk['text'] = article_heading + chunk['text']
            chunk['article_num'] = article_num
            result.append(chunk)
            continue
        paragraph_num = paragraph.get('Num')
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
                        'item_num': item.get('Num'),
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
    return normalization_text(extract_text(element))


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


law_meta = {
    'law_id': ...,
    'law_revision_id': ...,
    'law_title': ...,
    'law_num': ...,
    'enforce_date': ...,
}
file_name_list = []
chunk_result = []
for path in XML_DIR.rglob('335M50000400013_*.xml'):
    root = ET.parse(path).getroot()
    law_title_text = root.findtext('LawBody/LawTitle') or ''
    law_num_text = root.findtext('LawNum') or ''
    main = root.find('LawBody').find('MainProvision')
    file_name = path.stem
    file_name_list = file_name.split('_')
    law_meta.update(
        law_id=file_name_list[0],
        law_revision_id=file_name,
        law_title=law_title_text,
        law_num=law_num_text,
        enforce_date=file_name_list[1]
    )
    for article in main.iter('Article'):
        for chunk in xml_chunking(CHUNK_THRESHOLD, article):
            chunk.update(law_meta)
            chunk_result.append(chunk)
    print(law_meta)


# if __name__ == '__main__':
#     chunk_result = []
#     for path in XML_DIR.rglob('*.xml'):
#         root = ET.parse(path).getroot()
#         main = root.find('LawBody').find('MainProvision')
#         for article in main.iter('Article'):
#     for chunk in xml_chunking(CHUNK_THRESHOLD, article):
#         chunk.update(law_meta)
#         chunk_result.append(chunk)
