import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

df = pd.read_csv("C:/Users/USER/Desktop/ycdatacon/ycdaycon/df_final.csv")
# 읍면동 경계 GeoDataFrame
gdf_emd = gpd.read_file("C:/Users/USER/Desktop/ycdatacon/old.geojson")  # 또는 .shp 파일

# 좌표계 통일 (보통 WGS84 사용)
gdf_emd = gdf_emd.to_crs(epsg=4326)


# 기존 df의 위도/경도 → Point 형식으로 변환
geometry = [Point(xy) for xy in zip(df["경도"], df["위도"])]
gdf_building = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


# 공간 조인 (건물이 속한 읍면동 정보 붙이기)
gdf_joined = gpd.sjoin(gdf_building, gdf_emd[["EMD_KOR_NM", "geometry"]], how="left", predicate="within")

# 결과 확인
print(gdf_joined[["위도", "경도", "EMD_KOR_NM"]].head())

df["읍면동"] = gdf_joined["EMD_KOR_NM"]
df.to_csv("df_final.csv")