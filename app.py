import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 환경 설정
st.set_page_config(
    page_title="기후 변화 분석: 1960년대 vs 현대",
    page_icon="🌡️",
    layout="wide"
)

# 제목 및 설명
st.title("🌡️ 시대별 계절 기온 변화 분석 대시보드")
st.markdown("""
이 대시보드는 1960년대(1960-1969년)와 현대(2010-2019년)의 서울(지점 108) 일별 기온 데이터를 바탕으로, 사계절의 기후 변화를 비교 분석합니다.
""")

# 성능 향상을 위한 데이터 로드 및 캐싱
@st.cache_data
def load_data():
    # [수정] 파일 내부의 따옴표(")와 양쪽 공백을 완전히 무시하고 읽어옵니다.
    df = pd.read_csv("ta_20260601093156.csv", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    
    # 날짜 컬럼 안의 모든 탭(\t), 따옴표("), 공백을 완벽히 제거
    df['날짜'] = df['날짜'].astype(str).str.replace(r'[\t"\s]', '', regex=True)
    
    # 날짜형 데이터로 변환 후 에러 데이터 제거
    df['Date'] = pd.to_datetime(df['날짜'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # 분석용 컬럼명 매핑
    df = df.rename(columns={
        '평균기온(℃)': 'Avg_Temp',
        '최저기온(℃)': 'Min_Temp',
        '최고기온(℃)': 'Max_Temp'
    })
    
    # 연도 및 월 추출
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    
    # 시대(Era) 분류 정의
    def assign_era(year):
        if 1960 <= year <= 1969:
            return '1960년대'
        elif 2010 <= year <= 2019:
            return '현대 (2010년대)'
        return None
    
    df['Era'] = df['Year'].apply(assign_era)
    df = df.dropna(subset=['Era'])
    
    # 계절 분류 정의
    def assign_season(month):
        if month in [3, 4, 5]: return '봄 (3-5월)'
        elif month in [6, 7, 8]: return '여름 (6-8월)'
        elif month in [9, 10, 11]: return '가을 (9-11월)'
        else: return '겨울 (12-2월)'
        
    df['Season'] = df['Month'].apply(assign_season)
    return df

try:
    data = load_data()
    
    # --- 사이드바 제어 조작 ---
    st.sidebar.header("필터 옵션")
    selected_season = st.sidebar.selectbox(
        "분석할 계절을 선택하세요:",
        ['전체 계절', '봄 (3-5월)', '여름 (6-8월)', '가을 (9-11월)', '겨울 (12-2월)']
    )
    
    if selected_season != '전체 계절':
        filtered_data = data[data['Season'] == selected_season]
    else:
        filtered_data = data

    # --- KPI 주요 지표 통계 ---
    st.subheader(f"📊 주요 기온 통계 요약: {selected_season}")
    
    # 시대별 기온 평균 계산
    summary = filtered_data.groupby('Era')['Avg_Temp'].mean().round(2)
    max_summary = filtered_data.groupby('Era')['Max_Temp'].mean().round(2)
    min_summary = filtered_data.groupby('Era')['Min_Temp'].mean().round(2)
    
    # [수정] 데이터 공백으로 인한 0 도출 및 13도 에러 방지 안전장치 추가
    val_modern_avg = summary.get('현대 (2010년대)', 0)
    val_60s_avg = summary.get('1960년대', 0)
    
    val_modern_max = max_summary.get('현대 (2010년대)', 0)
    val_60s_max = max_summary.get('1960년대', 0)
    
    val_modern_min = min_summary.get('현대 (2010년대)', 0)
    val_60s_min = min_summary.get('1960년대', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        diff_avg = round(val_modern_avg - val_60s_avg, 2) if val_60s_avg != 0 else 0
        st.metric(
            label="일평균 기온", 
            value=f"{val_modern_avg} °C" if val_modern_avg != 0 else "데이터 없음", 
            delta=f"1960년대 대비 {diff_avg:+g} °C" if val_60s_avg != 0 else None
        )
    with col2:
        diff_max = round(val_modern_max - val_60s_max, 2) if val_60s_max != 0 else 0
        st.metric(
            label="평균 최고 기온", 
            value=f"{val_modern_max} °C" if val_modern_max != 0 else "데이터 없음", 
            delta=f"1960년대 대비 {diff_max:+g} °C" if val_60s_max != 0 else None
        )
    with col3:
        diff_min = round(val_modern_min - val_60s_min, 2) if val_60s_min != 0 else 0
        st.metric(
            label="평균 최저 기온", 
            value=f"{val_modern_min} °C" if val_modern_min != 0 else "데이터 없음", 
            delta=f"1960년대 대비 {diff_min:+g} °C" if val_60s_min != 0 else None
        )

    st.markdown("---")

    # --- 시각화 차트 ---
    left_chart, right_chart = st.columns(2)
    
    with left_chart:
        st.subheader("기온 분포 및 밀도 (히스토그램)")
        fig_dist = px.histogram(
            filtered_data, 
            x="Avg_Temp", 
            color="Era", 
            barmode="overlay",
            marginal="box",
            opacity=0.6,
            color_discrete_map={'1960년대': '#3498db', '현대 (2010년대)': '#e74c3c'},
            labels={'Avg_Temp': '일평균 기온 (°C)', 'count': '일수 (Days)', 'Era': '시대'}
        )
        fig_dist.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="일수 (Days)"
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with right_chart:
        st.subheader("계절별 기온 범위 비교 (박스플롯)")
        fig_box = px.box(
            data if selected_season == '전체 계절' else filtered_data,
            x="Season",
            y="Avg_Temp",
            color="Era",
            color_discrete_map={'1960년대': '#3498db', '현대 (2010년대)': '#e74c3c'},
            category_orders={"Season": ['봄 (3-5월)', '여름 (6-8월)', '가을 (9-11월)', '겨울 (12-2월)']},
            labels={'Season': '계절', 'Avg_Temp': '일평균 기온 (°C)', 'Era': '시대'}
        )
        fig_box.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_box, use_container_width=True)

    # --- 연도별 추세선 ---
    st.subheader("연도별 평균 기온 타임라인 (1960년대 vs 현대)")
    timeline_data = filtered_data.groupby(['Year', 'Era'])['Avg_Temp'].mean().reset_index()
    timeline_data['Year_str'] = timeline_data['Year'].astype(str)
    
    fig_line = go.Figure()
    df_60s = timeline_data[timeline_data['Era'] == '1960년대']
    fig_line.add_trace(go.Scatter(x=df_60s['Year_str'], y=df_60s['Avg_Temp'], name='1960년대', mode='lines+markers', line=dict(color='#3498db', width=3)))
    
    df_mod = timeline_data[timeline_data['Era'] == '현대 (2010년대)']
    fig_line.add_trace(go.Scatter(x=df_mod['Year_str'], y=df_mod['Avg_Temp'], name='현대 (2010년대)', mode='lines+markers', line=dict(color='#e74c3c', width=3)))
    
    fig_line.update_layout(
        xaxis_title="연도 (Year)",
        yaxis_title="연평균 기온 (°C)",
        xaxis=dict(type='category'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error(f"파일을 로드하거나 처리하는 중 오류가 발생했습니다: {e}")
