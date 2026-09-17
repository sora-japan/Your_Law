import xml.etree.ElementTree as ET
import pathlib
import collections
from text_extraction import extract_text, normalization_text
from collections import Counter

BASE_DIR = pathlib.Path(__file__).parent
XML_DIR = BASE_DIR / "all_xml"

ver = {}
for path in XML_DIR.rglob("411AC0000000089_*.xml"):
    root = ET.parse(path).getroot()
    parts = path.stem.split('_')
    main = root.find('LawBody').find('MainProvision')
    ver[(parts[1], parts[2])] = {
        a.get('Num'): normalization_text(extract_text(a))
        for a in main.findall('.//Article')
    }

past_keys = [k for k in ver if k[0] <= '20260915']
current_key = max(past_keys)
current = ver[current_key]

print(current_key)
print('9_2 :', current.get('9_2'))
print('16_2:', current.get('16_2'))

# TODAY = '20260915'
# 
# # 1. 法令IDごとのファイル数（パース不要）
# files_per_law = Counter()
# for path in XML_DIR.rglob("*.xml"):
#     files_per_law[path.stem.split('_')[0]] += 1
# 
# targets = [law_id for law_id, n in files_per_law.items() if n >= 2]
# print("対象法令数:", len(targets))
# 
# # 2. 法令ごとに差分を測る
# law_results = {}
# removed_samples = []
# 
# for i, law_id in enumerate(targets, 1):
#     if i % 50 == 0:
#         print(f"  {i}/{len(targets)}")
# 
#     ver = {}
#     for path in XML_DIR.rglob(f"{law_id}_*.xml"):
#         try:
#             root = ET.parse(path).getroot()
#         except ET.ParseError as e:
#             parse_errors.append((path.name, str(e)))
#             continue
#         parts = path.stem.split('_')
#         main = root.find('LawBody').find('MainProvision')
#         ver[(parts[1], parts[2])] = {
#             a.get('Num'): normalization_text(extract_text(a))
#             for a in main.findall('.//Article')
#         }
# 
#     past_keys = [k for k in ver if k[0] <= TODAY]
#     if not past_keys:
#         continue
#     current_key = max(past_keys)
#     current = ver[current_key]
# 
#     diff_total = 0
#     removed_total = 0
#     for k in ver:
#         if k == current_key:
#             continue
#         future = ver[k]
#         changed = [n for n in current if n in future and current[n] != future[n]]
#         added = future.keys() - current.keys()
#         removed = current.keys() - future.keys()
#         diff_total += len(changed) + len(added) + len(removed)
#         removed_total += len(removed)
#         if removed and len(removed_samples) < 20:
#             removed_samples.append((law_id, k, sorted(removed)))
# 
#     law_results[law_id] = {
#         "版数": len(ver),
#         "現行条数": len(current),
#         "差分合計": diff_total,
#         "削除合計": removed_total,
#     }
# 
# # 3. 集計
# diff_sum = sum(r["差分合計"] for r in law_results.values())
# full_sum = sum(r["版数"] * r["現行条数"] for r in law_results.values())
# removed_laws = [k for k, r in law_results.items() if r["削除合計"] > 0]
# removed_sum = sum(r["削除合計"] for r in law_results.values())
# 
# print("差分チャンク合計:", diff_sum)
# print("全条を持つ場合:", full_sum)
# print("削除が発生した法令:", len(removed_laws), "件")
# print("削除された条の総数:", removed_sum)
# print("削除サンプル:")
# for s in removed_samples[:10]:
#     print("  ", s)

