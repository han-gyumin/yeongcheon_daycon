import geopandas as gpd
import pandas as pd
import folium

# 1. Shapefile 불러오기
gdf = gpd.read_file("./ycdaycon/emd.shp", encoding="euc-kr")
gdf.to_file("yc.geojson", driver="GeoJSON")
# 2. 영천시 데이터만 필터링
gdf_yeongcheon = gdf[gdf["EMD_CD"].str.startswith("47230")].copy()


if gdf.crs is None:
    gdf.set_crs(epsg=5174, inplace=True)

gdf_yeongcheon = gdf[gdf["EMD_CD"].str.startswith("47230")].copy()
# 3. 면적 계산 (단위: km^2)
gdf_yeongcheon = gdf_yeongcheon.to_crs(epsg=5179)  # EPSG:5179는 면적 계산에 적합

# 이후 면적 계산 진행
gdf_yeongcheon["area_km2"] = gdf_yeongcheon.geometry.area / 1e6  # m² → km²

# 4. 인구 데이터 불러오기
pop_df = pd.read_csv("영천인구.csv")
pop_df = pop_df.rename(columns={"Unnamed: 0": "읍면동명"})






# 1. 매핑 데이터 불러오기
mapping_df = pd.read_csv("./ycdaycon/POS00006M_202201.csv", encoding="utf-8")

# 2. 영천시 데이터 필터링
mapping_df = mapping_df[mapping_df['CTGG_NM'] == '영천시']

# 3. 법정동과 행정동 매핑 딕셔너리 생성
법정_to_행정 = dict(zip(mapping_df['LGDNG_NM'], mapping_df['ADSTRD_NM']))

# 4. gdf_yeongcheon에 행정동명 컬럼 추가
gdf_yeongcheon['행정동명'] = gdf_yeongcheon['EMD_KOR_NM'].map(법정_to_행정)
gdf_yeongcheon['행정동명'] = gdf_yeongcheon['행정동명'].fillna(gdf_yeongcheon['EMD_KOR_NM'])

# 5. 인구 데이터 불러오기
pop_df = pd.read_csv("영천인구.csv")
pop_df = pop_df.rename(columns={"Unnamed: 0": "읍면동명"})
# 6. 병합
merged = gdf_yeongcheon.merge(pop_df, left_on="행정동명", right_on="읍면동명", how="left")





# 5. 병합
merged = gdf_yeongcheon.merge(pop_df, left_on="EMD_KOR_NM", right_on="읍면동명", how="left")

# 6. 인구 밀도 계산
merged["인구밀도"] = merged["총인구수"] / merged["area_km2"]


merged.head()
# 7. WGS84로 변환 (folium은 EPSG:4326만 가능)
merged = merged.to_crs(epsg=4326)

# 8. 지도 생성
center = merged.geometry.centroid.unary_union.centroid
m = folium.Map(location=[center.y, center.x], zoom_start=12)

# 9. Choropleth 시각화
folium.Choropleth(
    geo_data=merged,
    data=merged,
    columns=["EMD_KOR_NM", "인구밀도"],
    key_on="feature.properties.EMD_KOR_NM",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="영천시 인구밀도 (명/km²)"
).add_to(m)

# 10. 마우스 오버 시 읍면동명 + 밀도 표시
for _, r in merged.iterrows():
    folium.GeoJsonTooltip(fields=["EMD_KOR_NM", "인구밀도"],
                          aliases=["읍면동", "인구밀도(명/km²)"],
                          localize=True).add_to(folium.GeoJson(r["geometry"]).add_to(m))





m





import geopandas as gpd
import pandas as pd
import plotly.express as px
import json

# 1. shp 파일 불러오기 (encoding 지정)
gdf = gpd.read_file('./ycdaycon/emd.shp', encoding="cp949")

# 2. 좌표계 설정 및 변환 (보통 EPSG:5179 → WGS84)
gdf.set_crs(epsg=5179, inplace=True)
gdf = gdf.to_crs(epsg=4326)

# 3. EMD_CD 기준으로 영천시 필터링 (ex: 영천시는 47230으로 시작)
gdf["EMD_CD"] = gdf["EMD_CD"].astype(str)
gdf_yeongcheon = gdf[gdf["EMD_CD"].str.startswith("47230")].copy()

# 4. 이걸 GeoJSON으로 저장
gdf_yeongcheon.to_file("./emd_yeongcheon.geojson", driver="GeoJSON")

# 5. gdf와 사고 데이터 merge (왼쪽: gdf, 오른쪽: acc_df)
merged = gdf_yeongcheon.merge(pop_df, left_on='EMD_KOR_NM', right_on='읍면동명')


import geopandas as gpd
import plotly.graph_objects as go
import json

# 1. 영천시 GeoDataFrame 불러오기 (이미 필터링 되어 있다고 가정)
gdf_yeongcheon["EMD_CD"] = gdf_yeongcheon["EMD_CD"].astype(str)

# 2. 중심 좌표 계산
gdf_yeongcheon["centroid"] = gdf_yeongcheon.geometry.centroid
gdf_yeongcheon["lon"] = gdf_yeongcheon.centroid.x
gdf_yeongcheon["lat"] = gdf_yeongcheon.centroid.y

# 3. GeoJSON 불러오기
with open("./emd.geojson", encoding="utf-8") as f:
    geojson_data = json.load(f)

