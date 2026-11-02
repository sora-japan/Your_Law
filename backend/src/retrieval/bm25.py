import unicodedata
import re


def bigram(text: str) -> list[str]:
    normalized_text = unicodedata.normalize('NFKC', text)
    clean_text = re.split('[、。・()「」]', normalized_text)
    result = []
    for clean in clean_text:
        result_text = [clean[i: i + 2] for i in range(len(clean) - 1)]
        result.extend(result_text)
    return result


if __name__ == '__main__':
    text = '今日は、１０月２０日です。'
    result = bigram(text)
    print(result)
