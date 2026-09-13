import xml.etree.ElementTree as ET
import pathlib
from xml.etree.ElementTree import Element

# BASE_DIR = pathlib.Path(__file__).parent
# XML_DIR = BASE_DIR / "all_xml"

def extract_text(root: Element) -> str:
    xml_str = root.text
    return xml_str

if __name__ == "__main__":
# このループ処理は、ほかのファイル内に書いた方が綺麗？
    text_list = []
    # for path in XML_DIR.rglob("*.xml"):
    path_xml = pathlib.Path("502AC1000000077_20201211_000000000000000.xml")
    for path in path_xml:
        try:
            root = ET.parse(path).getroot()
            root.find('LawBody')
            text_list = extract_text(root)
        except ET.ParseError as e: # エラーが出るものはなかったが、一応必要？
            parse_errors.append((path.name, str(e)))
    #     continue
    # return root
    print(text_list)
