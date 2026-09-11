import xml.etree.ElementTree as ET
import pathlib
from collections import Counter

path_data = pathlib.Path(__file__).parent
path_count = Counter()
for path in path_data.rglob("*.xml"):
    tree = ET.parse(path)
    root = tree.getroot()
    for child in root:
        tag[] = child.tag
        path_count.update(tag)

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
