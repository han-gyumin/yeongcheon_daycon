from pathlib import Path

import pandas as pd


import pandas as pd
import numpy as np

import matplotlib as mpl
import matplotlib.font_manager as fm

import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
import geopandas as gpd

app_dir = Path(__file__).parent
font_path = app_dir / "MaruBuri-Regular.ttf"
font_prop = fm.FontProperties(fname=font_path)
mpl.rcParams["axes.unicode_minus"] = False


# ✅ 영천 인구 데이터 불러오기
df_population = pd.read_csv("yc_pop.csv")

# 총인구수 전처리
df_population["총인구수"] = (
    df_population["총인구수"]
    .astype(str)
    .str.replace(",", "")
    .str.strip()
    .replace("", "0")
    .astype(float)
)

# 고령인구 전처리
df_population["고령인구"] = (
    df_population["고령인구"]
    .astype(str)
    .str.replace(",", "")
    .str.strip()
    .replace("", "0")
    .astype(float)
)

# 고령인구비율 계산 (소수점 두 자리까지 반올림)
df_population["고령인구비율"] = (df_population["고령인구"] / df_population["총인구수"] * 100).round(2)





df = pd.read_csv("df_final.csv")
# ----------------------------------------
# df['위험등급'] = pd.qcut(df['total_score'], q=3, labels=["낮음", "중간", "높음"])

# df.columns
# df.groupby("위험등급")[["사용승인일(년도)", "지상층수","지하층수", "소화전거리", "소방서거리"]].mean().reset_index()

# df.groupby("위험등급")["구조그룹"].value_counts(normalize=True).unstack()
# ----------------------------------------
df["사용승인일(년도)"]


df["사용승인일"] = pd.to_datetime(df["사용승인일"], errors="coerce")
df = df.dropna(subset=["사용승인일"])
df["건축연도"] = df["사용승인일"].dt.year
# 구조 분류 딕셔너리 정의
structure_map = {
    '목조 계열': ['일반목구조', '목구조', '트러스목구조', '통나무구조'],
    '조적식 구조': ['벽돌구조', '블록구조', '시멘트블럭조', '흙벽돌조', '조적구조', '기타조적구조'],
    '콘크리트 계열': ['철근콘크리트구조', '철골콘크리트구조', '철골철근콘크리트구조', '보강콘크리트조', '프리케스트콘크리트구조', '기타콘크리트구조'],
    '철골 계열': ['일반철골구조', '경량철골구조', '기타강구조', '철골구조', '공업화박판강구조(PEB)', '단일형강구조', '스틸하우스조', '철파이프조', '강파이프구조'],
    '조립식·판넬·기타': ['조립식판넬조', '컨테이너조'],
    '기타 / 특수 구조': ['석구조', '기타구조']
}

def map_structure_type(name):
    for group, items in structure_map.items():
        if name in items:
            return group
    return '미분류'

df['구조그룹'] = df['구조코드명'].apply(map_structure_type)



df['주용도코드명']



stations = pd.read_csv("FireStationsAmbulances.csv",encoding='cp949')

# 2. "영천"으로 시작하고, 위경도 결측치 없는 행만 필터링
stations_filtered = stations[
    stations["소속"].astype(str).str.startswith("영천") &
    stations["위도"].notna() &
    stations["경도"].notna()
].copy()

stations_fake = stations_filtered.copy()
stations_fake.loc[len(stations_fake)] = [
    82, "영천소방서", "임고면가상센터", np.nan, "123마1234", 36.03993, 128.9848
]
stations_fake.loc[len(stations_fake)] = [
    83, "영천소방서", "화북면가상센터", np.nan, "123마1235", 36.01903, 128.8532
]


# 3. 소방서 좌표 배열
station_lats = np.radians(stations_filtered["위도"].values)
station_lons = np.radians(stations_filtered["경도"].values)

station_lats2 = np.radians(stations_fake["위도"].values)
station_lons2 = np.radians(stations_fake["경도"].values)

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


df_fake = df.copy()
df_fake["소방서거리"] = df_fake.apply(
    lambda row: haversine_min_distance(row["위도"], row["경도"], station_lats2, station_lons2),
    axis=1
)


conditions = [
    df_fake["소방서거리"] < 1000,
    df_fake["소방서거리"] < 3000,
    df_fake["소방서거리"] < 5000,
    df_fake["소방서거리"] < 7000,
    df_fake["소방서거리"] >= 7000
]

# 해당 조건에 대한 점수
scores = [1.0, 2.0, 3.0, 4.0, 5.0]

# 점수 계산 열 생성
df_fake["소방관서거리_점수"] = np.select(conditions, scores)
a = df_fake['소방관서거리_점수'] - df['소방관서거리_점수']
a.unique()
weights = {
    "건물연차점수": 25,
    "지상층수_점수": 9,
    "지하층수_점수": 11,
    "비상용승강기_점수": 5,
    "주용도_점수": 20,
    "구조코드_점수": 15,
    "소화전거리_점수": 5,
    "소방관서거리_점수": 10
}
# ✅ df_fake에도 total_score 계산
df_fake["total_score"] = sum(df_fake[col] * weight for col, weight in weights.items())





