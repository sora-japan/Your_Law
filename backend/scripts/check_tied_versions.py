import pathlib
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = pathlib.Path(__file__).parent.parent
XML_DIR = BASE_DIR / "data" / "all_xml"

today = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')

stems = []
law_ver = {}
for path in XML_DIR.rglob('*.xml'):
    parts = path.stem.split('_')
    stems.append(path.stem)
    law_id = parts[0]
    enforce_date = parts[1]
    amend_law_id = parts[2]
    law_ver.setdefault(law_id, []).append((enforce_date, amend_law_id, path))

print('版に一意性があるか確認')
print(len(stems))
print(len(set(stems)))

print('===')
file_list = [len(v) for v in law_ver.values()]
print(f'ファイル数: {sum(file_list)}')
print(f'法令数: {len(law_ver)}')

ver_counts = Counter()
for law_id, v in law_ver.items():
    ver_counts[law_id] = len(v)
most_law_id, most_count = ver_counts.most_common(1)[0]
print(f'最多バージョン: {most_law_id}が{most_count}件')

latest_dates = {}
for law_id, versions in law_ver.items():
    enforced = [v for v in versions if v[0] <= today]
    if not enforced:
        continue
    date_list = [date for date, _, _ in enforced]
    latest_dates[law_id] = max(date_list)
print(f'施行済みの版を持つ法令数: {len(latest_dates)}')
print(f'{most_law_id}の最新施行日 = {latest_dates[most_law_id]}')

tied_laws = []
for law_id, versions in law_ver.items():
    latest = latest_dates.get(law_id)
    if latest is None:
        continue
    same_day = [(amend, path) for date, amend, path in versions if date == latest]
    if len(same_day) > 1:
        tied_laws.append((law_id, latest, sorted(same_day)))
print(f'影響する法令: {len(tied_laws)}')

for law_id, date, same_day in tied_laws:
    amend_ids = [amend for amend, _ in same_day]
    print(law_id, date, amend_ids)


def main_article_nums(path: pathlib.Path) -> set:
    root = ET.parse(path).getroot()
    main = root.find('LawBody').find('MainProvision')
    num_set = set()
    for article in main.findall('.//Article'):
        num_set.add(article.get('Num', ''))
    return num_set


if __name__ == '__main__':
    print('===')
    compared = 0
    missing_count = 0
    for law_id, enforce_date, same_day in tied_laws:
        # tied_lawsはsort済みなので、一番最後のものを候補とする
        candidate = main_article_nums(same_day[-1][1])
        for other_amend, other_path in same_day[:-1]:
            other_set = main_article_nums(other_path)
            ans = other_set - candidate
            compared += 1
            if ans:
                print('他版にあって候補にない条番号: ', ans, law_id, other_amend)
                missing_count += 1
            print(law_id, same_day[-1][0], len(candidate), other_amend, len(other_set))
    print(f'計算した回数: {compared}')
    print(f'失った条があった回数: {missing_count}')