# 4. Choropleth 시각화 (색칠)
choropleth = go.Choroplethmapbox(
    geojson=geojson_data,
    locations=merged["EMD_CD"],
    z=merged["합계_계"],
    featureidkey="properties.EMD_CD",
    colorscale="RdBu",
    colorbar_title="총인구수",
    marker_opacity=0.8,
    marker_line_width=0.5,
    text=merged["EMD_KOR_NM"],  # ✅ 이게 hover 텍스트에 들어감
    hovertemplate="<b>%{text}</b><br>총인구수: %{z:,}명<extra></extra>"  # ✅ 형식 커스터마이징
)


# 5. 중심에 라벨 붙이기
text_layer = go.Scattermapbox(
    lat=gdf_yeongcheon["lat"],
    lon=gdf_yeongcheon["lon"],
    mode="text",
    text=gdf_yeongcheon["EMD_KOR_NM"],
    textfont=dict(size=12, color="black"),
    hoverinfo="none"
)

# 6. 지도 layout 설정
fig = go.Figure(data=[choropleth, text_layer])

fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=10,
    mapbox_center={"lat": 35.97, "lon": 128.93},
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    title="영천시 읍면동별 고령 인구수"
)

fig.show()
# fig.update_layout(
#     mapbox_style="white-bg"
# )


df= pd.read_csv("./df_final.csv",encoding="utf-8")
df.head()

from geopy.distance import geodesic

# 위도, 경도: (위도, 경도) 순서
building_coord = (35.976748, 128.964934)
hydrant_coord = (35.973500, 128.965800)

distance_m = geodesic(building_coord, hydrant_coord).meters
print(f"거리: {distance_m:.2f} m")


import folium
import pandas as pd
df_hydrant = pd.read_csv("./FireHydrants.csv")
df_yeongcheon = df_hydrant[df_hydrant["소화전 고유코드"].str.contains("영천", na=False)]
# 중심점 계산 (영천시 중심 또는 평균값)
center_lat = df_yeongcheon["위도"].mean()
center_lon = df_yeongcheon["경도"].mean()
df_yeongcheon.shape
# 지도 생성
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

# 소화전 마커 추가
for _, row in df_yeongcheon.iterrows():
    folium.Marker(
        location=[row["위도"], row["경도"]],
        tooltip=f"{row['위치명']} ({row['상태']})",
        icon=folium.Icon(color="red", icon="fire", prefix="fa")
    ).add_to(m)

# 결과 출력
m

df=pd.read_csv("./df_final.csv")
df['지상층수']
df['지상층수'].value_counts().sort_index()
df['지하층수'].value_counts().sort_index()
count = df[(df['지상층수'] == 0) & (df['지하층수'] == 0)].shape[0]
print("지상층수 0이고 지하층수도 0인 행 개수:", count)


import pandas as pd
import numpy as np

# 1. 데이터 불러오기
df = pd.read_csv("df_final.csv")
hydrants = pd.read_csv("FireHydrants.csv")

# 2. '영천' 소화전 필터링
hydrants_filtered = hydrants[hydrants["소화전 고유코드"].astype(str).str.contains("영천")].copy()

# 3. 소화전 좌표 추출 (numpy 배열로 빠르게 처리하기 위함)
hydrant_lats = np.radians(hydrants_filtered["위도"].values)
hydrant_lons = np.radians(hydrants_filtered["경도"].values)

# 4. haversine 거리 계산 함수 (단일 건물에 대해 가장 가까운 거리 반환)
def haversine_min_distance(lat1, lon1, hy_lats, hy_lons):
    R = 6371000  # 지구 반지름 (m)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    
    dlat = hy_lats - lat1
    dlon = hy_lons - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(hy_lats) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distances = R * c
    return distances.min()

# 5. 각 건물에 대해 최소 거리 계산
df["소화전거리"] = df.apply(
    lambda row: haversine_min_distance(row["위도"], row["경도"], hydrant_lats, hydrant_lons),
    axis=1
)




import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))
sns.histplot(df['소화전거리'], bins=50, kde=True, color='skyblue', edgecolor='black')
plt.title("소화전거리 분포 (히스토그램 + KDE)")
plt.xlabel("소화전거리 (m)")
plt.ylabel("건물 수")
plt.grid(True)
plt.show()







import pandas as pd
import numpy as np

# 1. 파일 불러오기
df = pd.read_csv("df_final.csv")
stations = pd.read_csv("FireStationsAmbulances.csv",encoding='cp949')

# 2. "영천"으로 시작하고, 위경도 결측치 없는 행만 필터링
stations_filtered = stations[
    stations["소속"].astype(str).str.startswith("영천") &
    stations["위도"].notna() &
    stations["경도"].notna()
].copy()

# 3. 소방서 좌표 배열
station_lats = np.radians(stations_filtered["위도"].values)
station_lons = np.radians(stations_filtered["경도"].values)

# 4. 거리 계산 함수
def haversine_min_distance(lat1, lon1, lats2, lons2):
    R = 6371000  # 지구 반지름 (m)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    dlat = lats2 - lat1
    dlon = lons2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lats2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return (R * c).min()

# 5. 건물별 가장 가까운 소방서 거리 계산
df["소방서거리"] = df.apply(
    lambda row: haversine_min_distance(row["위도"], row["경도"], station_lats, station_lons),
    axis=1
)


plt.figure(figsize=(10, 6))
sns.histplot(df["소방서거리"], bins=50, kde=True, color='salmon', edgecolor='black')
plt.title("소방서까지 거리 분포")
plt.xlabel("거리 (m)")
plt.ylabel("건물 수")
plt.grid(True)
plt.show()








import pandas as pd
from datetime import datetime

# 1. 현재 연도 가져오기
df = pd.read_csv("df_final.csv")
df['사용승인일(년도)'].value_counts().sort_index()

