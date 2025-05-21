from shiny import App, ui, render, reactive, req
import pandas as pd
import geopandas as gpd
import folium
import plotly.express as px
from shared import app_dir, df_population, df,create_distance_hist_image, common_df,create_firehydrant_distance_plot,create_building_map,create_hydrant_station_map, stations_filtered

region_list = df_population["읍면동"].unique().tolist()

# UI 구성
def app_ui(request):
    return ui.page_navbar(
        ui.nav_panel("프로젝트 개요",
             ui.layout_columns(
    ui.div(
        ui.img(src="/text1.png", style="width:100%; height:auto;"),
        style="padding: 5px; display: flex; align-items: center; justify-content: center; min-height: 120px;"
    ),
    ui.div(
        ui.img(src="/text2.png", style="width:100%; height:auto;"),
        style="padding: 5px; display: flex; align-items: center; justify-content: center; min-height: 120px;"
    ),
    ui.div(
        ui.img(src="/text3.png", style="width:100%; height:auto;"),
        style="padding: 5px; display: flex; align-items: center; justify-content: center; min-height: 120px;"
    )
),
             ui.layout_columns(
                    ui.div(
                        ui.img(src="../img1.png", style="width:100%"),
                        style="padding: 5px;"
                    ),
                    ui.div(
                        ui.img(src="../img2.png", style="width:100%"),
                        style="padding: 5px;"
                    )
             ),
              # 🔸 프로젝트 목적 카드
            ui.card(
                ui.markdown("""
                    ### **프로젝트 목적**

                    #### - 영천시의 건축물대장 데이터를 기반으로 화재에 취약한 건물의 분포를 분석  
                    #### - 건축 구조, 층수, 접근성 등을 반영한 **행정동 단위의 화재 취약 점수**를 산출  
                    #### - 소방서·소화전·대피소 등의 **재난 대응 인프라 우선 설치 지역**을 도출하고  
                    ####   **인터랙티브 지도 시각화**로 행정 활용을 지원
                """),
                full_screen=True
            ),

            # 🔸 프로젝트 기대효과 카드
            ui.card(
                ui.markdown("""
                    ### **프로젝트 기대효과**

                    #### - **데이터 기반의 화재 취약 지역 파악**으로 인한 재난 대응 효율성 향상  
                    #### - 고령 인구 밀집 지역 등 **사회적 약자 보호 강화**  
                    #### - 소방 인프라 미흡 지역의 선제적 대응 가능  
                    #### - 영천시 외 타 지자체에서도 활용 가능한 **분석·시각화 템플릿 모델 제시**
                """),
                full_screen=True
            )
             
        ),
        ui.nav_panel("시각화",
            ui.layout_columns(
                ui.card(
                    ui.card_header("건물 노후도 구간별 분포 (2025년 기준)"),
                    ui.output_ui("show_building_age_bar"),
                    full_screen=True
                ),
                
                ui.card(
                    ui.card_header("구조별 건물 분포"),
                    ui.output_ui("show_structure_pie"),
                    full_screen=True
                )
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("주용도별 건물 분포"),
                    ui.output_ui("show_usage_pie"),
                    full_screen=True
                ),
                ui.card(
                    ui.card_header("비상용 승강기 수 분포 (5층 이상 건물)"),
                    ui.output_ui("show_elevator_pie"),
                    full_screen=True
                )
            ),
            ui.layout_columns(
                # 🔵 소방서 거리 분포
                ui.card(
                    ui.card_header("소방서 거리 분포 시각화"),
                    ui.output_ui("show_station_distance_plot")
                ),

                
                # 🔵 소화전 거리 분포
                ui.card(
                    ui.card_header("🧯 소화전 거리 분포"),
                    ui.output_ui("show_firehydrant_distance_plot")
                ),
            ),
            ui.layout_columns(
                # 🔴 소화전 및 소방서 위치 지도
                ui.card(
                    ui.card_header("🧯 소화전 및 소방서 위치 + 읍면동 경계 지도"),
                    ui.output_ui("show_hydrant_station_map"),
                    height="100%"
                )
                ,

                # 📋 소방관서 테이블
                ui.card(
                    ui.card_header("📋 영천시 소방관서 정보"),
                    ui.output_data_frame("show_station_table")
                )
            )
        ),
        ui.nav_panel(
            "위험스코어",
            ui.layout_sidebar(
            ui.sidebar(
                ui.input_checkbox_group("region", "읍면동 선택", choices=region_list, selected=region_list),
                title="Filter controls"
            ),
                ui.card(
                    ui.card_header("📊 평균 위험 점수 상·하위 건물 특성 비교"),
                    ui.output_data_frame("show_summary"),
                    full_screen=True
                
            ),
                ui.layout_columns(
                ui.card(
                    ui.card_header("📊 읍면동별 평균 위험 점수 및 건물 특성 비교"),
                    ui.output_data_frame("show_summary2"),
                    full_screen=True
    )
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("읍면동별 평균 점수 시각화"),
                    ui.output_ui("show_score_map"),
                    full_screen=True
                ),
                ui.card(
                    ui.card_header("영천시 고령인구 비율 시각화"),
                    ui.output_ui("show_population_map"),
                    full_screen=True
                )
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("읍면동별 인구 및 고령 인구 현황"),
                    ui.output_data_frame("population_table"),
                    full_screen=True
                ))
            ),
        ),
                
                
        
        
        
        ui.nav_panel("결론",
            ui.card(
        ui.card_header("🔍 데이터 기반 분석을 통한 화재 취약 지역 식별 및 시사점 도출"),
        ui.output_ui("highlight_common_regions"),
        full_screen=True
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("🔍 사용자 선택 기준에 따른 건물 데이터 시각화"),
            ui.layout_columns(
            ui.input_slider("year_range", "사용승인년도(From ~ To)", min=1950, max=2025, value=(1980, 2000)),
            ui.input_slider("score_range", "위험 점수(From ~ To)", min=90, max=400, value=(300, 350))),
            ui.output_ui("show_filtered_building_map"),
            full_screen=True
        )
    ),
    ui.card(
        ui.card_header("📈 조건 변화에 따른 점수 변화 시뮬레이션"),
        full_screen=True
    )
        ),
        
        
        
        ui.nav_panel("부록",
            # 🔹 변수 정의 + 데이터 설명
            ui.layout_columns(
                ui.card(
                    ui.card_header("📊 변수 정의"),
                    ui.output_data_frame("show_variable_table")
                ),
                ui.card(
                    ui.card_header("📂 데이터 설명"),
                    ui.output_data_frame("show_data_table")
                )
            ),

            # 🔹 점수 기준표 + 가중치 기준표
            ui.layout_columns(
                ui.card(
                    ui.card_header("📐 점수 산출 기준표"),
                    ui.output_data_frame("show_score_table"),
                    full_screen=True
                ),
                ui.card(
                    ui.card_header("📐 가중치 산출 기준표"),
                    ui.output_data_frame("show_weight_table"),
                    full_screen=True
                )
            ),

            # 🔹 사용자 정의 가중치 지도
            ui.card(
                ui.card_header("⚙️ 사용자 정의 가중치 기반 위험도 지도"),

                ui.layout_columns(
                    ui.input_slider("w0", "① 건물연차 점수", min=0, max=25, value=1),
                    ui.input_slider("w1", "② 지상층수", min=0, max=25, value=1),
                    ui.input_slider("w2", "③ 지하층수", min=0, max=25, value=1),
                    ui.input_slider("w3", "④ 비상용 승강기", min=0, max=25, value=1),
                ),
                ui.layout_columns(
                    ui.input_slider("w4", "⑤ 주용도", min=0, max=25, value=1),
                    ui.input_slider("w5", "⑥ 구조 재료", min=0, max=25, value=1),
                    ui.input_slider("w6", "⑦ 소화전 거리", min=0, max=25, value=1),
                    ui.input_slider("w7", "⑧ 소방관서 거리", min=0, max=25, value=1),
                ),
                
                ui.layout_columns(
                    ui.input_slider("year_filter", "건축연도 (From ~ To)", min=1950, max=2025, value=(1980, 2020)),
                    ui.input_slider("score_filter", "위험 점수 (From ~ To)", min=0, max=500, value=(100, 350)),
                    ui.input_checkbox_group("structure_group", "구조 그룹 선택", choices=df["구조그룹"].dropna().unique().tolist(), selected=df["구조그룹"].dropna().unique().tolist()),
                    ui.download_button("download_csv", "📥 CSV 다운로드"),
                ),
                ui.output_ui("show_score_map2"),
                    full_screen=True
                ),
                    ),
        title="🧯 영천시 화재 취약건물 분석"
    )





























