def is_match(gold: dict, retrieved_meta: dict) -> bool:
    law_id_match = (gold.get('law_id') == retrieved_meta.get('law_id'))
    provision_match = (gold.get('provision') == retrieved_meta.get('provision'))
    article_num_match = (gold.get('article_num') == retrieved_meta.get('article_num'))
    if law_id_match and provision_match and article_num_match:
        return True
    else:
        return False