# ver = {}
# for path in XML_DIR.rglob("325AC0000000226_*.xml"):
#     try:
#         root = ET.parse(path).getroot()
#     except ET.ParseError as e:
#         parse_errors.append((path.name, str(e)))
#         continue
#     parts = path.stem.split('_')
#     root_body = root.find('LawBody')
#     root_main = root_body.find('MainProvision')
#     list_article = root_main.findall('.//Article')
#     ver[(parts[1], parts[2])] = {a.get('Num'): normalization_text(extract_text(a)) for a in list_article}
# 
# # print(len(ver))
# 
# 
# past_key = [c for c in ver if c[0] <= '20260915']
# current_key = max(past_key)
# current = ver[current_key]
# 
# result = {}
# for k in ver:
#     if k == current_key:
#         continue
#     future = ver[k]
#     changed = [nums for nums in current if nums in future and current[nums] != future[nums]]
#     added = future.keys() - current.keys()
#     removed = current.keys() - future.keys()
#     result[k] = {
#         "変更": len(changed),
#         "追加": len(added),
#         "削除": len(removed),
#         "合計": len(changed) + len(added) + len(removed),
#     }
# 
# for k in sorted(result):
#     r = result[k]
#     print(k, r)
# 
# total = sum(r["合計"] for r in result.values())
# print("差分チャンク合計:", total)
# print("全条を持つ場合:", len(ver) * len(current))

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
# 
#     parts = path.stem.split('_')
#     enforce = parts[1]
#     if enforce <= '20260916':
#         print(parts)

# group_couter = Counter()
# for path in XML_DIR.rglob("*.xml"):
#     parts = path.stem.split('_')
#     group_couter[(parts[0], parts[1])] += 1
# 
# group = {k: v for k, v in group_couter.items() if v >= 2}
# groups = {}
# # for path in XML_DIR.rglob("325AC0000000226_20270401*.xml"):
# # for i, (law_id, enforce_date) in enumerate(group.keys(), 1):
# #     print(f"{i}/{len(group)} {law_id}_{enforce_date}")
# for path in XML_DIR.rglob(f"323M40000100050_20270401_*.xml"):
#     try:
#         root = ET.parse(path).getroot()
#     except ET.ParseError as e:
#         parse_errors.append((path.name, str(e)))
#         continue
#     parts = path.stem.split('_')
#     key = (parts[0], parts[1])
#     amend_id = parts[2]
#     root_body = root.find('LawBody')
#     root_main = root_body.find('MainProvision')
#     # nums = {a.get('Num') for a in root_main.findall('.//Article')}
#     nums = set()
#     for a in root_main.findall('.//Article'):
#         nums.add(a.get('Num'))
#     groups.setdefault(key, {})[amend_id] = nums
#     # for amend_id, nums in groups.items():
# 
# 
# for key, ver in groups.items():
#     print(key, "版: ", sorted(ver.keys()))
#     latest = max(ver.keys())
#     print("候補: ", latest)
#     cand = ver[latest]
#     for amend_id, nums in ver.items():
#         if amend_id == latest:
#             continue
#         missing = nums - cand
#         print(key, amend_id, '欠落', len(missing), list(missing))



# law_id = path.stem.split('_')
# group_couter[(law_id[0], law_id[1])] += 1
# group = {k: v for k, v in group_couter.items() if v >= 2}
# print(group)

# group_couter = Counter()
# for path in XML_DIR.rglob("*.xml"):
#     law_id = path.stem.split('_')
#     group_couter[(law_id[0], law_id[1])] += 1
# 
# group = {k: v for k, v in group_couter.items() if v >= 2}
# print(group)


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

