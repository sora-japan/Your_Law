import xml.etree.ElementTree as ET
from text_extraction import extract_text, normalization_text
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
XML_FILE = BASE_DIR / 'all_xml'
CHUNK_THRESHOLD = 1000

def article_chunking(CHUNK_THRESHOLD: int, text: str, num: int) -> dict:
    result = {}
    length = len(text)
    if length <= CHUNK_THRESHOLD:
        result = {num: text}
        return result
    else:


if __name__ == '__main__':
    for path in XML_FILE.rgrob('335M50000400013_*.xml'):
        root = ET.parse(path).getroot()
        main = root.find('LawBody').find('MainProvision')
        for article in main.findall('.//Article'):
            text = normalization_text(extract_text(article))
            article_number = article.get('Num')
            chunk_text = article_chunking(CHUNK_THRESHOLD, text, article_number)
