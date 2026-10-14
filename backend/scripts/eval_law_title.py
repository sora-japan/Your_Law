"""
法令名のキーワードから法令IDを探す調査スクリプト。

評価データの gold に書く法令IDを特定するために使う。
ファイル名に法令名は入っていないため、XMLの LawTitle を読む。

現行版のみを対象にする。gold の法令はコーパスに存在しなければならず、
コーパスは現行版だけで構成されるため。

LawTitle は .text で読まない。先頭にルビ等の子要素があると None になり、
途中に子要素があると黙って切れた文字列が返るため。
"""
from src.ingestion.chunk_splitting import find_current_version_paths, extract_text
from src import config
import xml.etree.ElementTree as ET

TARGETS = ('介護保険法', '建築基準', '都市計画', '消防法', '食品衛生', '特定商取引')

if __name__ == '__main__':
    child_title_count = 0
    current_paths = find_current_version_paths(config.XML_DIR)
    print(f'対象ファイル: {len(current_paths)}')

    matches = {target: [] for target in TARGETS}
    nested_titles = []

    for current_path in current_paths:
        root = ET.parse(current_path).getroot()
        law_title = root.find('.//LawTitle')
        law_id = current_path.stem.split('_')[0]

        title = extract_text(law_title)
        # if len(list(law_title)) > 0:
        #     nested_titles.append((law_id, title, law_title.text))
        for target in TARGETS:
            if target in title:
                matches[target].append((title, law_id, current_path))
    print(f'LawTitleが子要素を持つファイル: {len(nested_titles)}件')
    for law_id, title, raw_text in nested_titles:
        print(f'{law_id}: {title}')
        # print(f'.textだけだと: {raw_text}')
    for target in TARGETS:
        rows = sorted(matches[target])
        print(f'==={target} {len(rows)}===')
        for title, law_id, path in rows:
            print(f'{law_id}: {title}')
            print(f'{path}')
