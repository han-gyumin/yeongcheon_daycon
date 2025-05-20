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

        with ui.layout_column_wrap(fill=False):
            with ui.value_box(showcase=icon_svg("users")):
                "선택된 지역 총 인구수"
                @render.text
                def total_population():
                    return f"{filtered_df()['총인구수'].sum():,.0f} 명"

            with ui.value_box(showcase=icon_svg("user-group")):
                "선택된 지역 평균 인구수"
                @render.text
                def avg_population():
                    return f"{filtered_df()['총인구수'].mean():,.1f} 명"






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
    
        
    # with ui.card(full_screen=True):
    #     ui.card_header("건물 위치 지도 (위도/경도 기반)")

    #     @render.ui
    #     def show_building_map():
    #         return ui.HTML(create_building_map())
        
    
    
    with ui.layout_columns():
        with ui.card(full_screen=True):
            ui.card_header("영천시 지역별 주요 구조 재료 시각화")

            # ✅ GeoJSON 불러오기
            gdf = gpd.read_file("C:/Users/USER/Desktop/yeongcheon_daycon/ycdatacon/old.geojson")

            # ✅ df에서 읍면동별로 가장 많은 구조코드명 추출
            df_major_structure = (
                df.groupby(["읍면동", "구조그룹"])
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
                .drop_duplicates("읍면동")  # 읍면동별 가장 많은 구조코드명만 남김
            )

            # ✅ GeoDataFrame과 병합
            gdf_struct = gdf.merge(df_major_structure, left_on="EMD_KOR_NM", right_on="읍면동", how="left")

            # ✅ 구조 재료별 색상 매핑
            structure_colors = {
                "목조 계열": "#A0522D",       # 🪵 진한 갈색 → 나무 색 그대로
                "조적식 구조": "#B22222",     # 🧱 벽돌색 (파이어브릭 레드)
                "콘크리트 계열": "#A9A9A9",   # 🪨 콘크리트 회색
                "철골 계열": "#4682B4",       # 🔩 스틸 블루 (철골 느낌)
                "조립식·판넬·기타": "#D3D3D3",# 🧩 연회색 → 가벼운 패널·임시 건물 느낌
                }       
            # 구조 코드명
#   
            def get_color(name):
                return structure_colors.get(name, "#AAAAAA")

            @reactive.calc
            def structure_map_html():
                selected = input.region()
                gdf_filtered = gdf_struct[gdf_struct["EMD_KOR_NM"].isin(selected)]

                center = gdf_filtered.geometry.unary_union.centroid
                m = folium.Map(location=[center.y, center.x], zoom_start=11)

                # ✅ GeoJson에 색상 입히기
                folium.GeoJson(
                    gdf_filtered,
                    name="구조 재료 시각화",
                    style_function=lambda feature: {
                        "fillColor": get_color(feature["properties"].get("구조그룹", "미분류")),
                        "color": "black",
                        "weight": 1,
                        "fillOpacity": 0.6,
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["EMD_KOR_NM", "구조그룹"],
                        aliases=["읍면동", "주요 구조재"],
                        localize=True
                    ),  
                ).add_to(m)

                return m._repr_html_()

            @render.ui
            def show_structure_map():
                return ui.HTML(structure_map_html())
        with ui.card(full_screen=True):
            ui.card_header("위험도 기반 건물 시각화")

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

                # ✅ 4. 지도 생성
                center = gdf.geometry.unary_union.centroid
                m = folium.Map(location=[center.y, center.x], zoom_start=11)

                # ✅ 5. 위험도 색상 매핑 함수 정의
                def get_score_color(score):
                    if score >= 23.5:
                        return "#d73027"  # 빨강
                    elif score >= 23:
                        return "#fc8d59"  # 주황
                    elif score >= 22.5:
                        return "#fee08b"  # 노랑
                    elif score >= 22:
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
                        aliases=["읍면동", "평균 위험 점수"],
                        localize=True
                    ),
                ).add_to(m)

                return m._repr_html_()

            @render.ui
            def show_score_map():
                return ui.HTML(score_map_html())
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