import xml.etree.ElementTree as ET
import pathlib
from xml.etree.ElementTree import Element
import re


def normalization_text(parts: str) -> str:
    result = re.sub(r'[\n\t ]+', '', parts).strip()
    return result


def extract_text(root: Element) -> str:
    parts = []
    if root.text is not None:
        parts.append(root.text)
    for element in root:
        if element.tag != 'Rt':
            parts.append(extract_text(element))
        if element.tail is not None:
            parts.append(element.tail)
    str_text = "".join(parts)
    return str_text
