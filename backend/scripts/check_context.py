if __name__ == '__main__':
    from src.generation.prompt import build_context

    SAMPLE_RESULTS = [
        # 条のみ（level=Article）。項番号を持たないチャンク
        {
            'chunk_id': '409AC0000000123_20261001_507AC0000000087#92',
            'level': 'Article',
            'law_title': '介護保険法',
            'provision': '本則',
            'article_num': '9',
            'paragraph_num': '',
            'item_num': '',
            'text': '次に掲げる者は、市町村又は特別区が行う介護保険の被保険者とする。',
        },
        # 条＋項（level=Paragraph）。ts024 で誤読された形
        {
            'chunk_id': '409AC0000000123_20261001_507AC0000000087#105',
            'level': 'Paragraph',
            'law_title': '介護保険法',
            'provision': '本則',
            'article_num': '27',
            'paragraph_num': '11',
            'item_num': '',
            'text': '第一項の申請に対する処分は、当該申請のあった日から三十日以内にしなければならない。'
                    'ただし、当該申請に係る被保険者の心身の状況の調査に日時を要する等特別な理由が'
                    'ある場合には、当該申請のあった日から三十日以内に、当該被保険者に対し、'
                    '当該申請に対する処分をするためになお要する期間及びその理由を通知し、'
                    'これを延期することができる。',
        },
        # 条＋項＋号（level=Item）
        {
            'chunk_id': '351AC0000000057_20260812_508AC0000000064#80',
            'level': 'Item',
            'law_title': '特定商取引に関する法律',
            'provision': '本則',
            'article_num': '26',
            'paragraph_num': '1',
            'item_num': '2',
            'text': '本邦外に在る者に対する商品若しくは権利の販売又は役務の提供',
        },
        # 枝番号の条。「第15_3条」と出ることを確認する（ADR-0020 の未処理分）
        {
            'chunk_id': '351AC0000000057_20260812_508AC0000000064#45',
            'level': 'Article',
            'law_title': '特定商取引に関する法律',
            'provision': '本則',
            'article_num': '15_3',
            'paragraph_num': '',
            'item_num': '',
            'text': '通信販売をする場合の商品又は特定権利の販売条件について広告をした販売業者が'
                    '…その売買契約に係る商品の引渡し又は特定権利の移転を受けた日から起算して'
                    '八日を経過するまでの間は、その売買契約の申込みの撤回又はその売買契約の'
                    '解除を行うことができる。ただし、当該販売業者が申込みの撤回等についての'
                    '特約を当該広告に表示していた場合には、この限りでない。',
        },
        # 附則で番号を一切持たないチャンク。3つとも空のときの挙動
        {
            'chunk_id': '351AC0000000057_20260812_508AC0000000064#317',
            'level': 'Paragraph',
            'law_title': '特定商取引に関する法律',
            'provision': '附則',
            'article_num': '',
            'paragraph_num': '',
            'item_num': '',
            'text': 'この法律は、公布の日から起算して六月を超えない範囲内において'
                    '政令で定める日から施行する。',
        },
    ]

    prompt = build_context(SAMPLE_RESULTS)
    print(prompt)
