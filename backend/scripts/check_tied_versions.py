import pathlib
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = pathlib.Path(__file__).parent.parent
XML_DIR = BASE_DIR / "data" / "all_xml"

today = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y%m%d')

law_id_counter = Counter()
law_ver = {}
for path in XML_DIR.rglob('*.xml'):
    parts = path.stem.split('_')
    law_id = parts[0]
    enforce_date = parts[1]
    amend_law_id = parts[2]
    law_ver.setdefault(law_id, []).append((enforce_date, amend_law_id, path))

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
