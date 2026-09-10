import requests

headers = {
    'user-agent': 
}

res = requests.get('https://laws.e-gov.go.jp/api/2/law_data/142AC0000000039', headers=headers)
# {142AC0000000039_20250601_504AC0000000068}
print(res.status_code)
print(res.json())