def create_distance_hist_image():
    fig = plt.figure(figsize=(10, 6))
    sns.histplot(df["소방서거리"], bins=50, kde=True, color='salmon', edgecolor='black')
    plt.title("소방서 거리 분포", fontproperties=font_prop)
    plt.xlabel("거리 (m)", fontproperties=font_prop)
    plt.ylabel("건물 수", fontproperties=font_prop)
    plt.grid(True)

    # 이미지 버퍼에 저장
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64








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

def create_firehydrant_distance_plot():
    fig = plt.figure(figsize=(10, 6))
    sns.histplot(df['소화전거리'], bins=50, kde=True, color='skyblue', edgecolor='black')
    plt.title("소화전 거리 분포", fontproperties=font_prop)
    plt.xlabel("소화전거리 (m)", fontproperties=font_prop)
    plt.ylabel("건물 수", fontproperties=font_prop)
    plt.grid(True)

    # 이미지 저장 → 메모리 → base64 인코딩
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64
import folium

def create_building_map():
    center_lat = df["위도"].mean()
    center_lon = df["경도"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # ✅ 마커 추가
    for _, row in df.iterrows():
        lat, lon = row["위도"], row["경도"]
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.6,
            popup=f"건물 ID: {row.get('건물ID', 'N/A')}"  # 건물 ID가 있으면 팝업
        ).add_to(m)

    return m._repr_html_()



def create_hydrant_station_map():
    # 중심 좌표 계산
    center_lat = hydrants_filtered["위도"].mean()
    center_lon = hydrants_filtered["경도"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

    # 🔷 읍면동 경계 추가
    gdf = gpd.read_file("old.geojson").to_crs(epsg=4326)
    folium.GeoJson(
        gdf,
        name="읍면동 경계",
        style_function=lambda x: {
            "fillColor": "#ffffff",
            "color": "#999999",
            "weight": 1.5,
            "fillOpacity": 0.5,
            "opacity": 0.8
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["EMD_KOR_NM"],
            aliases=["읍면동"],
            localize=True
        )
    ).add_to(m)

    # 🔵 소화전 추가
    for _, row in hydrants_filtered.iterrows():
        folium.CircleMarker(
            location=[row["위도"], row["경도"]],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.7,
            popup=f"소화전 코드: {row['소화전 고유코드']}"
        ).add_to(m)

    # 🔴 소방서 추가
    for _, row in stations_filtered.iterrows():
        folium.Marker(
            location=[row["위도"], row["경도"]],
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
            popup=row["안전센터"]
        ).add_to(m)

    # 🟡 범례 추가 (HTML + CSS)
    legend_html = """
    <div style="
        position: fixed;
        bottom: 10px;
        left: 10px;
        z-index: 9999;
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 6px 10px;
        font-size: 13px;
        box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
        ">
        🔵 소화전<br>
        🔴 소방서
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m._repr_html_()


# def create_hydrant_station_map():
#     # 중심 좌표 설정 (영천시 중심 정도로 평균 좌표)
#     center_lat = hydrants_filtered["위도"].mean()
#     center_lon = hydrants_filtered["경도"].mean()
#     m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

#     # 🔵 소화전 점 찍기
#     for _, row in hydrants_filtered.iterrows():
#         folium.CircleMarker(
#             location=[row["위도"], row["경도"]],
#             radius=3,
#             color="blue",
#             fill=True,
#             fill_opacity=0.7,
#             popup=f"소화전 코드: {row['소화전 고유코드']}"
#         ).add_to(m)

#     # 🔴 소방서 마커 찍기
#     for _, row in stations_filtered.iterrows():
#         folium.Marker(
#             location=[row["위도"], row["경도"]],
#             icon=folium.Icon(color="red", icon="fire"),
#             popup=f"소방서: {row['소속']}"
#         ).add_to(m)

#     return m._repr_html_()


weights = {
                "건물연차점수": 25,
                "지상층수_점수": 9,
                "지하층수_점수": 11,
                "비상용승강기_점수": 5,
                "주용도_점수": 20,
                "구조코드_점수": 15,
                "소화전거리_점수": 5,
                "소방관서거리_점수": 10
            }
            # ✅ total_score 계산
df["total_score"] = sum(df[col] * weight for col, weight in weights.items())




# top5_score = df.sort_values(by="total_score", ascending=False).head(5)

# # 읍면동 기준 중복 제거 (total_score 높은 값 기준으로)
# df_unique = df.sort_values(by="total_score", ascending=False).drop_duplicates(subset="읍면동")

# 상위 4개 추출
top5_score = ( 
    df.groupby("읍면동")["total_score"]
    .mean()
    .reset_index()
    .sort_values(by="total_score", ascending=False)
    .head(5)
)

# 고령인구비율 상위 4개 지역 추출
top5_old = df_population.sort_values(by="고령인구비율", ascending=False).head(5)

# 교집합 추출
common_areas = set(top5_score['읍면동']) & set(top5_old['읍면동'])

# 겹치는 읍면동만 필터링
score_filtered = top5_score[top5_score["읍면동"].isin(common_areas)][["읍면동", "total_score"]]
old_filtered = top5_old[top5_old["읍면동"].isin(common_areas)][["읍면동", "고령인구비율"]]

# 두 데이터프레임 병합
common_df = pd.merge(score_filtered, old_filtered, on="읍면동")


region_list = df_population["읍면동"].unique().tolist()
half = len(region_list) // 2
region_score1 = region_list[:half]
region_score2 = region_list[half:]