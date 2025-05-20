import pandas as pd

# 건축물대장 불러오기 xlsx
df = pd.read_excel('건축물대장.xlsx')

# 필요한 칼럼만 가져오기
columns_to_extract = ['대지위치',
    '사용승인일', '지상층수', '지하층수',
      '높이(m)','구조코드명', '기타구조', '주용도코드명',
        '지붕코드명','기타지붕', '비상용승강기수'
]
df_building = df[columns_to_extract]

# 사용승인일 열에서 년도만 가져오기
df_building.loc[:, '사용승인일'] = df_building['사용승인일'].astype(str).str.strip()
df_building.loc[:, '사용승인일(년도)'] = df_building['사용승인일'].apply(
    lambda x: x[:4] if len(x) in [5, 6, 8] else x
)

# 사용승인일(년도) 열 위치 변경
cols = list(df_building.columns)
idx = cols.index('사용승인일')
cols.remove('사용승인일(년도)')
cols.insert(idx + 1, '사용승인일(년도)')
df_final = df_building[cols]

# 위도 경도 파일 불러오기
df_long_lat = pd.read_csv('df_unique.csv')

# 건축물대장파일과 위,경도 파일 붙이기
df_final = df_building.merge(df_long_lat, on='대지위치', how='left')

# 칼럼별 결측치 확인하기
empty_counts = {}
for col in df_final.columns:
    empty_count = ((df_final[col].isna()) | (df_final[col] == '')).sum()
    empty_counts[col] = empty_count
empty_counts_series = pd.Series(empty_counts)
print(empty_counts_series)

# 결측치 삭제하기
# 1. '사용승인일(년도)' 전처리 - 조건 하나씩 나누기
df_final = df_final[df_final['사용승인일(년도)'].notna()]
df_final = df_final[df_final['사용승인일(년도)'].astype(str).str.strip() != '']
df_final = df_final[df_final['사용승인일'] != 30000317]
df_final = df_final[df_final['사용승인일(년도)'] != 'nan']

# 2. 나머지 변수들에 대한 결측치 제거
df_final = df_final[df_final['주용도코드명'].notna()]
df_final = df_final[df_final['기타구조'].notna()]
df_final = df_final[df_final['기타지붕'].notna()]
df_final = df_final[df_final['지붕코드명'].notna()]
df_final = df_final[df_final['위도'].notna()]
df_final = df_final[df_final['경도'].notna()]
df_final = df_final[df_final['지상층수'] != 0]

df_final['지상층수'].value_counts()
df_final['지하층수'].value_counts()
df_final['사용승인일(년도)'].value_counts()

df_final[df_final['사용승인일'] == 30000317]

# 결측치 삭제 후 확인하기
empty_counts = {}
for col in df_final.columns:
    empty_count = ((df_final[col].isna()) | (df_final[col] == '')).sum()
    empty_counts[col] = empty_count
# 결과를 시리즈로 변환해 보기 쉽게 출력
empty_counts_series = pd.Series(empty_counts)
print(empty_counts_series)

df_final.to_excel('df_final.xlsx', index=False)

# 소화전 데이터 가져오기
df_firedrants = pd.read_csv('firehydrants.csv')

# 영천 소화전중 사용가능데이터만 가져오기
firedrants_yc = df_firedrants[df_firedrants['소화전 고유코드'].str.contains('영천', na=False)]
firedrants_yc = firedrants_yc[firedrants_yc['상태'] == '사용가']