import xml.etree.ElementTree as ET
import pathlib
from collections import Counter

BASE_DIR = pathlib.Path(__file__).parent
XML_DIR = BASE_DIR / "all_xml"

tag_count = Counter()
parse_errors = []
for path in XML_DIR.rglob("*.xml"):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        parse_errors.append((path.name, str(e)))
        continue
    root_body = root.find('LawBody')
    root_main= root_body.find('MainProvision')
    if root_main is None:
        main_none_count += 1
    else:
        for el in root_main:
            tag_count[el.tag] += 1
    # path_count.update()

for tag, count in tag_count.most_common():
    print(count, tag)
print("失敗:", len(parse_errors), "件")

print(XML_DIR)
print(XML_DIR.exists())
print(len(list(XML_DIR.rglob("*.xml"))))

# root.iter()

# type(root)
# print("===")
# print(tree)
# print("===")
# print(root)
# print("===")
# print(root.tag)
# print("===")
# print(root.attrib)
# print("===")
# print(root.find('LawNum'))
# print(root.find('LawBody'))
# print(root.findall('Law'))
# print(root.iter('Law'))
# 
# print("===")
# 
# print(path_data.exists())
# if path_data.exists():
#     print("ファイルが存在します")
# print(path_data)
# 
# if path.is_dir():
#     print(path_count)
