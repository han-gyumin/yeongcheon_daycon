import requests
import pandas as pd
import xml.etree.ElementTree as ET

# ✅ API 기본 정보
url = "https://apis.data.go.kr/5100000/yeongcheon_onsd_pasng_road1"
service_key = "kQPgV2SgwW+Pok4VNe4d2v1FEf0wvCsPyWphZsAZMlb5qHJI6k13Jm93u9ydyTYIrk3A1MghznrLYmyX5Lta+w=="

# ✅ 파라미터 구성
params = {
    "serviceKey": service_key,
    "pageNo": 1,
    "numOfRows": 100,
}

# ✅ 요청 시 SSL 검증을 끄는 경우 (테스트용)
response = requests.get(url, params=params, verify=False)

# ✅ 응답 내용 일부 출력 (확인용)
print(response.text[:500])

# ✅ XML 파싱
try:
    root = ET.fromstring(response.content)
    items = root.findall(".//item")

    data = []
    for item in items:
        row = {child.tag: child.text for child in item}
        data.append(row)

    # ✅ CSV로 저장
    df = pd.DataFrame(data)
    df.to_csv("영천시_일방통행도로.csv", index=False, encoding="utf-8-sig")
    print("✅ 저장 완료: 영천시_일방통행도로.csv")

except ET.ParseError:
    print("❌ 응답이 XML 형식이 아닙니다. HTML 오류 페이지일 수 있습니다.")