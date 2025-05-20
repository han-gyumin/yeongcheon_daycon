import seaborn as sns
from faicons import icon_svg
import plotly.express as px
# Import data from shared.py
from shared import app_dir, df_population, df,create_distance_hist_image, create_firehydrant_distance_plot,create_building_map,create_hydrant_station_map, stations_filtered
import pandas as pd
from shiny import reactive
from shiny.express import input, render, ui
from shiny.ui import page_navbar, nav_panel
# import folium
# from shared import app_dir, df
# import pandas as pd
import folium
# import seaborn as sns
# import plotly.express as px
# from faicons import icon_svg
from functools import partial

from shiny.express import ui
from shiny.ui import page_navbar
import geopandas as gpd
from pathlib import Path

# from shiny import reactive
# from shiny.express import input, render, ui

ui.page_opts(title="🧯영천 화재 취약건물 분석", fillable=True, page_fn=partial(page_navbar, id="page"))

with ui.nav_panel("프로젝트 개요"):
    ui.card_header("📢 최근 영천시 화재 기사 캡처")
    with ui.layout_columns():
        for src in ["/text1.png", "/text2.png", "/text3.png"]:
            ui.div(
                ui.img(src=src, style="width:100%; height:auto;"),
                style="padding: 5px; display: flex; align-items: center; justify-content: center; min-height: 120px;"
            )
    with ui.card(full_screen=True):
        ui.card_header("🔥 화재 현장 사진")
        with ui.layout_columns():
            ui.div(
                ui.img(src="../img1.png", style="width:100%"),
                style="padding: 5px;"
            )
            ui.div(
                ui.img(src="../img2.png", style="width:100%"),
                style="padding: 5px;"
            )
    # 🔹 1. 상단 프로젝트 목표
    with ui.card(full_screen=True):
        ui.markdown("""
            ### ✅ **프로젝트 목적**

            #### - 영천시의 건축물대장 데이터를 기반으로 화재에 취약한 건물의 분포를 분석  
            #### - 건축 구조, 층수, 접근성 등을 반영한 **행정동 단위의 화재 취약 점수**를 산출
            #### - 소방서·소화전·대피소 등의 **재난 대응 인프라 우선 설치 지역**을 도출하고 **인터랙티브 지도 시각화**로 행정 활용을 지원
            """)
    with ui.card(full_screen=True):
        ui.markdown("""
            ### ✅ **프로젝트 기대효과**

            #### - **데이터 기반의 화재 취약 지역 파악**으로 인한 재난 대응 효율성 향상
            #### - 고령 인구 밀집 지역 등 **사회적 약자 보호 강화**
            #### - 소방 인프라 미흡 지역의 선제적 대응 가능
            #### - 영천시 외 타 지자체에서도 활용 가능한 **분석·시각화 템플릿 모델 제시**
            """)

    # 🔹 2. 중간 2분할 카드 (변수 정의 + 데이터 설명)
    

    
