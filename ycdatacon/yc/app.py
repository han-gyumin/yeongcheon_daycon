from shiny import App, ui, render, reactive, req
import pandas as pd
import geopandas as gpd
from shinyswatch import theme
import folium
import plotly.express as px
import os
import matplotlib.ticker as ticker
from shared import df_population, df,font_prop,create_distance_hist_image, common_df,df_fake,create_firehydrant_distance_plot,create_building_map,create_hydrant_station_map, stations_filtered,top5_old,top5_score
import plotly.graph_objs as go
STATIC_DIR = os.path.join(os.path.dirname(__file__), "www")
region_list = df_population["읍면동"].unique().tolist()

# UI 구성
def app_ui(request):
    return ui.page_fluid(
        ui.tags.head(
        ui.tags.style(
            """
            .scroll-box {
                max-height: 600px;
                overflow-y: auto;
                border: 1px solid #ccc;
                padding: 10px;
            }
            table {
                font-size: 14px;
                line-height: 1.6;
                table-layout: fixed;
                width: 100%;
            }
            th {
                white-space: nowrap !important;
                text-align: center;
                background-color: #f8f9fa;
            }
            td {
                vertical-align: top;
                white-space: normal !important;
                padding: 8px;
            }
            td:nth-child(1) {
                width: 10%;
                text-align: left;
            }
            td:nth-child(2) {
                width: 10%;
                text-align: center;
            }
            td:nth-child(3) {
                width: 80%;
                text-align: left;
            }
            """
),

            ui.tags.link(
                href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/dist/journal/bootstrap.min.css",
                rel="stylesheet"
            )
        ), 
        ui.page_navbar(
            ui.nav_panel("HOME",
                ui.card(
                    ui.card_header("사용자 가중치 설정"),
                    ui.layout_columns(
                        ui.input_slider("w0", "① 건물연차 점수", min=0, max=25, value=25),
                        ui.input_slider("w1", "② 지상층수", min=0, max=25, value=9),
                        ui.input_slider("w2", "③ 지하층수", min=0, max=25, value=11),
                        ui.input_slider("w3", "④ 비상용 승강기", min=0, max=25, value=5),
                    ),
                    ui.layout_columns(
                        ui.input_slider("w4", "⑤ 주용도", min=0, max=25, value=20),
                        ui.input_slider("w5", "⑥ 건축 자재", min=0, max=25, value=15),
                        ui.input_slider("w6", "⑦ 소화전 거리", min=0, max=25, value=5),
                        ui.input_slider("w7", "⑧ 소방관서 거리", min=0, max=25, value=10),
                    ),
                    ui.layout_columns(
                        ui.input_checkbox_group("structure_group", "건축 자재 선택", choices=df["구조그룹"].dropna().unique().tolist(), selected=df["구조그룹"].dropna().unique().tolist()),
                        ui.input_slider("year_filter", "건축연도 (From ~ To)", min=1950, max=2025, value=(1980, 2020)),
                        ui.input_slider("score_filter", "취약 점수 (From ~ To)", min=0, max=500, value=(100, 350)),
                        ui.download_button("download_csv", "CSV 다운로드",style="background-color: #ec766e; color: white;"),
                    ),
                    ui.card(
                        ui.card_header("사용자 설정 기반 취약 점수 지도 및 건물 목록"),
                        ui.output_ui("show_score_map2"),
                        full_screen=True
                    )
                ),
            ),
            ui.nav_panel("건물 취약도 분석",
                ui.tags.head(
                    ui.tags.style("""
                        .nav-link {
                           background-color: #f05d4e !important;
                           color: white !important;
                           font-weight: bold;
                           border-radius: 4px;
                           margin: 2px;
                        }

                        .nav-link.active {
                            background-color: #d94d40 !important;
                            color: #fff !important;
                        }
                    """)
                ),
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_checkbox_group("region", "행정동 선택", choices=region_list, selected=["금호읍","청통면","신녕면","화산면","화북면","화남면","자양면","임고면","고경면","북안면","대창면","동부동","중앙동","서부동","완산동","남부동"]),
                        ui.input_action_button("apply_filter", "적용",style="background-color: #ec766e; color: white;"),
                        title="필터 설정"
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("사용자 설정에 따른 건물 분포 시각화"),
                            ui.layout_columns(
                                ui.input_slider("year_range", "건축연도(From ~ To)", min=1950, max=2025, value=(1980, 2000)),
                                ui.input_slider("score_range", "취약 점수(From ~ To)", min=90, max=400, value=(220, 260))
                            ),
                            ui.output_ui("show_filtered_building_map"),
                            full_screen=True
                        ),
                        ui.card(
                            ui.card_header("전체 건물 취약 점수 분포"),
                            ui.output_plot("top_bottom_histogram"),
                            ui.output_data_frame("show_summary"),
                            full_screen=True
                        )
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("행정동별 평균 취약 점수 및 건물 특성 비교"),
                            ui.output_data_frame("show_summary2"),
                            full_screen=True
                        )
                            
                    ),
                )
            ),
            ui.nav_panel("행정동 취약도 분석",
                ui.layout_columns(
                    ui.card(
                        ui.card_header("행정동별 평균 취약 점수 시각화"),
                        ui.output_ui("show_score_map"),
                        full_screen=True
                    ),
                    ui.card(
                            ui.output_ui("show_top_score_boxes")
                    ),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("영천시 고령인구 비율 시각화"),
                        ui.output_ui("show_population_map"),
                        full_screen=True
                    ),
                    ui.card(
                            ui.output_ui("show_top_old_boxes")
                    ),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("화재 취약 점수와 고령 인구 비율이 모두 높은 지역"),
                        ui.output_ui("highlight_common_regions"),
                        full_screen=False,
                        width=6
                    ),
                    ui.card(
                        ui.output_plot("line_total_score_by_dong")
                    ),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("취약 지역 내 소방서 설치 시뮬레이션 결과"),
                        ui.output_ui("show_score_map3"),
                        full_screen=True,
                    ), 
                    ui.card(
                        ui.card_header("취약 지역 내 소방서 설치 전후 변화"),
                        ui.output_ui("show_score_comparison_boxes")
                    ),   
                ),
        ),
            ui.nav_panel("부록1(시각화)",
                ui.layout_columns(
                    ui.card(
                        ui.card_header("건물 노후도 구간별 분포 (2025년 기준)"),
                        ui.output_ui("show_building_age_bar"),
                        full_screen=True
                        ),

                    ui.card(
                        ui.card_header("건축 자재별 건물 분포"),
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
                    ui.card(
                        ui.card_header("소화전 거리 분포"),
                        ui.output_ui("show_firehydrant_distance_plot")
                    ),
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("소화전 및 소방서 위치 + 읍면동 경계 지도"),
                        ui.output_ui("show_hydrant_station_map"),
                        height="100%"
                    ),
                    ui.card(
                        ui.card_header("영천시 소방관서 정보"),
                        ui.output_data_frame("show_station_table")
                    )
                )
            ),
            ui.nav_panel("부록2(기준 및 설명)",
                ui.layout_columns(
                    ui.card(
                        ui.card_header("변수 정의"),
                        ui.output_ui("show_data_table")
                    ),
                    ui.card(
                        ui.card_header("데이터 설명"),
                        ui.output_ui("show_variable_table")
                    )
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("점수 산출 기준표"),
                        ui.output_ui("show_score_table"),
                        full_screen=True
                    ),
                    ui.card(
                        ui.card_header("가중치 산출 기준표"),
                        ui.output_ui("show_weight_table"),
                        full_screen=True
                    )
                ),
            ),
        
        title=ui.tags.a("🔥 영천시 화재 취약건물 분석", href="/yc_project/", style="text-decoration:none; color:inherit;"),
        theme = theme.journal
                
        )
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
            title='건축 자재별 건물 분포',
            hole=0.4
        )

        # 🔹 숨기고 싶은 레이블 정의
        hidden_labels = ["조립식·판넬·기타", "기타 / 특수 구조"]

        # 🔹 텍스트 조건부 표시
        fig.update_traces(
        texttemplate=[
            f"{label}" if label not in hidden_labels else ""
            for label, percent in zip(
                group_counts["구조그룹"],
                group_counts["건물수"] / group_counts["건물수"].sum() * 100
            )
        ],
        textposition="inside",
        insidetextorientation="horizontal",
        hovertemplate="<b>구조그룹=%{label}</b><br>건물수=%{value:,}<br>비율=%{percent:.1%}<extra></extra>"
        )


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
        group_counts['비율'] = group_counts['건물수'] / group_counts['건물수'].sum()

        # 숨길 항목
        hidden_labels = ["교육/복지시설", "종교/문화시설", "숙박/다중이용시설", "교정/군사/운수/기타", "행정/공공/업무시설"]

        # 텍스트 설정 (비율 없이)
        group_counts['label'] = group_counts.apply(
            lambda row: "" if row['주용도_그룹'] in hidden_labels else f"{row['주용도_그룹']}",
            axis=1
        )

        fig = px.pie(
            group_counts,
            names='주용도_그룹',
            values='건물수',
            title='주용도별 건물 분포',
            hole=0.4
        )

        fig.update_traces(
            text=group_counts['label'],
            textinfo='text',
            textposition='inside',
            insidetextorientation="horizontal",
            hovertemplate="<b>주용도=%{label}</b><br>건물수=%{value:,}<br>비율=%{percent:.1%}<extra></extra>"
        )

        fig.update_layout(title_font_size=20)

        return ui.HTML(fig.to_html())


    @output
    @render.ui
    def show_elevator_pie():
        df_filtered = df[(df["지상층수"] >= 5) | (df["지하층수"] >= 5)]
        ordered_labels = ["0", "1", "2", "3", "4", "5"]

        # value_counts 후 누락된 값 채우기
        all_counts = pd.Series(index=ordered_labels, dtype=int)
        actual_counts = df_filtered["비상용승강기수"].astype(str).value_counts()
        all_counts.update(actual_counts)
        all_counts = all_counts.fillna(0).astype(int)

        elevator_df = pd.DataFrame({
            "비상용승강기수": all_counts.index,
            "건물수": all_counts.values
        })

        # 내부 텍스트: 4, 5 제외하고 "n대"로 표시 (비율 제거)
        elevator_df['label'] = elevator_df.apply(
            lambda row: f"{row['비상용승강기수']}대" if row['비상용승강기수'] not in ['4', '5'] else "",
            axis=1
        )

        fig = px.pie(
            elevator_df,
            names="비상용승강기수",
            values="건물수",
            title="비상용 승강기 수 분포",
            hole=0.4,
            category_orders={"비상용승강기수": ordered_labels}
        )

        fig.update_traces(
            text=elevator_df['label'],
            textinfo="text",
            textposition="inside",
            insidetextorientation="horizontal",
            hovertemplate="<b>승강기 수=%{label}대</b><br>건물수=%{value:,}<br>비율=%{percent:.1%}<extra></extra>"
        )

        fig.update_layout(
            title_font_size=20,
            legend_traceorder="normal"
        )

        return ui.HTML(fig.to_html())
    
    @output
    @render.ui
    def show_station_distance_plot():
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=df["소방서거리"],
            nbinsx=50,
            marker=dict(color='salmon', line=dict(color='black', width=1)),
            name="소방서 거리"
        ))

        fig.update_layout(
            title="소방서 거리 분포",
            xaxis_title="거리 (m)",
            yaxis_title="건물 수",
            template="simple_white",
            margin=dict(l=40, r=20, t=50, b=40),
            font=dict(family="Arial", size=14)
        )

        # Plotly Figure를 HTML로 변환
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return ui.HTML(plot_html)

    @output
    @render.ui
    def show_hydrant_station_map():
        return ui.HTML(create_hydrant_station_map())

    @output
    @render.ui
    def show_firehydrant_distance_plot():
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=df["소화전거리"],
            nbinsx=50,
            marker=dict(color='skyblue', line=dict(color='black', width=1)),
            name="소화전 거리"
        ))

        fig.update_layout(
            title="소화전 거리 분포",
            xaxis_title="소화전 거리 (m)",
            yaxis_title="건물 수",
            template="simple_white",
            margin=dict(l=40, r=20, t=50, b=40),
            font=dict(family="Arial", size=14)
        )

        # HTML로 변환 후 반환
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        return ui.HTML(plot_html)

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
        selected = filtered_region()
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
            avg_hydrant_dist = f"{round(df_subset['소화전거리'].mean(), 2):,}"
            avg_firestation_dist = f"{round(df_subset['소방서거리'].mean(), 2):,}"
            avg_total_score = round(df_subset['total_score'].mean(), 2)

            return [
                label,
                most_common_year,
                most_common_purpose,
                most_common_material,
                most_common_region,
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
            "구분", "최빈 사용 승인 연도", "최빈 주용도", "최빈 건물 구조", "최다 출현 읍면동", "소화전 거리 평균", "소방관서 거리 평균", "위험 점수 평균"
        ]

        summary_df = pd.DataFrame(summary_data, columns=columns)
        return render.DataGrid(summary_df, width="100%", height="200px", filters=False)
    import branca.colormap as cm
    @output
    @render.ui
    def show_score_map():
        selected = input.region()
        gdf = gpd.read_file("old.geojson")

        df_score = df[df["읍면동"].isin(selected)].copy()
        df_score_grouped = df_score.groupby("읍면동")["total_score"].mean().reset_index()
        df_score_grouped = df_score_grouped.rename(columns={"읍면동": "EMD_KOR_NM", "total_score": "평균위험도"})

        gdf = gdf.merge(df_score_grouped, on="EMD_KOR_NM", how="left")
        gdf["평균위험도"] = gdf["평균위험도"].fillna(0)
        gdf = gdf[gdf["EMD_KOR_NM"].isin(selected)].copy()

        min_score = gdf["평균위험도"].min()
        max_score = gdf["평균위험도"].max()
        step = (max_score - min_score) / 5 if max_score != min_score else 1

        # ✅ 동일한 색상 및 등급 구간 적용
        thresholds = [min_score + step * i for i in range(6)]  # 5등급 → 6경계값
        colors = ["#91cf60", "#d9ef8b", "#fee08b", "#fc8d59", "#d73027"]

        colormap = cm.StepColormap(
            colors=colors,
            index=thresholds,
            vmin=min_score,
            vmax=max_score,
            caption="평균 취약 점수"
        )

        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=10)

        folium.GeoJson(
            gdf,
            name="위험도 시각화",
            style_function=lambda feature: {
                "fillColor": colormap(feature["properties"].get("평균위험도", 0)),
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

        colormap.add_to(m)

        return ui.HTML(m._repr_html_())

    import branca.colormap as cm

    @output
    @render.ui
    def show_population_map():
        selected = input.region()
        gdf = gpd.read_file("old.geojson")
        df_pop = pd.read_csv("yc_pop.csv")
        df_pop = df_pop.rename(columns={"읍면동": "EMD_KOR_NM"})
        df_pop = df_pop[df_pop["EMD_KOR_NM"] != "합계"]
        df_pop["총인구수"] = df_pop["총인구수"].astype(str).str.replace(",", "").astype(float)
        df_pop["고령인구"] = df_pop["고령인구"].astype(str).str.replace(",", "").astype(float)
        df_pop["고령인구비율(%)"] = (df_pop["고령인구"] / df_pop["총인구수"] * 100).round(2)

        gdf = gdf.merge(df_pop, on="EMD_KOR_NM", how="left")
        gdf = gdf[gdf["EMD_KOR_NM"].isin(selected)]

        min_ratio = gdf["고령인구비율(%)"].min()
        max_ratio = gdf["고령인구비율(%)"].max()

        # ✅ 연속형 색상바 정의 (보라 계열)
        colormap = cm.linear.Purples_09.scale(min_ratio, max_ratio)
        # colormap.caption = "고령인구 비율 (%)"

        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=10)

        folium.GeoJson(
            gdf,
            name="고령인구 비율 시각화",
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties'].get('고령인구비율(%)', 0)),
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

        # ✅ 색상바 추가
        colormap.add_to(m)

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
        gdf = gpd.read_file("old.geojson")
        gdf = gdf.to_crs(epsg=4326)
    
        # 사용자 선택 불러오기
        year_min, year_max = input.year_range()
        score_min, score_max = input.score_range()
        selected_emds = filtered_region()
    
        # 조건에 따라 필터링
        df_filtered = df[
            (df["사용승인일(년도)"].between(year_min, year_max)) &
            (df["total_score"].between(score_min, score_max)) &
            (df["읍면동"].isin(selected_emds))
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
    
        m = folium.Map(location=center_coords, zoom_start=10)
    
        # GeoJSON 시각화
        folium.GeoJson(
            gdf_filtered,
            name="조건 만족 읍면동",
            style_function=lambda feature: {
                "fillColor": "#c2c2c1",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
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
                    fill_color="#ec766e",
                    color=None,
                    fill_opacity=0.3,
                    popup=f"{row['읍면동']} | 위험도: {row['total_score']}"
                ).add_to(m)
    
        return ui.TagList(
            ui.markdown(f"🔍 전체 **{total_count:,}건 중 {filtered_count:,}건**이 조건을 만족합니다."),
            ui.HTML(m._repr_html_())
        )
            
    common_style = """
    <style>
        .scroll-box {
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
        }
        table {
            font-size: 14px;
            line-height: 1.6;
            table-layout: fixed;
            width: 100%;
        }
        th {
            white-space: nowrap !important;
            text-align: center;
            background-color: #f8f9fa;
        }
        td {
            vertical-align: top;
            white-space: normal !important;
            padding: 8px;
        }
        td:nth-child(1) {
            width: 10%;
            text-align: left;
        }
        td:nth-child(2) {
            width: 10%;
            text-align: center;
        }
        td:nth-child(3) {
            width: 80%;
            text-align: left;
        }
    </style>
    """


    
    
    
        # 🔹 데이터프레임 렌더링
    @output
    @render.ui
    def show_data_table():
        import pandas as pd
        from shiny import ui

        df = pd.DataFrame({
            "변수명": [
                "사용승인일(년도)", "지상층수", "지하층수", "주용도코드명", "구조코드명",
                "비상용승강기수", "소화전 거리", "소방관서 거리"
            ],
            "설명": [
                "건물의 사용 승인 연도(건물 노후도를 알아보기 위함)",
                "건물의 지상 층 수",
                "건물의 지하 층 수",
                "건물의 주요 기능 및 사용 목적 구분",
                "건물의 주요 구조체 재료",
                "화재 시 대피에 사용할 수 있는 승강기 수",
                "건물과 가장 가까운 소화전까지의 거리",
                "최근접 소방관서(소방서, 119센터 등) 거리"
            ],
            "예시값": [
                "1984", "5층", "지하 2층", "공장, 숙박시설", "목조, 철근콘크리트",
                "1대", "100m", "4km"
            ],
            "비고": [
                "오래될수록 전기/소방 설비 노후 및 내화재 미비 가능성 ↑",
                "층수가 높을수록 대피 시간 증가",
                "연기 흡입 및 대피 지연 위험 ↑",
                "용도별로 화재 확산/발생 위험 통계 기반",
                "목조건물은 내화성 낮고 구조적 위험 ↑",
                "대피 수단 부족 시 위험도 ↑",
                "70m 이상부터는 소방 호스 연결 제한 가능성 ↑",
                "도착 지연 시 초기 대응 실패율 ↑"
            ]
        })

        html = df.to_html(
            escape=False,
            index=False,
            classes="table table-striped table-bordered",
            border=0
        )

        style = """
        <style>
            .scroll-box {
                max-height: 500px;
                overflow-y: auto;
                border: 1px solid #ccc;
                padding: 10px;
            }
            table { font-size: 14px; line-height: 1.6; }
            td, th { vertical-align: top; text-align: left; white-space: normal !important; }
        </style>
        """

        return ui.HTML(style + f'<div class="scroll-box">{html}</div>')


    @output
    @render.ui
    def show_variable_table():
        from shiny import ui
        import pandas as pd

        try:
            df = pd.DataFrame({
                "공공데이터명": [
                    "경상북도_소방관서 및 구급차량 현황",
                    "경상북도_소화전 통합관리 운영현황",
                    "2025 1분기 주민등록인구통계",
                    "건축물대장(표제부)"
                ],
                "출처": [
                    "공공데이터포털",
                    "공공데이터포털",
                    "영천시청",
                    "건축HUB"
                ],
                "국가중점": [
                    "⭕", "⭕", "⭕", "⭕"
                ]
            })

            html = df.to_html(
                escape=False,
                index=False,
                classes="table table-striped table-bordered",
                border=0
            )

            style = """
            <style>
                .scroll-box {
                    max-height: 400px;
                    overflow-y: auto;
                    border: 1px solid #ccc;
                    padding: 10px;
                }
                table { font-size: 14px; line-height: 1.6; }
                td, th { vertical-align: middle; text-align: center; white-space: normal !important; }
            </style>
            """

            return ui.HTML(style + f'<div class="scroll-box">{html}</div>')

        except Exception as e:
            return ui.div(f"⚠️ 오류 발생: {str(e)}", class_="text-danger")


    
    @output
    @render.ui
    def show_score_table():
        import pandas as pd
        from shiny import ui

        df = pd.DataFrame({
            "항목": [
                "건물 노후도", "지상층수", "지하층수", "주요 용도", "구조 재질", 
                "비상용 승강기 수", "소화전 거리", "소방관서 거리"
            ],
            "기준 / 조건": [
                "40년 이상: +5.0<br>30년~40년: +4.0<br> 20년~30년: +3.0<br> 10년~20년: +2.0<br> 10년 이하: +1.0",
                "1층: +0.0<br>2층: +1.0<br>3층: +2.0<br>4층: +3.0",
                "B1층: +1.0<br>B2층: +2.0<br>B3층: +3.0",
                "숙박/다중이용시설: +9.0<br>공장/창고시설: +8.0<br>교육/복지시설: +7.0<br>상업/판매시설: +5.0<br>문화/업무시설: +5.0<br>교정/군사/운수/기타: +4.0<br>기타: +3.0<br> 주거시설: +2.0<br>행정/공공/업무시설: +1.0",
                "목조 계열: +5.0<br> 조적식 구조: +4.0<br>조립식/판넬/기타: +3.0<br>철골 계열: +2.0<br>기타/특수 구조: +1.0<br>콘크리트 계열: +0.0",
                "0대: +5.0<br>1대: +4.0<br>2대: +3.0<br>3대: +2.0<br>4대: +1.0<br>5대: +0.0",
                "≤30m: +1.0<br>≤60m: +2.0<br>≤90m: +3.0<br>≤120m: +4.0<br>≤150m: +5.0",
                "<1km: +1.0<br><3km: +2.0<br><5km: +3.0<br><7km: +4.0<br><9km: +5.0"
            ],
            "설명": [
                "•  전기/소방 설비 노후, 내화재 미비 가능성<br>•  구조 변경 복잡 → 대피 경로 복잡<br>•  오래된 설비로 인한 화재 위험 증가",
                "•  고층일수록 연기 확산 빠름<br>•  구조대 접근 어려움, 계단 이용 제약",
                "•  지하는 연기·열기 배출 어려움<br>•  구조대 접근 제한 및 대피 통로 부족",
                "•  숙박/공장 등은 인원 밀집 또는 가연성 자재로 대형 화재 위험<br>•  용도에 따라 대피 능력, 감지/진압 인프라 차이",
                "•  목조·조적식은 화재 확산 빠름<br>•  콘크리트·철골 계열은 내화성 높음<br>•  구조 재질은 붕괴 시간과도 관련",
                "•  고층 건물 대피 시간 단축에 필수<br>•  승강기 미설치 시 구조 어려움",
                "•  소화전은 초기 화재 진압에 중요<br>•  멀수록 진압 실패 가능성 증가",
                "•  도착 시간은 골든타임과 직결<br>•  지연 시 인명·재산 피해 증가"
            ]
        })

        html = df.to_html(escape=False, index=False, classes="table table-striped table-bordered", border=0)
        return ui.HTML(common_style + f'<div class="scroll-box">{html}</div>')


    common_style2 = """
    <style>
        .scroll-box {
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
        }
        table {
            font-size: 14px;
            line-height: 1.6;
            table-layout: fixed;
            width: 100%;
        }
        th {
            white-space: nowrap !important;
            text-align: center;
            background-color: #f8f9fa;
        }
        td {
            vertical-align: top;
            white-space: normal !important;
            padding: 8px;
        }
        td:nth-child(1) {
            width: 15%;
            text-align: left;
        }
        td:nth-child(2) {
            width: 10%;
            text-align: center;
        }
        td:nth-child(3) {
            width: 75%;
            text-align: left;
        }
    </style>
    """



    @output
    @render.ui
    def show_weight_table():
        import pandas as pd
        from shiny import ui

        df = pd.DataFrame({
            "항목": [
                "건물 노후도", "지상층수", "지하층수", "주요 용도", "구조 재질",
                "비상용 승강기 수", "소화전 거리", "소방관서 거리"
            ],
            "점수": [25, 9, 11, 20, 15, 5, 5, 10],
            "설명": [
                "• 전기배선, 가스관, 소방시설의 노후화로<br> 화재 발생 가능성과 피해 규모 증가<br>"
                "• 내화재 미비, 스프링클러 미설치로<br> 초기 진압 어려움",
                "• 연기 상승, 구조 난이도, 소방차 진입 제약<br>• 고층일수록 대피 및 진압 난이도 증가",
                "• 환기 부족, 출입구 제약, 비상탈출 어려움<br>• 지하 화재 시 질식 위험과 사망률 증가",
                "• 용도에 따라 화재 발생률과 피해 규모 상이<br>• 병원·노유자시설 등은 대피 지연 위험 큼",
                "• 목조·경량 철골조는 연소 빠르고 확산 쉬움<br>• 철근콘크리트는 내화 성능 우수<br>• 구조는 화재 확산 및 대피 시간에 영향",
                "• 고층 건물 대피 시 유용하나<br>• 구조 지연의 주요 원인은 계단에 있음",
                "• 소화전이 멀면 초기 진화 지연 발생<br>• 일반인 접근 제한도 대응에 장애",
                "• 소방 도착 시간은 화재 확대에 큰 영향<br>• 도착 지연 시 피해 규모 급증"
            ]
        })

        html = df.to_html(escape=False, index=False, classes="table table-striped table-bordered", border=0)
        return ui.HTML(f'<div class="scroll-box">{html}</div>')



    @output
    @render.data_frame
    def show_weighted_table():
    
        w = [input.w0(), input.w1(), input.w2(), input.w3(),
             input.w4(), input.w5(), input.w6(), input.w7()]
        year_min, year_max = input.year_filter()
        score_min, score_max = input.score_filter()
        structure_selected = input.structure_group()
    
        df_score = df[
            (df["사용승인일(년도)"].between(year_min, year_max)) &
            (df["total_score"].between(score_min, score_max)) &
            (df["구조그룹"].isin(structure_selected))
        ].copy()
    
        if df_score.empty:
            return pd.DataFrame(columns=["행정동", "주소", "기존점수", "사용자가중점수"])
    
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
    
        df_table = df_score[["읍면동", "대지위치", "total_score", "weighted_score"]].copy()
        df_table = df_table.rename(columns={
            "읍면동": "행정동",
            "대지위치": "주소",
            "total_score": "기존 점수",
            "weighted_score": "사용자 점수"
        })
    
        return render.DataGrid(df_table, width="100%", height="600px", filters=False)
    
    # 🔹 사용자 정의 가중치 기반 지도
    @output
    @render.ui
    def show_score_map2():
        selected = ['동부동', '중앙동', '서부동', '남부동', '완산동',
                    '금호읍', '청통면', '신녕면', '화산면', '화북면',
                    '화남면', '자양면', '임고면', '고경면', '북안면', '대창면']

        w = [input.w0(), input.w1(), input.w2(), input.w3(),
            input.w4(), input.w5(), input.w6(), input.w7()]

        gdf = gpd.read_file("old.geojson")
        
        year_min, year_max = input.year_filter()
        score_min, score_max = input.score_filter()
        structure_selected = input.structure_group()

        df_score = df[
            (df["읍면동"].isin(selected)) &
            (df["사용승인일(년도)"].between(year_min, year_max)) &
            (df["total_score"].between(score_min, score_max)) &
            (df["구조그룹"].isin(structure_selected))
        ].copy()

        total_count = len(df)
        filtered_count = len(df_score)

        if df_score.empty:
            return ui.HTML("<b>해당 조건에 일치하는 건물 데이터가 없습니다.</b>")

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

        # ✅ 색상바 추가
        import branca.colormap as cm
        colormap = cm.StepColormap(
            colors=["#91cf60", "#d9ef8b", "#fee08b", "#fc8d59", "#d73027"],
            vmin=min_score, vmax=max_score,
            index=[min_score + step * i for i in range(6)],
            caption="평균 위험 점수"
        )
        colormap.add_to(m)

        df_table = df_score[["읍면동", "대지위치", "total_score", "weighted_score"]].copy()
        df_table = df_table.rename(columns={
            "읍면동": "행정동",
            "대지위치": "주소",
            "total_score": "기존점수",
            "weighted_score": "사용자가중점수"
        })

        return ui.TagList(
            ui.markdown(f"전체 **{total_count:,}건 중 {filtered_count:,}건**이 조건을 만족합니다."),
            ui.layout_columns(
                ui.card(
                    ui.HTML(m._repr_html_()),
                    full_screen=True
                ),
                ui.card(
                    ui.output_data_frame("show_weighted_table")
                ),
                col_widths=[7, 5]
            )
        )
        
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

            w = [input.w0(), input.w1(), input.w2(), input.w3(),input.w4(), input.w5(), input.w6(), input.w7()]

            df_filtered["weighted_score"] = (
            df_filtered["건물연차점수"] * w[0] +
            df_filtered["지상층수_점수"] * w[1] +
            df_filtered["지하층수_점수"] * w[2] +
            df_filtered["비상용승강기_점수"] * w[3] +
            df_filtered["주용도_점수"] * w[4] +
            df_filtered["구조코드_점수"] * w[5] +
            df_filtered["소화전거리_점수"] * w[6] +
            df_filtered["소방관서거리_점수"] * w[7]
                )

        # 저장할 컬럼
            selected_cols = ["대지위치", "위도", "경도", "total_score", "weighted_score"]
            df_selected = df_filtered[selected_cols]

            yield df_selected.to_csv(index=False, encoding="utf-8-sig")

        return generator()  # ← 여기 반드시 () 붙여서 실행 결과 반환!!!
    
    def summarize_buildings(df_subset, label):
        most_common_year = df_subset['사용승인일(년도)'].mode().iloc[0] if not df_subset['사용승인일(년도)'].mode().empty else None
        most_common_purpose = df_subset['주용도코드명'].mode().iloc[0] if not df_subset['주용도코드명'].mode().empty else None
        most_common_material = df_subset['구조코드명'].mode().iloc[0] if not df_subset['구조코드명'].mode().empty else None
        avg_hydrant_dist = f"{round(df_subset['소화전거리'].mean(), 2):,}"
        avg_firestation_dist = f"{round(df_subset['소방서거리'].mean(), 2):,}"
        avg_total_score = round(df_subset['total_score'].mean(), 2)

        return [
            label,
            most_common_year,
            most_common_purpose,
            most_common_material,
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
            "구분", "최빈 사용 승인 연도", "최빈 주용도", "최빈 건물 구조", "소화전 거리 평균", "소방관서 거리 평균", "취약 점수 평균"
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
        gdf = gpd.read_file("old.geojson").to_crs(epsg=4326)

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
        m = folium.Map(location=[center.y, center.x], zoom_start=10)

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
            ui.HTML(m._repr_html_())
        )
    @reactive.Effect
    @reactive.event(input.go_home)
    def _():
        session.send_input("main_tab", "프로젝트 개요")


    @output
    @render.plot
    def top_bottom_histogram():
        import matplotlib.pyplot as plt
    
        filtered = filtered_building_df()
        if filtered.empty:
            fig, ax = plt.subplots()
            ax.set_title("데이터 없음")
            return fig
    
        # 전체 데이터
        all_scores = filtered["total_score"]
    
        # 상/하위 10% 기준값
        top_thresh = all_scores.quantile(0.9)
        bottom_thresh = all_scores.quantile(0.1)
    
        # 각 그룹 나누기
        top_10 = filtered[filtered["total_score"] >= top_thresh]
        bottom_10 = filtered[filtered["total_score"] <= bottom_thresh]
        mid_80 = filtered[(filtered["total_score"] > bottom_thresh) & (filtered["total_score"] < top_thresh)]
    
        # 공통 bins 설정
        bin_edges = plt.hist(all_scores, bins=30)[1]
        plt.clf()
    
        fig, ax = plt.subplots(figsize=(10, 5))
    
        # 중간 80% 회색
        ax.hist(mid_80["total_score"], bins=bin_edges, alpha=0.5, color="lightgray", label="중간 80%")
    
        # 하위 10% 주황
        ax.hist(bottom_10["total_score"], bins=bin_edges, alpha=0.7, color="orange", label="하위 10%")
    
        # 상위 10% 파랑
        ax.hist(top_10["total_score"], bins=bin_edges, alpha=0.7, color="royalblue", label="상위 10%")
        
        
    
        ax.set_title("취약 점수 분포",fontproperties=font_prop)
        ax.set_xlabel("취약 점수 (total_score)",fontproperties=font_prop)
        ax.set_ylabel("건물 수",fontproperties=font_prop)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        ax.legend(prop=font_prop)
    
        return fig
    @output
    @render.data_frame
    def show_ProjectSummary_table():
        df = pd.read_csv("ProjectSummary.csv", sep="\t", encoding="utf-8")
        return render.DataGrid(df, width="100%", height="500px", filters=False)
    
    @output
    @render.ui
    def show_score_map3():
        selected = ['금호읍', '청통면', '신녕면', '화산면', '화북면', '화남면', '자양면', '임고면', '고경면',
                    '북안면', '대창면', '동부동', '중앙동', '서부동', '완산동', '남부동']
        
        gdf = gpd.read_file("old.geojson")

        # ✅ df_fake 사용
        df_score = df_fake[df_fake["읍면동"].isin(selected)].copy()
        df_score_grouped = df_score.groupby("읍면동")["total_score"].mean().reset_index()
        df_score_grouped = df_score_grouped.rename(columns={"읍면동": "EMD_KOR_NM", "total_score": "평균위험도"})

        gdf = gdf.merge(df_score_grouped, on="EMD_KOR_NM", how="left")
        gdf["평균위험도"] = gdf["평균위험도"].fillna(0)
        gdf = gdf[gdf["EMD_KOR_NM"].isin(selected)].copy()

        min_score = gdf["평균위험도"].min()
        max_score = gdf["평균위험도"].max()
        step = (max_score - min_score) / 5 if max_score != min_score else 1

        # ✅ 색상 스텝 정의
        thresholds = [min_score + step * i for i in range(6)]  # 5등급 → 6경계값
        colors = ["#91cf60", "#d9ef8b", "#fee08b", "#fc8d59", "#d73027"]

        colormap = cm.StepColormap(
            colors=colors,
            index=thresholds,
            vmin=min_score,
            vmax=max_score,
            caption="평균 취약 점수"
        )

        center = gdf.geometry.unary_union.centroid
        m = folium.Map(location=[center.y, center.x], zoom_start=10)

        folium.GeoJson(
            gdf,
            name="위험도 시각화",
            style_function=lambda feature: {
                "fillColor": colormap(feature["properties"].get("평균위험도", 0)),
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

        # ✅ 색상바 추가
        colormap.add_to(m)

        return ui.HTML(m._repr_html_())

    
    @output
    @render.ui
    def show_score_comparison_boxes():
        selected = ['금호읍', '청통면', '신녕면', '화산면', '화북면', '화남면', '자양면', '임고면',
                    '고경면', '북안면', '대창면', '동부동', '중앙동', '서부동', '완산동', '남부동']

        df_before = df[df["읍면동"].isin(selected)].groupby("읍면동")["total_score"].mean().round(2).reset_index()
        df_after = df_fake[df_fake["읍면동"].isin(selected)].groupby("읍면동")["total_score"].mean().round(2).reset_index()

        df_before = df_before.rename(columns={"total_score": "전"})
        df_after = df_after.rename(columns={"total_score": "후"})
        df_compare = df_before.merge(df_after, on="읍면동")
        df_compare["변화"] = (df_compare["후"] - df_compare["전"]).abs()

        top4 = df_compare.sort_values(by="변화", ascending=False).head(4)

        boxes = []
        for _, row in top4.iterrows():
            box = ui.value_box(
                title=row["읍면동"],
                value=f"{row['전']} → {row['후']}",
                showcase=ui.img(src="fire.png", height="60px"),
                theme="danger" if row["후"] > row["전"] else "",
                style="font-size: 1.5rem; min-height: 130px;"
            )
            boxes.append(box)

    # 세로로 네 개 쌓기: 한 열로 구성
        return ui.layout_column_wrap(width=1, *boxes)
    @reactive.calc
    def mean_score_by_dong():
        filtered = filtered_building_df()
        grouped = (
        filtered
        .dropna(subset=['읍면동', 'total_score'])  # 결측 제거
        .groupby('읍면동', as_index=False)['total_score']
        .mean()
        .rename(columns={'total_score': '위험 점수 평균'})
        )
        return grouped
    
    @render.ui
    def show_top_score_boxes():
        df_top4 = top5_score.head(4)
        return [  # 첫 번째 행
                ui.value_box(
                    title=df_top4.iloc[0]["읍면동"],
                    value=f"{df_top4.iloc[0]['total_score']:.2f}",
                    showcase=ui.img(src="alarmdark.png", height="60px"),
                    theme="",
                    style="font-size: 1.4rem; min-height: 130px;"
                ),
                ui.value_box(
                    title=df_top4.iloc[1]["읍면동"],
                    value=f"{df_top4.iloc[1]['total_score']:.2f}",
                    showcase=ui.img(src="alarm.png", height="60px"),
                    theme="",
                    style="font-size: 1.4rem; min-height: 130px;"
                ),
                ui.value_box(
                    title=df_top4.iloc[2]["읍면동"],
                    value=f"{df_top4.iloc[2]['total_score']:.2f}",
                    showcase=ui.img(src="alarmdark.png", height="60px"),
                    theme="",
                    style="font-size: 1.4rem; min-height: 130px;"
                ),
                ui.value_box(
                    title=df_top4.iloc[3]["읍면동"],
                    value=f"{df_top4.iloc[3]['total_score']:.2f}",
                    showcase=ui.img(src="alarm.png", height="60px"),
                    theme="",
                    style="font-size: 1.4rem; min-height: 130px;"
                )
        ]

    
    @render.ui
    def show_top_old_boxes():
        df_top4_old = top5_old.head(4)
        return [
                ui.value_box(
                    title=df_top4_old.iloc[0]["읍면동"],
                    value=f"{df_top4_old.iloc[0]['고령인구비율']:.2f}%",
                    showcase=ui.img(src="oldman.png", height="60px"),
                    theme="purple"
                ),
                ui.value_box(
                    title=df_top4_old.iloc[1]["읍면동"],
                    value=f"{df_top4_old.iloc[1]['고령인구비율']:.2f}%",
                    showcase=ui.img(src="oldmandark.png", height="60px"),
                    theme="purple"
                ),
                ui.value_box(
                    title=df_top4_old.iloc[2]["읍면동"],
                    value=f"{df_top4_old.iloc[2]['고령인구비율']:.2f}%",
                    showcase=ui.img(src="oldmandark.png", height="60px"),
                    theme="purple"
                ),
                ui.value_box(
                    title=df_top4_old.iloc[3]["읍면동"],
                    value=f"{df_top4_old.iloc[3]['고령인구비율']:.2f}%",
                    showcase=ui.img(src="oldman.png", height="60px"),
                    theme="purple"
                )
        ]

    
    @output
    @render.plot
    def line_total_score_by_dong():
        import matplotlib.pyplot as plt

        # 데이터 준비
        df_score = mean_score_by_dong()
        df_age = df_population[['읍면동', '고령인구비율']].copy()
        highlight_dongs = ['화산면', '임고면']

        # ❶ 위험 점수 정렬용
        df_score_sorted = df_score.sort_values(by='위험 점수 평균', ascending=False).reset_index(drop=True)
        df_score_sorted['순서_위험'] = df_score_sorted.index

        # ❷ 고령 인구 정렬용
        df_age_sorted = df_age.sort_values(by='고령인구비율', ascending=False).reset_index(drop=True)
        df_age_sorted['순서_고령'] = df_age_sorted.index

        # 플롯 그리기
        fig, ax1 = plt.subplots(figsize=(9, 5))

        # 왼쪽 y축: 위험 점수
        color1 = 'skyblue'
        ax1.plot(df_score_sorted['순서_위험'], df_score_sorted['위험 점수 평균'], marker='o', color=color1, label='취약 점수 평균')
        ax1.set_ylabel('취약 점수 평균', color=color1,fontsize=14,fontproperties=font_prop)
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.set_xticks(df_score_sorted['순서_위험'])
        ax1.set_xticklabels([''] * len(df_score_sorted))
        # 강조: 위험 점수
        for dong in highlight_dongs:
            row = df_score_sorted[df_score_sorted['읍면동'] == dong]
            if not row.empty:
                idx = row['순서_위험'].values[0]
                score = row['위험 점수 평균'].values[0]
                ax1.scatter(idx, score, color='red', zorder=5)
                ax1.text(idx, score + 0.2, f"{dong}\n({score:.2f})", ha='center', va='bottom', color='red', fontweight='bold',fontproperties=font_prop)

        # 오른쪽 y축: 고령 인구
        ax2 = ax1.twinx()
        color2 = 'green'
        ax2.plot(df_age_sorted['순서_고령'], df_age_sorted['고령인구비율'], marker='s', linestyle='--', color=color2, label='고령 인구 비율')
        ax2.set_ylabel('고령 인구 비율 (%)', color=color2,fontsize=14,fontproperties=font_prop)
        ax2.tick_params(axis='y', labelcolor=color2)

        # 강조: 고령 인구
        for dong in highlight_dongs:
            row = df_age_sorted[df_age_sorted['읍면동'] == dong]
            if not row.empty:
                idx = row['순서_고령'].values[0]
                age = row['고령인구비율'].values[0]
                ax2.scatter(idx, age, color='red', zorder=5)
                ax2.text(idx, age + 0.5, f"{dong}\n({age:.1f}%)", ha='center', va='bottom', color='red', fontweight='bold',fontproperties=font_prop)

        # 제목
        plt.title('취약 점수 (ㅡ) / 고령 인구 비율 (---)', fontproperties=font_prop)
        plt.tight_layout()
        
    applied = reactive.Value(False)
    applied_region = reactive.Value(region_list)  # 초기값은 전체 선택
    
    @reactive.effect
    @reactive.event(input.apply_filter)
    def _():
        applied.set(True)
        applied_region.set(input.region())  # 버튼 눌렀을 때만 업데이트
    
    @reactive.calc
    def filtered_region():
        return applied_region.get()
    
    @reactive.Effect
    @reactive.event(input.go_home)
    def _():
        session.send_input("main_tab", "사용자 가중치 설정")
app = App(app_ui, server, static_assets=STATIC_DIR)

