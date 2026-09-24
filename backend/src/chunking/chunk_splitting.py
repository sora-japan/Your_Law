import xml.etree.ElementTree as ET
from text_extraction import extract_text, normalization_text

CHUNK_THRESHOLD = 1000

def article_chunking(CHUNK_THRESHOLD: int, num: int, text: str):
    length = len(text)
    if length <= CHUNK_THRESHOLD:
        return text
    else:
        