# 서버 로직 틀 정의 (예시 placeholder)
def server(input, output, session):
    @output
    @render.ui
    def show_building_age_bar():
        CURRENT_YEAR = 2025
        df['사용승인일(년도)'] = df['사용승인일(년도)'].astype('Int64')
        df['건물나이'] = CURRENT_YEAR - df['사용승인일(년도)']

        def classify_age(age):
            if age >= 40:
                return '40년 이상'
            elif age >= 30:
                return '30년 이상 40년 미만'
            elif age >= 20:
                return '20년 이상 30년 미만'
            elif age >= 10:
                return '10년 이상 20년 미만'
            else:
                return '10년 미만'

        df['노후도 구간'] = df['건물나이'].apply(classify_age)

        age_group_counts = df['노후도 구간'].value_counts().reindex([
            '40년 이상',
            '30년 이상 40년 미만',
            '20년 이상 30년 미만',
            '10년 이상 20년 미만',
            '10년 미만'
        ])

        age_df = age_group_counts.reset_index()
        age_df.columns = ['노후도 구간', '건물 수']

        fig = px.bar(
            age_df,
            x='노후도 구간',
            y='건물 수',
            title='건물 노후도 구간별 분포 (2025년 기준)',
            color='건물 수',
            color_continuous_scale='darkmint',
            template='plotly_white'
        )
        fig.update_layout(xaxis_title='노후도 구간', yaxis_title='건물 수')

        return ui.HTML(fig.to_html())
    
    
    @output
    @render.ui
    
    def show_structure_pie():
        # 🔹 구조 그룹별 건물 수 집계
        group_counts = df['구조그룹'].value_counts().reset_index()
        group_counts.columns = ['구조그룹', '건물수']

        # 🔹 파이차트 생성
        fig = px.pie(
            group_counts,
            names='구조그룹',
            values='건물수',
            title='구조 그룹별 건물 분포',
            hole=0.4
        )
        fig.update_traces(textinfo='percent+label')
        fig.update_layout(title_font_size=20)

        return ui.HTML(fig.to_html())
    
    
    @output
    @render.ui
    def show_usage_pie():
        def classify_usage(name):
            if pd.isna(name):
                return '기타'
            if any(x in name for x in ['단독주택', '공동주택']):
                return '주거시설'
            elif any(x in name for x in ['공장', '창고', '자원순환', '위험물', '분뇨', '쓰레기']):
                return '공장/창고시설'
            elif any(x in name for x in ['근린생활', '판매', '소매점', '일반업무']):
                return '상업/판매시설'
            elif any(x in name for x in ['숙박', '위락', '수련', '관광', '야영']):
                return '숙박/다중이용시설'
            elif any(x in name for x in ['노유자', '교육', '의료', '복지']):
                return '교육/복지시설'
            elif any(x in name for x in ['종교', '사찰', '교회', '문화', '운동']):
                return '종교/문화시설'
            elif any(x in name for x in ['업무', '공공용', '동사무소', '방송통신', '발전']):
                return '행정/공공/업무시설'
            elif any(x in name for x in ['교정', '군사', '국방', '운수', '장례', '묘지']):
                return '교정/군사/운수/기타'
            else:
                return '기타'

        df['주용도_그룹'] = df['주용도코드명'].apply(classify_usage)

        group_counts = df['주용도_그룹'].value_counts().reset_index()
        group_counts.columns = ['주용도_그룹', '건물수']

        fig = px.pie(
            group_counts,
            names='주용도_그룹',
            values='건물수',
            title='주용도별 건물 분포',
            hole=0.4
        )
        fig.update_traces(textinfo='percent+label')
        fig.update_layout(title_font_size=20)

        return ui.HTML(fig.to_html())

    @output
    @render.ui
    def show_elevator_pie():
        df_filtered = df[(df["지상층수"] >= 5) | (df["지하층수"] >= 5)]
        elevator_counts = df_filtered["비상용승강기수"].value_counts().sort_index()
        elevator_df = pd.DataFrame({
            "비상용승강기수": elevator_counts.index.astype(str),
            "건물수": elevator_counts.values
        })

        fig = px.pie(
            elevator_df,
            names="비상용승강기수",
            values="건물수",
            title="비상용 승강기 수 분포",
            hole=0.4
        )
        fig.update_traces(textinfo='percent+label')
        fig.update_layout(title_font_size=20)

        return ui.HTML(fig.to_html())
    
    @output
    @render.ui
    def show_station_distance_plot():
        encoded_img = create_distance_hist_image()
        return ui.HTML(f'<img src="data:image/png;base64,{encoded_img}" style="width:100%;">')

    @output
    @render.ui
    def show_hydrant_station_map():
        return ui.HTML(create_hydrant_station_map())

    @output
    @render.ui
    def show_firehydrant_distance_plot():
        encoded_img = create_firehydrant_distance_plot()
        return ui.HTML(f'<img src="data:image/png;base64,{encoded_img}" style="width:90%;">')

    @output
    @render.data_frame
    def show_station_table():
        display_df = stations_filtered[["소속", "안전센터", "지역대"]]
        return render.DataGrid(display_df, filters=False, width="100%", height="300px")

    
    @reactive.calc
    def filtered_df():
        selected = input.region()
        return df_population[df_population["읍면동"].isin(selected)]

    @reactive.calc
    def filtered_building_df():
        selected = input.region()
        if "전체선택" in selected:
            return df[df["읍면동"].isin(region_list)]
        else:
            return df[df["읍면동"].isin(selected)]


    @output
    @render.data_frame
    def show_summary():
        def summarize_buildings(df_subset, label):
            most_common_year = df_subset['사용승인일(년도)'].mode().iloc[0] if not df_subset['사용승인일(년도)'].mode().empty else None
            most_common_purpose = df_subset['주용도코드명'].mode().iloc[0] if not df_subset['주용도코드명'].mode().empty else None
            most_common_material = df_subset['구조코드명'].mode().iloc[0] if not df_subset['구조코드명'].mode().empty else None
            most_common_region = df_subset['읍면동'].mode().iloc[0] if not df_subset['읍면동'].mode().empty else None
            avg_height = round(df_subset[df_subset['높이(m)'] > 0]['높이(m)'].mean(), 2)
            avg_hydrant_dist = round(df_subset['소화전거리'].mean(), 2)
            avg_firestation_dist = round(df_subset['소방서거리'].mean(), 2)
            avg_total_score = round(df_subset['total_score'].mean(), 2)

            return [
                label,
                most_common_year,
                most_common_purpose,
                most_common_material,
                most_common_region,
                avg_height,
                avg_hydrant_dist,
                avg_firestation_dist,
                avg_total_score
            ]

        filtered = filtered_building_df()
        if filtered.empty:
            return pd.DataFrame(columns=[
                "구분", "최빈 사용 승인 연도", "최빈 주용도", "최빈 건물 구조", "최다 출현 읍면동",
                "건물 높이 평균", "소화전 거리 평균", "소방관서 거리 평균", "위험 점수 평균"
            ])

        top_10 = filtered[filtered["total_score"] >= filtered["total_score"].quantile(0.9)]
        bottom_10 = filtered[filtered["total_score"] <= filtered["total_score"].quantile(0.1)]

        summary_data = [
            summarize_buildings(top_10, "상위 10%"),
            summarize_buildings(bottom_10, "하위 10%")
        ]

        columns = [
            "구분", "최빈 사용 승인 연도", "최빈 주용도", "최빈 건물 구조", "최다 출현 읍면동",
            "건물 높이 평균", "소화전 거리 평균", "소방관서 거리 평균", "위험 점수 평균"
        ]

        summary_df = pd.DataFrame(summary_data, columns=columns)
        return render.DataGrid(summary_df, width="100%", height="130px", filters=False)

    @output
    @render.ui
    def show_score_map():
        selected = input.region()
        gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")

        df_score = df[df["읍면동"].isin(selected)].copy()
        df_score_grouped = df_score.groupby("읍면동")["total_score"].mean().reset_index()
        df_score_grouped = df_score_grouped.rename(columns={"읍면동": "EMD_KOR_NM", "total_score": "평균위험도"})

        gdf = gdf.merge(df_score_grouped, on="EMD_KOR_NM", how="left")
        gdf["평균위험도"] = gdf["평균위험도"].fillna(0)
        gdf = gdf[gdf["EMD_KOR_NM"].isin(selected)].copy()
        
        min_score = gdf["평균위험도"].min()
        max_score = gdf["평균위험도"].max()
        step = (max_score - min_score) / 5 if max_score != min_score else 1

        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=11)

        def get_score_color(score):
            if score >= min_score + step * 4: return "#d73027"
            elif score >= min_score + step * 3: return "#fc8d59"
            elif score >= min_score + step * 2: return "#fee08b"
            elif score >= min_score + step * 1: return "#d9ef8b"
            else: return "#91cf60"

        folium.GeoJson(
            gdf,
            name="위험도 시각화",
            style_function=lambda feature: {
                "fillColor": get_score_color(feature["properties"].get("평균위험도", 0)),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["EMD_KOR_NM", "평균위험도"],
                aliases=["읍면동", "평균 취약 점수"],
                localize=True
            )
        ).add_to(m)

        return ui.HTML(m._repr_html_())

    @output
    @render.ui
    def show_population_map():
        selected = input.region()
        gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")
        df_pop = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/ycdaycon/영천인구.csv")
        df_pop = df_pop.rename(columns={"읍면동": "EMD_KOR_NM"})
        df_pop = df_pop[df_pop["EMD_KOR_NM"] != "합계"]
        df_pop["총인구수"] = df_pop["총인구수"].astype(str).str.replace(",", "").astype(float)
        df_pop["고령인구"] = df_pop["고령인구"].astype(str).str.replace(",", "").astype(float)
        df_pop["고령인구비율(%)"] = (df_pop["고령인구"] / df_pop["총인구수"] * 100).round(2)

        gdf = gdf.merge(df_pop, on="EMD_KOR_NM", how="left")
        gdf = gdf[gdf["EMD_KOR_NM"].isin(selected)]

        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=10)

        folium.GeoJson(
            gdf,
            name="고령인구 비율 시각화",
            style_function=lambda feature: {
                'fillColor': '#%02x%02x%02x' % (
                    255,
                    255 - int(feature['properties'].get('고령인구비율(%)', 0) / max(gdf["고령인구비율(%)"].max(), 1) * 255),
                    150
                ),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["EMD_KOR_NM", "총인구수", "고령인구", "고령인구비율(%)"],
                aliases=["읍면동", "총 인구수", "고령 인구수", "고령 인구 비율(%)"],
                localize=True
            )
        ).add_to(m)

        return ui.HTML(m._repr_html_())

    @output
    @render.data_frame
    def population_table():
        df_show = filtered_df().copy()
        df_show["고령인구비율"] = (df_show["고령인구비율"]).round(2).astype(str) + " %"
        return df_show[["읍면동", "총인구수", "고령인구", "고령인구비율"]]

    @output
    @render.ui
    def show_filtered_building_map():
        # GeoJSON 로딩 (초기 1회)
        gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")
        gdf = gdf.to_crs(epsg=4326)
    
        # 사용자 선택 불러오기
        year_min, year_max = input.year_range()
        score_min, score_max = input.score_range()
    
        # 조건에 따라 필터링
        df_filtered = df[
            (df["사용승인일(년도)"].between(year_min, year_max)) &
            (df["total_score"].between(score_min, score_max))
        ]
        total_count = len(df)
        filtered_count = len(df_filtered)
    
        # 읍면동 필터링
        emds = df_filtered["읍면동"].unique()
        gdf_filtered = gdf[gdf["EMD_KOR_NM"].isin(emds)].copy()
        gdf_filtered = gdf_filtered[gdf_filtered.geometry.notnull()]
    
        if gdf_filtered.empty or df_filtered.empty:
            return ui.HTML(f"<b>조건을 만족하는 건물이 없습니다. (0 / {total_count})</b>")
    
        # 지도 중심 좌표 계산
        try:
            center = gdf_filtered.geometry.unary_union.centroid
            center_coords = [center.y, center.x]
        except Exception:
            center_coords = [36.01, 128.9426]  # 기본값
    
        m = folium.Map(location=center_coords, zoom_start=11)
    
        # GeoJSON 시각화
        folium.GeoJson(
            gdf_filtered,
            name="조건 만족 읍면동",
            style_function=lambda feature: {
                "fillColor": "#3186cc",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.4,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["EMD_KOR_NM"],
                aliases=["읍면동"],
                localize=True
            )
        ).add_to(m)
    
        # 건물 점 표시
        for _, row in df_filtered.iterrows():
            if pd.notna(row["위도"]) and pd.notna(row["경도"]):
                folium.CircleMarker(
                    location=(row["위도"], row["경도"]),
                    radius=4,
                    fill=True,
                    fill_color="red",
                    color=None,
                    fill_opacity=0.7,
                    popup=f"{row['읍면동']} | 위험도: {row['total_score']}"
                ).add_to(m)
    
        return ui.TagList(
            ui.markdown(f"🔍 전체 **{total_count:,}건 중 {filtered_count:,}건**이 조건을 만족합니다."),
            ui.HTML(m._repr_html_())
        )
        
    
    
    
    
    
    # 🔹 데이터프레임 렌더링
    @output
    @render.data_frame
    def show_variable_table():
        df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/variable.csv", encoding="euc-kr")
        return df

    @output
    @render.data_frame
    def show_data_table():
        df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/data.csv")
        return df

    @output
    @render.data_frame
    def show_score_table():
        df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/score.csv", encoding="euc-kr")
        return df

    @output
    @render.data_frame
    def show_weight_table():
        df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/weight.csv")
        return df

    
    # 🔹 사용자 정의 가중치 기반 지도
    @output
    @render.ui
    def show_score_map2():
        # 📌 region 입력이 없을 경우 전체 사용
        try:
            selected = input.region()
        except Exception:
            selected = df["읍면동"].unique().tolist()

        # ✅ 가중치 가져오기
        w = [input.w0(), input.w1(), input.w2(), input.w3(),
             input.w4(), input.w5(), input.w6(), input.w7()]

        # ✅ GeoJSON 불러오기
        gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")

        # ✅ 필터링된 건물 데이터
        df_score = df[df["읍면동"].isin(selected)].copy()

        if df_score.empty:
            return ui.HTML("<b>해당 조건에 일치하는 건물 데이터가 없습니다.</b>")

        # ✅ 가중치 점수 계산
        df_score["weighted_score"] = (
            df_score["건물연차점수"] * w[0] +
            df_score["지상층수_점수"] * w[1] +
            df_score["지하층수_점수"] * w[2] +
            df_score["비상용승강기_점수"] * w[3] +
            df_score["주용도_점수"] * w[4] +
            df_score["구조코드_점수"] * w[5] +
            df_score["소화전거리_점수"] * w[6] +
            df_score["소방관서거리_점수"] * w[7]
        )

        grouped = df_score.groupby("읍면동")["weighted_score"].mean().reset_index()
        grouped = grouped.rename(columns={"읍면동": "EMD_KOR_NM", "weighted_score": "평균위험도"})

        gdf = gdf.merge(grouped, on="EMD_KOR_NM", how="left")
        gdf["평균위험도"] = gdf["평균위험도"].fillna(0)

        # ✅ 지도 시각화
        min_score = gdf["평균위험도"].min()
        max_score = gdf["평균위험도"].max()
        step = (max_score - min_score) / 5 if max_score != min_score else 1

        def get_score_color(score):
            if score >= min_score + step * 4: return "#d73027"
            elif score >= min_score + step * 3: return "#fc8d59"
            elif score >= min_score + step * 2: return "#fee08b"
            elif score >= min_score + step * 1: return "#d9ef8b"
            else: return "#91cf60"

        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=11)

        folium.GeoJson(
            gdf,
            name="위험도 시각화",
            style_function=lambda feature: {
                "fillColor": get_score_color(feature["properties"].get("평균위험도", 0)),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["EMD_KOR_NM", "평균위험도"],
                aliases=["읍면동", "평균 위험 점수"],
                localize=True
            )
        ).add_to(m)

        return ui.HTML(m._repr_html_())
    @reactive.calc
    def filtered_csv_data():
        year_min, year_max = input.year_filter()
        score_min, score_max = input.score_filter()
        selected_structures = input.structure_filter()

        df_filtered = df[
            (df["사용승인일(년도)"].between(year_min, year_max)) &
            (df["total_score"].between(score_min, score_max)) &
            (df["구조그룹"].isin(selected_structures))
        ][["대지위치", "위도", "경도", "total_score"]].copy()

        return df_filtered
    
    @output
    @render.download(filename="filtered_buildings.csv")
    def download_csv():
        def generator():
            df_filtered = df[
                (df["사용승인일(년도)"].between(input.year_range()[0], input.year_range()[1])) &
                (df["total_score"].between(input.score_range()[0], input.score_range()[1])) &
                (df["구조그룹"].isin(input.structure_group()))
            ]

            selected_cols = ["대지위치", "위도", "경도", "total_score"]
            df_selected = df_filtered[selected_cols].copy()

            yield df_selected.to_csv(index=False, encoding="utf-8-sig")

        return generator()  # ← 여기 반드시 () 붙여서 실행 결과 반환!!!
    
    def summarize_buildings(df_subset, label):
        most_common_year = df_subset['사용승인일(년도)'].mode().iloc[0] if not df_subset['사용승인일(년도)'].mode().empty else None
        most_common_purpose = df_subset['주용도코드명'].mode().iloc[0] if not df_subset['주용도코드명'].mode().empty else None
        most_common_material = df_subset['구조코드명'].mode().iloc[0] if not df_subset['구조코드명'].mode().empty else None
        avg_height = round(df_subset[df_subset['높이(m)'] > 0]['높이(m)'].mean(), 2)
        avg_hydrant_dist = round(df_subset['소화전거리'].mean(), 2)
        avg_firestation_dist = round(df_subset['소방서거리'].mean(), 2)
        avg_total_score = round(df_subset['total_score'].mean(), 2)

        return [
            label,
            most_common_year,
            most_common_purpose,
            most_common_material,
            avg_height,
            avg_hydrant_dist,
            avg_firestation_dist,
            avg_total_score
        ]

    @reactive.calc
    def summary_df2():
        filtered = filtered_building_df()  # ← 선택된 읍면동만 사용
        dong_list = filtered['읍면동'].dropna().unique()

        summary_data = [
            summarize_buildings(filtered[filtered['읍면동'] == dong], dong)
            for dong in dong_list
        ]

        columns = [
            "구분", "최빈 사용 승인 연도", "최빈 주용도", "최빈 건물 구조",
            "건물 높이 평균", "소화전 거리 평균", "소방관서 거리 평균", "위험 점수 평균"
        ]
        return pd.DataFrame(summary_data, columns=columns)

    @output
    @render.data_frame
    def show_summary2():
        return render.DataGrid(summary_df2(), width="100%", height="500px", filters=False)


    @output
    @render.ui
    def highlight_common_regions():
        import geopandas as gpd
        import pandas as pd
        import folium

        # ✅ GeoJSON 전체 불러오기
        gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson").to_crs(epsg=4326)

        # ✅ 공통 지역 리스트 가져오기
        common_regions = common_df["읍면동"].unique().tolist()

        # ✅ 위험 점수 평균 계산
        df_score = df[df["읍면동"].isin(common_regions)].copy()
        df_score_grouped = df_score.groupby("읍면동")["total_score"].mean().reset_index()
        df_score_grouped = df_score_grouped.rename(columns={"읍면동": "EMD_KOR_NM", "total_score": "평균위험도"})

        # ✅ GeoJSON과 병합
        gdf = gdf.merge(df_score_grouped, on="EMD_KOR_NM", how="left")

        # ✅ 고령인구 비율 병합
        df_old_filtered = df_population[df_population["읍면동"].isin(common_regions)][["읍면동", "고령인구비율"]]
        df_old_filtered = df_old_filtered.rename(columns={"읍면동": "EMD_KOR_NM"})
        gdf = gdf.merge(df_old_filtered, on="EMD_KOR_NM", how="left")

        # ✅ 지도 중심 계산
        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=11)

        # ✅ GeoJSON 시각화
        folium.GeoJson(
            gdf,
            name="전체 읍면동",
            style_function=lambda feature: {
                "fillColor": "#ff4c4c" if feature["properties"]["EMD_KOR_NM"] in common_regions else "#cccccc",
                "color": "black" if feature["properties"]["EMD_KOR_NM"] in common_regions else "gray",
                "weight": 2 if feature["properties"]["EMD_KOR_NM"] in common_regions else 1,
                "fillOpacity": 0.7,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["EMD_KOR_NM", "평균위험도", "고령인구비율"],
                aliases=["읍면동", "평균 위험도", "고령 인구 비율(%)"],
                localize=True,
                sticky=False,
                labels=True,
                toLocaleString=True,
                style="background-color: white;"
            )
        ).add_to(m)

        return ui.TagList(
            ui.markdown("📌 겹치는 지역 2곳만 **빨간색**으로 강조한 전체 지도입니다."),
            ui.HTML(m._repr_html_())
        )

app = App(app_ui, server)