with ui.nav_panel(title="시각화"):
    with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("건물 노후도 구간별 분포 (2025년 기준)")

                @reactive.calc
                def building_age_bar():
                    import pandas as pd
                    import plotly.express as px

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
                    return fig.to_html()

                @render.ui
                def show_building_age_bar():
                    return ui.HTML(building_age_bar())
                
                
            with ui.card(full_screen=True):
                ui.card_header("구조별 건물 분포")
                @reactive.calc
                def structure_pie_html():
                    # 구조 그룹별 건물 수 집계
                    group_counts = df['구조그룹'].value_counts().reset_index()
                    group_counts.columns = ['구조그룹', '건물수']

                    # 파이차트 생성
                    fig = px.pie(
                        group_counts,
                        names='구조그룹',
                        values='건물수',
                        title='구조 그룹별 건물 분포',
                        hole=0.4
                    )
                    fig.update_traces(textinfo='percent+label')
                    fig.update_layout(title_font_size=20)

                    return fig.to_html()

                @render.ui
                def show_structure_pie():
                    return ui.HTML(structure_pie_html())
    with ui.layout_columns(col_widths=[6, 6]):
        with ui.card(full_screen=True):
            ui.card_header("주용도별 건물 분포")

            @reactive.calc
            def usage_pie_html():
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

                return fig.to_html()

            @render.ui
            def show_usage_pie():
                return ui.HTML(usage_pie_html())
            
        with ui.card(full_screen=True):
            ui.card_header("비상용 승강기 수 분포 (5층 이상 건물)")

            @reactive.calc
            def elevator_pie_html():
                # 5층 이상 조건 필터링
                df_filtered = df[(df["지상층수"] >= 5) | (df["지하층수"] >= 5)]

                # 비상용승강기 수 분포 계산
                elevator_counts = df_filtered["비상용승강기수"].value_counts().sort_index()
                elevator_df = pd.DataFrame({
                    "비상용승강기수": elevator_counts.index.astype(str),
                    "건물수": elevator_counts.values
                })

                # Plotly 파이차트 생성
                fig = px.pie(
                    elevator_df,
                    names="비상용승강기수",
                    values="건물수",
                    title="비상용 승강기 수 분포",
                    hole=0.4
                )
                fig.update_traces(textinfo='percent+label')
                fig.update_layout(title_font_size=20)

                return fig.to_html()

            @render.ui
            def show_elevator_pie():
                return ui.HTML(elevator_pie_html())

    with ui.layout_columns(col_widths=[6, 6]):
        with ui.card():
            ui.card_header("소방서 거리 분포 시각화")

            @render.ui
            def show_station_distance_plot():
                encoded_img = create_distance_hist_image()
                return ui.HTML(f'<img src="data:image/png;base64,{encoded_img}" style="width:100%;">')
        

        # 🔹 오른쪽 열: 전체 지도
        with ui.card(height="100%"):
            ui.card_header("🧯 소화전 및 소방서 위치 + 읍면동 경계 지도")

            @render.ui
            def show_hydrant_station_map():
                return ui.HTML(create_hydrant_station_map())
                    
            
        # with ui.layout_columns():
        with ui.card():
            ui.card_header("🧯 소화전 거리 분포")
            @render.ui
            def show_firehydrant_distance_plot():
                encoded_img = create_firehydrant_distance_plot()
                return ui.HTML(f'<img src="data:image/png;base64,{encoded_img}" style="width:90%; ">')
        with ui.card():
            ui.card_header("📋 영천시 소방관서 정보")
            @render.data_frame
            def show_station_table():
            # 소속 및 고유한 안전센터 값만 추출
                display_df = stations_filtered[["소속", "안전센터","지역대"]]
                return render.DataGrid(display_df, filters=False, width="100%", height="300px")
