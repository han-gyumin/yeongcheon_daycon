import requests
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://apis.data.go.kr/5100000/yeongcheon_onsd_pasng_road1"
service_key = "kQPgV2SgwW+Pok4VNe4d2v1FEf0wvCsPyWphZsAZMlb5qHJI6k13Jm93u9ydyTYIrk3A1MghznrLYmyX5Lta+w=="

params = {
    'serviceKey': service_key,
    'pageNo': 1,
    'numOfRows': 10,
    '_type': 'json'
}

response = requests.get(url, params=params, verify=False)
data = response.json()
items = data['response']['body']['items']
df = pd.DataFrame(items)
df.to_csv("output.csv", index=False, encoding="utf-8-sig")
print("✅ 저장 완료!")

import ssl
print(ssl.OPENSSL_VERSION)
