import xml.etree.ElementTree as ET
import pathlib
from xml.etree.ElementTree import Element
import re

# BASE_DIR = pathlib.Path(__file__).parent
# XML_DIR = BASE_DIR / "all_xml"

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

if __name__ == "__main__":
# このループ処理は、ほかのファイル内に書いた方が綺麗？
    text_list = []
    # for path in XML_DIR.rglob("*.xml"):
    # path_xml = pathlib.Path("502AC1000000077_20201211_000000000000000.xml")
    path_xml = pathlib.Path("325AC0000000201_20261126_508AC0000000023.xml")
    #  for path in path_xml.glob('*.xml'):
    #      try:
    #          root = ET.parse(path).getroot()
    #          title = root.find('LawBody').find('LawTitle')
    #          text_list = extract_text(title)
    #      except ET.ParseError as e: # エラーが出るものはなかったが、一応必要？
    #          parse_errors.append((path.name, str(e)))
    #     continue
    # return root
    root = ET.parse(path_xml).getroot()
    text_list = extract_text(root)
    clear_norma = normalization_text(text_list)
    print(clear_norma)
    # print(text_list)
