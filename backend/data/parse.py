import xml.etree.ElementTree as ET
import pathlib
from collections import Counter
from text_extraction import extract_text, normalization_text

BASE_DIR = pathlib.Path(__file__).parent
XML_DIR = BASE_DIR / "all_xml"

# tag_count = Counter()
# parse_errors = []
# article_none_count = 0
# article_none_name = []
# hide_count = Counter()
# hide_true_name = []
# delete_count = Counter()
# extract_count = Counter()
# rt_count = Counter()
# column_stats = Counter()
# column_inner_space_samples = []
# for path in XML_DIR.rglob("*.xml"):
#     try:
#         root = ET.parse(path).getroot()
#     except ET.ParseError as e:
#         parse_errors.append((path.name, str(e)))
#         continue
#     root_body = root.find('LawBody')
#     root_main = root_body.find('MainProvision')
#     root_article = root_main.findall('.//Article')
#     hide = root.findall('.//*[@Hide]')
#     delete = root.findall('.//*[@Delete]')
#     extract = root.findall('.//*[@Extract]')
#     rt = root.findall('.//Rt')
#     for el in rt:
#         if el.tail is not None:
#             el_tail = el.tail.strip()
#             if el_tail != "":
#                 rt_count[el_tail] += 1
#     for el in extract:
#         extract_count[el.tag] += 1
#     for el in delete:
#         delete_count[el.attrib['Delete']] += 1
#     for el in hide:
#         hide_count[el.attrib['Hide']] += 1
#         if el.attrib['Hide'] == 'true':
#             hide_true_name.append(path.name)
#     if not root_article:
#         article_none_count += 1
#         article_none_name.append((path.name))
#     else:
#         for el in root_article:
#             tag_count[el.tag] += 1
# # --- ループの中 ---
#     for el in root.findall('.//Column'):
#         raw = extract_text(el)
#         stripped = raw.strip()
# 
#         if stripped == "":
#             column_stats['空'] += 1
#             continue
# 
#         if raw != stripped:
#             column_stats['前後に空白あり'] += 1
#         else:
#             column_stats['前後に空白なし'] += 1
# 
#         if ' ' in stripped:
#             column_stats['内部に半角スペース'] += 1
#         if '\u3000' in stripped:
#             column_stats['内部に全角スペース'] += 1
#         if '\n' in stripped:
#             column_stats['内部に改行'] += 1
#         if '\t' in stripped:
#             column_stats['内部にタブ'] += 1
# 
#         if ' ' in stripped:
#             if len(column_inner_space_samples) < 1:
#                 display = stripped.replace(' ', '␣')
#                 column_inner_space_samples.append((path.name, display))
#     # path_count.update()

count_article = Counter()
list_article = []
count_article_max = Counter()
count_article_max["max"] = 0
len_max_name = []
for path in XML_DIR.rglob("*.xml"):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        parse_errors.append((path.name, str(e)))
        continue

    root_body = root.find('LawBody')
    root_main = root_body.find('MainProvision')
    root_article = root_main.findall('.//Article')
    for article in root_article:
        article_text = extract_text(article)
        article_text_norma = normalization_text(article_text)
        len_article_text = len(article_text_norma)
        if len_article_text < 500:
            count_article["~500文字"] += 1
        elif len_article_text <= 1000:
            count_article["500~1000"] += 1
        elif len_article_text <= 2000:
            count_article["1001~2000"] += 1
        elif len_article_text <= 5000:
            count_article["2001~5000"] += 1
        elif len_article_text <= 8000:
            count_article["5001 ~ 8000"] += 1
        elif len_article_text >= 8001:
            count_article["8001~"] += 1
        if count_article_max["max"] < len_article_text:
            count_article_max["max"] = len_article_text
            len_max_name.append(path.name)

print(count_article)
print(count_article_max)
print(len_max_name)
# print("一番長い条: ", count_article.most_common())

# print(root.attrib)
# 
# print("===")
# print("Column の内訳:", column_stats)
# print("内部に空白があるサンプル:")
# for name, text in column_inner_space_samples:
#     print(" ", name, text)
# 
# print("=====")
# print("rtの数、.tailにテキストが入っているか: ", rt_count)
# 
# print("=====")
# print("Extractの数: ", extract_count)
# 
# print("=====")
# print("Deleteの数 :", delete_count)
# 
# print("=====")
# print("Hideの数: ", hide_count)
# print("Hide=Trueのファイル名: ", hide_true_name)
# print("条を持たない法令: ", article_none_count, "件")
# article_none_five = article_none_name[:5]
# print("条を持たない法令のファイル名: ", article_none_five)
# 
# for tag, count in tag_count.most_common():
#     print(count, tag)
# print("失敗:", len(parse_errors), "件")
# 
# print(XML_DIR)
# print(XML_DIR.exists())
# print(len(list(XML_DIR.rglob("*.xml"))))

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