with ui.nav_panel(title="위험스코어"):
# df = pd.read_csv("./영천인구.csv", encoding="utf-8")
    # 🔹 3. 하단 점수 산정식 카드
    
    with ui.layout_sidebar():
        with ui.sidebar(title="Filter controls"):
            region_list = df_population["읍면동"].unique().tolist()
            # ui.input_slider("pop", "인구 수", 0, 10000, 5000)
            ui.input_checkbox_group("region", "읍면동 선택", choices=region_list[:], selected=region_list[:])

        @reactive.calc
        def filtered_df():
            selected = input.region()
            if "전체선택" in selected:
                return df_population[df_population["읍면동"].isin(region_list)]
            else:
                return df_population[df_population["읍면동"].isin(selected)]

        # with ui.layout_column_wrap(fill=False):
        #     with ui.value_box(showcase=icon_svg("users")):
        #         "선택된 지역 총 인구수"
        #         @render.text
        #         def total_population():
        #             return f"{filtered_df()['총인구수'].sum():,.0f} 명"

        #     with ui.value_box(showcase=icon_svg("user-group")):
        #         "선택된 지역 평균 인구수"
        #         @render.text
        #         def avg_population():
        #             return f"{filtered_df()['총인구수'].mean():,.1f} 명"
                
        with ui.card(full_screen=True):
            ui.card_header("📊 평균 위험 점수 상·하위 건물 특성 비교")
            def summarize_buildings(df_subset, label):
                most_common_year = df_subset['사용승인일(년도)'].mode().iloc[0]
                most_common_purpose = df_subset['주용도코드명'].mode().iloc[0]
                most_common_material = df_subset['구조코드명'].mode().iloc[0]
                avg_height = round(df_subset[df_subset['높이(m)'] > 0]['높이(m)'].mean(), 2)
                avg_hydrant_dist = round(df_subset['소화전거리'].mean(), 2)
                avg_firestation_dist = round(df_subset['소방서거리'].mean(), 2)
                avg_building_score = round(df_subset['건물연차점수'].mean(), 2)
                avg_upstair_score = round(df_subset['지상층수_점수'].mean(), 2)
                avg_downstair_score = round(df_subset['지하층수_점수'].mean(), 2)
                avg_elevator_score = round(df_subset['비상용승강기_점수'].mean(), 2)
                avg_hydrant_score = round(df_subset['소화전거리_점수'].mean(), 2)
                avg_firestation_score = round(df_subset['소방관서거리_점수'].mean(), 2)
        
                return [
                    label,
                    most_common_year,
                    most_common_purpose,
                    most_common_material,
                    avg_height,
                    avg_hydrant_dist,
                    avg_firestation_dist,
                    avg_building_score,
                    avg_upstair_score,
                    avg_downstair_score,
                    avg_elevator_score,
                    avg_hydrant_score,
                    avg_firestation_score,
                ]
        
            # 기준 분할
            top_10 = df[df["total_score"] >= df["total_score"].quantile(0.9)]
            bottom_10 = df[df["total_score"] <= df["total_score"].quantile(0.1)]
        
            # 표 생성
            summary_data = [
                summarize_buildings(top_10, "상위 10%"),
                summarize_buildings(bottom_10, "하위 10%"),
            ]
        
            columns = [
                "구분", "최빈 사용 승인 연도", "최빈 주용도", "최빈 건물 구조",
                "건물 높이 평균", "소화전 거리 평균", "소방관서 거리 평균",
                "건물연차_점수", "지상층수_점수", "지하층수_점수",
                "비상용승강기_점수", "소화전거리_점수", "소방관서거리_점수"
            ]
        
            summary_df = pd.DataFrame(summary_data, columns=columns)
        
            @render.data_frame
            def show_summary():
                return render.DataGrid(summary_df, filters=False)
                    
                    
        with ui.card(full_screen=True):
            ui.card_header("📊 평균 위험 점수 상·하위 지역 특성 비교")
        with ui.card(full_screen=True):
            ui.card_header("읍면동별 평균 점수 시각화")
            @reactive.calc
            def score_map_html():
                selected = input.region()
                # ✅ 1. GeoJSON 불러오기
                gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")


                # ✅ 2. df에서 읍면동별 평균 total_score 집계


                df_score = df[df["읍면동"].isin(selected)].copy()
                df_score_grouped = df_score.groupby("읍면동")["total_score"].mean().reset_index()
                # ✅ 3. 컬럼 이름 맞추고 병합
                df_score_grouped = df_score_grouped.rename(columns={"읍면동": "EMD_KOR_NM", "total_score": "평균위험도"})

                gdf = gdf.merge(df_score_grouped, on="EMD_KOR_NM", how="left")
                gdf["평균위험도"] = gdf["평균위험도"].fillna(0)

                # ✅ 동적으로 색상 구간 계산
                min_score = gdf["평균위험도"].min()
                max_score = gdf["평균위험도"].max()
                step = (max_score - min_score) / 5 if max_score != min_score else 1  # 분모 0 방지
                # ✅ 4. 지도 생성
                center = gdf.geometry.unary_union.centroid
                m = folium.Map(location=[center.y, center.x], zoom_start=11)
                # ✅ 5. 위험도 색상 매핑 함수 정의
                def get_score_color(score):
                    if score >= min_score + step * 4:
                        return "#d73027"  # 빨강
                    elif score >= min_score + step * 3:
                        return "#fc8d59"  # 주황
                    elif score >= min_score + step * 2:
                        return "#fee08b"  # 노랑
                    elif score >= min_score + step * 1:
                        return "#d9ef8b"  # 연두
                    else:
                        return "#91cf60"  # 초록
                # ✅ 6. GeoJson 추가
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
                    ),
                ).add_to(m)
                return m._repr_html_()
            @render.ui
            def show_score_map():
                return ui.HTML(score_map_html())

            with ui.layout_columns():
                with ui.card(full_screen=True):
                    ui.card_header("영천시 고령인구 비율 시각화")

                    @reactive.calc
                    def population_map_html():
                        selected = input.region()

                        # ✅ GeoJSON 불러오기
                        gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")

                        # ✅ 인구수 CSV 불러오기 및 전처리
                        df_pop = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/ycdaycon/영천인구.csv")
                        df_pop = df_pop.rename(columns={"읍면동": "EMD_KOR_NM"})
                        df_pop = df_pop[df_pop["EMD_KOR_NM"] != "합계"].copy()

                        # 총인구, 고령인구 전처리
                        df_pop["총인구수"] = df_pop["총인구수"].astype(str).str.replace(",", "").str.strip().astype(float)
                        df_pop["고령인구"] = df_pop["고령인구"].astype(str).str.replace(",", "").str.strip().astype(float)

                        # 고령인구 비율 계산
                        df_pop["고령인구비율(%)"] = (df_pop["고령인구"] / df_pop["총인구수"] * 100).round(2)

                        # ✅ GeoJSON 병합
                        gdf = gdf.merge(
                        df_pop[["EMD_KOR_NM", "총인구수", "고령인구", "고령인구비율(%)"]],
                            on="EMD_KOR_NM", how="left"
                            )
                        gdf[["총인구수", "고령인구", "고령인구비율(%)"]] = gdf[["총인구수", "고령인구", "고령인구비율(%)"]].fillna(0)

                        # ✅ 선택 지역 필터링
                        gdf_filtered = gdf[gdf["EMD_KOR_NM"].isin(selected)].copy()

                        center = gdf_filtered.geometry.unary_union.centroid
                        m = folium.Map(location=[center.y, center.x], zoom_start=10)

                        # ✅ 지도 시각화
                        folium.GeoJson(
                            gdf_filtered,
                            name="고령인구 비율 시각화",
                            style_function=lambda feature: {
                                'fillColor': '#%02x%02x%02x' % (
                                    255,
                                    255 - int(feature['properties'].get('고령인구비율(%)', 0) / max(gdf_filtered["고령인구비율(%)"].max(), 1) * 255),
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

                        return m._repr_html_()

                    @render.ui
                    def show_population_map():
                        return ui.HTML(population_map_html())


                with ui.card(full_screen=True):
                    ui.card_header("읍면동별 인구 및 고령 인구 현황")

                    @render.data_frame
                    def population_table():
                        # 표시할 컬럼을 명시적으로 지정 (고령인구 및 비율 포함)
                        cols = [
                            "읍면동",
                            "총인구수",
                            "고령인구",
                            "고령인구비율"
                        ]
                        # 고령인구비율은 퍼센트 형식으로 포맷팅해서 보여주고 싶다면 다음 코드도 가능
                        df_show = filtered_df()[cols].copy()
                        df_show["고령인구비율"] = (df_show["고령인구비율"]).round(2).astype(str) + " %"

                        return render.DataGrid(df_show, filters=False)
with ui.nav_panel(title="결론"):
    with ui.card(full_screen=True):
        ui.card_header("🔍 데이터 기반 분석을 통한 화재 취약 지역 식별 및 시사점 도출")

    
    with ui.layout_columns():
        with ui.card(full_screen=True):
            gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")
            gdf = gdf.to_crs(epsg=4326)
            ui.card_header("🔍 사용자 선택 기준에 따른 건물 데이터 시각화")
            with ui.layout_columns():
                ui.input_slider("year_range", "사용승인년도(From ~ To)", min=1950, max=2025, value=(1980,2000))
                ui.input_slider("score_range", "위험 점수(From ~ To)", min=90, max=400, value=(300, 350))
        
            
        
            @render.ui
            def show_filtered_building_map():
                # ✅ 사용자 선택 범위 불러오기
                year_min, year_max = input.year_range()
                score_min, score_max = input.score_range()

                # ✅ 범위 조건에 따라 필터링
                df_filtered = df[
                    (df["사용승인일(년도)"].between(year_min, year_max)) &
                    (df["total_score"].between(score_min, score_max))
                ]
                total_count = len(df)
                filtered_count = len(df_filtered)

                # 읍면동 필터링
                emds = df_filtered["읍면동"].unique()
                gdf_filtered = gdf[gdf["EMD_KOR_NM"].isin(emds)]
                gdf_filtered = gdf_filtered[gdf_filtered.geometry.notnull()]

                if gdf_filtered.empty or df_filtered.empty:
                    return ui.HTML(f"<b>조건을 만족하는 건물이 없습니다. (0 / {total_count})</b>")

                # 지도 중심 계산
                try:
                    center = gdf_filtered.geometry.unary_union.centroid
                    center_coords = [center.y, center.x]
                except Exception:
                    center_coords = [36.01, 128.9426]

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

                # 지도 + 설명 텍스트 반환
                return ui.TagList(
                    ui.markdown(f"🔍 전체 **{total_count:,}건 중 {filtered_count:,}건**이 조건을 만족합니다."),
                    ui.HTML(m._repr_html_())
                )
    with ui.card(full_screen=True):
        ui.card_header("📈 조건 변화에 따른 점수 변화 시뮬레이션")


with ui.nav_panel("부록"):
    with ui.layout_columns():
        with ui.card():
            ui.card_header("📊 변수 정의")
            variable_df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/variable.csv",encoding="euc-kr")
            score_df=variable_df.iloc[:,1:]
            @render.data_frame
            def show_variable_table():
                return render.DataGrid(variable_df, filters=False, width="100%")
        with ui.card():
            ui.card_header("📂 데이터 설명")
            data_df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/data.csv")
            score_df=data_df.iloc[:,1:]
            @render.data_frame
            def show_data_table():
                return render.DataGrid(data_df, filters=False, width="100%")
    with ui.layout_columns():
        with ui.card(full_screen=True):
                ui.card_header("📐 점수 산출 기준표")
                score_df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/score.csv",encoding="euc-kr")
                score_df=score_df.iloc[:,1:]
                @render.data_frame
                def show_score_table():
                    return render.DataGrid(score_df, filters=False, width="100%")
        with ui.card(full_screen=True):
                ui.card_header("📐 가중치 산출 기준표")
                weight_df = pd.read_csv("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/weight.csv")
                @render.data_frame
                def show_weight_table():
                    return render.DataGrid(weight_df, filters=False, width="100%")
    with ui.card(full_screen=True):
        ui.card_header("⚙️ 사용자 정의 가중치 기반 위험도 지도")

        # 🔹 8개 변수에 대한 가중치 입력 UI
        with ui.layout_columns():
            ui.input_slider("w0", "① 건물연차 점수 가중치", min=0, max=25, value=1)
            ui.input_slider("w1", "② 지상층수 가중치", min=0, max=25, value=1)
            ui.input_slider("w2", "③ 지하층수 가중치", min=0, max=25, value=1)
            ui.input_slider("w3", "④ 비상용 승강기 가중치", min=0, max=25, value=1)
            ui.input_slider("w4", "⑤ 주용도 가중치", min=0, max=25, value=1)
            ui.input_slider("w5", "⑥ 구조 재료 가중치", min=0, max=25, value=1)
            ui.input_slider("w6", "⑦ 소화전 거리 가중치", min=0, max=25, value=1)
            ui.input_slider("w7", "⑧ 소방관서 거리 가중치", min=0, max=25, value=1)

        @reactive.calc
        def weighted_score_map_html():
            selected = input.region()

            # ✅ 입력받은 가중치 값
            w0 = input.w0()
            w1 = input.w1()
            w2 = input.w2()
            w3 = input.w3()
            w4 = input.w4()
            w5 = input.w5()
            w6 = input.w6()
            w7 = input.w7()

            # ✅ GeoJSON 로딩
            gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")

            # ✅ df 필터링
            df_score = df[df["읍면동"].isin(selected)].copy()

            # ✅ 사용자 가중치 기반 점수 계산
            df_score["weighted_score"] = (
                df_score["건물연차점수"] * w0 +
                df_score["지상층수_점수"] * w1 +
                df_score["지하층수_점수"] * w2 +
                df_score["비상용승강기_점수"] * w3 +
                df_score["주용도_점수"] * w4 +
                df_score["구조코드_점수"] * w5 +
                df_score["소화전거리_점수"] * w6 +
                df_score["소방관서거리_점수"] * w7
            )

            # ✅ 읍면동별 평균 점수
            grouped = df_score.groupby("읍면동")["weighted_score"].mean().reset_index()
            grouped = grouped.rename(columns={"읍면동": "EMD_KOR_NM", "weighted_score": "평균위험도"})

            gdf = gdf.merge(grouped, on="EMD_KOR_NM", how="left")
            gdf["평균위험도"] = gdf["평균위험도"].fillna(0)

            # ✅ 지도 시각화
            center = gdf.geometry.unary_union.centroid
            m = folium.Map(location=[center.y, center.x], zoom_start=11)

            def make_score_color_func(min_score, max_score):
                # 등분 구간 계산
                step = (max_score - min_score) / 5

                def get_score_color2(score):
                    if score >= min_score + step * 4:
                        return "#d73027"  # 빨강
                    elif score >= min_score + step * 3:
                        return "#fc8d59"  # 주황
                    elif score >= min_score + step * 2:
                        return "#fee08b"  # 노랑
                    elif score >= min_score + step * 1:
                        return "#d9ef8b"  # 연두
                    else:
                        return "#91cf60"  # 초록

                return get_score_color2
            # 점수 최대/최소값 계산
            min_score = gdf["평균위험도"].min()
            max_score = gdf["평균위험도"].max()
            
            # 색상 매핑 함수 생성
            get_score_color2 = make_score_color_func(min_score, max_score)
            folium.GeoJson(
                gdf,
                name="위험도 시각화",
                style_function=lambda feature: {
                "fillColor": get_score_color2(feature["properties"].get("평균위험도", 0)),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["EMD_KOR_NM", "평균위험도"],
                    aliases=["읍면동", "평균 위험 점수"],
                    localize=True
                ),
            ).add_to(m)

            return m._repr_html_()

        @render.ui
        def show_score_map2():
            return ui.HTML(weighted_score_map_html())
        
    ui.include_css(app_dir / "styles.css")