# count_article = Counter()
# list_article = []
# count_article_max = Counter()
# count_article_max["max"] = 0
# len_max_name = []
# count_article_tag = Counter()
# article_tag_count = Counter()
# len_paragraph_max = 0
# len_item_max = 0
# count_len_item = Counter()
# item_name = []
# for path in XML_DIR.rglob("*.xml"):
#     try:
#         root = ET.parse(path).getroot()
#     except ET.ParseError as e:
#         parse_errors.append((path.name, str(e)))
#         continue
# 
#     root_body = root.find('LawBody')
#     root_main = root_body.find('MainProvision')
#     root_article = root_main.findall('.//Article')
#     # root_tablecolumn = root_article.findall('.//TableColumn')
#     for article in root_article:
#         article_text = extract_text(article)
#         article_text_norma = normalization_text(article_text)
#         len_article_text = len(article_text_norma)
#         if len_article_text < 500:
#             count_article["~500文字"] += 1
#         elif len_article_text <= 1000:
#             count_article["500~1000"] += 1
#         elif len_article_text <= 2000:
#             count_article["1001~2000"] += 1
#         elif len_article_text <= 5000:
#             count_article["2001~5000"] += 1
#         elif len_article_text <= 8000:
#             count_article["5001 ~ 8000"] += 1
#         elif len_article_text >= 8001:
#             count_article["8001~"] += 1
#             for el in article.iter():
#                 article_tag_count[el.tag] += 1
#             for para in article.findall('Paragraph'):
#                 para_text = extract_text(para)
#                 len_paragraph_text = len(normalization_text(para_text))
#                 if len_paragraph_max < len_paragraph_text:
#                     len_paragraph_max = len_paragraph_text
#             for item in article.findall('.//Item'):
#                 item_text = extract_text(item)
#                 len_item_text = len(normalization_text(item_text))
#                 if len_item_text > 8000:
#                     count_len_item["8000文字を超える号の数"] += 1
#                     item_name.append((path.name, article.attrib.get('Num'), item.attrib.get('Num'), len_item_text))
#                 if len_item_max < len_item_text:
#                     len_item_max = len_item_text
#             # table_count = len(article.findall('.//TableColumn'))
#             # item_count = len(article.findall('.//Item'))
#             # if table_count >= 50:
#             #     count_article_tag["表が多い"] += 1
#             # elif item_count >= 50:
#             #     count_article_tag["号が多い"] += 1
#             # else:
#             #     count_article_tag["どちらでもない"] += 1
#         if count_article_max["max"] < len_article_text:
#             count_article_max["max"] = len_article_text
#             len_max_name.append(path.name)
# 
# 
# 
# print(count_article)
# print(count_article_max)
# print(len_max_name)
# print("===")
# print(count_article_tag)
# print("===")
# print(article_tag_count)
# print("===")
# print("paragraphの文字数", len_paragraph_max)
# print("===")
# print("itemの文字数", len_item_max)
# print("8000文字を超えるitemの数", count_len_item)
# print("8000文字超の号:", len(item_name), "件")
# for name, art_num, item_num, length in sorted(item_name):
#     print(f"  {length:>7,}  第{art_num}条 第{item_num}号  {name}")
# print("===")

# past_per_law = Counter()
# all_law_ids = set()
# 
# for path in XML_DIR.rglob("*.xml"):
#     parts = path.stem.split('_')
#     law_id, enforce_date = parts[0], parts[1]
#     all_law_ids.add(law_id)
#     if enforce_date <= "20260916":
#         past_per_law[law_id] += 1
# 
# dist = Counter(past_per_law.values())
# print("過去日ファイル数の分布: ", sorted(dist.items()))
# 
# multi = {k: v for k, v in past_per_law.items() if v >= 2}
# print("過去日が2件以上の法令: ", len(multi), "件")
# print("上位: ", sorted(multi.items(), key=lambda x: -x[1])[:10])
# 
# no_past = all_law_ids - set(past_per_law.keys())
# print("過去日を持たない法令:", len(no_past), "件")
# print("例:", list(no_past)[:10])

# for path in XML_DIR.rglob("332AC0000000026*.xml"):
#     parts = path.stem.split('_')
#     enforce = parts[1]
#     if enforce <= '20260916':
#         print(parts)


# enfoce = Counter()
# future_dates = Counter()
# for path in XML_DIR.rglob("*.xml"):
#     law_id = path.stem.split('_')
#     enforce_date = law_id[1]
#     enfoce[enforce_date[:4]] += 1
#     if enforce_date >= '21000101':
#         future_dates[enforce_date] += 1
# 
# print(enfoce)
# print(future_dates)

#for enforce_date, amend_id in sorted(ver):
#    print(enforce_date, amend_id)
# for i in sorted(ver):
#     print(i)


#print("合計：", len(ver), "版")


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
