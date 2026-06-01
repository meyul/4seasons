import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Climate Shift: 1950s vs Modern Era",
    page_icon="🌡️",
    layout="wide"
)

# Title and Description
st.title("🌡️ Historical Climate Shift Analysis")
st.markdown("""
This dashboard compares the daily temperature records of Seoul (Station 108) between the **1950s (1950-1959)** and the **Modern Era (2010-2019)** across all four seasons. 
""")

# Load and cache data for performance
@st.cache_data
def load_data():
    # Load dataset, stripping potential whitespace from column names
    df = pd.read_csv("ta_20260601093156.csv")
    df.columns = df.columns.str.strip()
    
    # Clean the Date column (remove tabs/quotes if present)
    df['날짜'] = df['날짜'].astype(str).str.replace(r'[\t"\s]', '', regex=True)
    df['Date'] = pd.to_datetime(df['날짜'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Rename columns for ease of use
    df = df.rename(columns={
        '평균기온(℃)': 'Avg_Temp',
        '최저기온(℃)': 'Min_Temp',
        '최고기온(℃)': 'Max_Temp'
    })
    
    # Extract Year and Month
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    
    # Define Eras
    def assign_era(year):
        if 1950 <= year <= 1959:
            return '1950s'
        elif 2010 <= year <= 2019:
            return 'Modern Era (2010s)'
        return None
    
    df['Era'] = df['Year'].apply(assign_era)
    df = df.dropna(subset=['Era'])
    
    # Define Korean Seasons
    # Spring: Mar-May, Summer: Jun-Aug, Autumn: Sep-Nov, Winter: Dec-Feb
    def assign_season(month):
        if month in [3, 4, 5]: return 'Spring (Mar-May)'
        elif month in [6, 7, 8]: return 'Summer (Jun-Aug)'
        elif month in [9, 10, 11]: return 'Autumn (Sep-Nov)'
        else: return 'Winter (Dec-Feb)'
        
    df['Season'] = df['Month'].apply(assign_season)
    return df

try:
    data = load_data()
    
    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("Filter Options")
    selected_season = st.sidebar.selectbox(
        "Select a Season to Inspect:",
        ['All Seasons', 'Spring (Mar-May)', 'Summer (Jun-Aug)', 'Autumn (Sep-Nov)', 'Winter (Dec-Feb)']
    )
    
    # Filter dataset based on selection
    if selected_season != 'All Seasons':
        filtered_data = data[data['Season'] == selected_season]
    else:
        filtered_data = data

    # --- KPI METRICS ---
    st.subheader(f"📊 Summary Statistics: {selected_season}")
    
    # Calculate seasonal averages per Era
    summary = filtered_data.groupby('Era')['Avg_Temp'].mean().round(2)
    max_summary = filtered_data.groupby('Era')['Max_Temp'].mean().round(2)
    min_summary = filtered_data.groupby('Era')['Min_Temp'].mean().round(2)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        diff_avg = round(summary.get('Modern Era (2010s)', 0) - summary.get('1950s', 0), 2)
        st.metric(
            label="Average Temperature", 
            value=f"{summary.get('Modern Era (2010s', 'N/A')} °C", 
            delta=f"{diff_avg:+g} °C vs 1950s"
        )
    with col2:
        diff_max = round(max_summary.get('Modern Era (2010s)', 0) - max_summary.get('1950s', 0), 2)
        st.metric(
            label="Average Max Temperature", 
            value=f"{max_summary.get('Modern Era (2010s)', 'N/A')} °C", 
            delta=f"{diff_max:+g} °C vs 1950s"
        )
    with col3:
        diff_min = round(min_summary.get('Modern Era (2010s)', 0) - min_summary.get('1950s', 0), 2)
        st.metric(
            label="Average Min Temperature", 
            value=f"{min_summary.get('Modern Era (2010s)', 'N/A')} °C", 
            delta=f"{diff_min:+g} °C vs 1950s"
        )

    st.markdown("---")

    # --- VISUALIZATIONS ---
    left_chart, right_chart = st.columns(2)
    
    with left_chart:
        st.subheader("Temperature Distributions (Density)")
        # Histogram/Density plot to show shifts in temperatures
        fig_dist = px.histogram(
            filtered_data, 
            x="Avg_Temp", 
            color="Era", 
            barmode="overlay",
            marginal="box",
            color_discrete_map={'1950s': '#3498db', 'Modern Era (2010s)': '#e74c3c'},
            labels={'Avg_Temp': 'Daily Average Temperature (°C)', 'count': 'Days Count'}
        )
        fig_dist.update_layout(opacity=0.6, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_dist, use_container_width=True)

    with right_chart:
        st.subheader("Seasonal Temperature Ranges")
        # Box plot broken down by seasons for macro view
        fig_box = px.box(
            data if selected_season == 'All Seasons' else filtered_data,
            x="Season",
            y="Avg_Temp",
            color="Era",
            color_discrete_map={'1950s': '#3498db', 'Modern Era (2010s)': '#e74c3c'},
            category_orders={"Season": ['Spring (Mar-May)', 'Summer (Jun-Aug)', 'Autumn (Sep-Nov)', 'Winter (Dec-Feb)']}
        )
        fig_box.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_box, use_container_width=True)

    # --- RECENT TREND LINE ---
    st.subheader("Yearly Averages Timeline (1950s vs Modern Era)")
    timeline_data = filtered_data.groupby(['Year', 'Era'])['Avg_Temp'].mean().reset_index()
    
    fig_line = go.Figure()
    # 1950s Line
    df_50s = timeline_data[timeline_data['Era'] == '1950s']
    fig_line.add_trace(go.Scatter(x=df_50s['Year'], y=df_50s['Avg_Temp'], name='1950s', line=dict(color='#3498db', width=3)))
    # Modern Line
    df_mod = timeline_data[timeline_data['Era'] == 'Modern Era (2010s)']
    fig_line.add_trace(go.Scatter(x=df_mod['Year'], y=df_mod['Avg_Temp'], name='Modern Era', line=dict(color='#e74c3c', width=3)))
    
    fig_line.update_layout(
        xaxis_title="Year",
        yaxis_title="Mean Temperature (°C)",
        xaxis=dict(tickmode='linear')
    )
    st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error(f"Error loading or processing file: {e}")
    st.info("Please make sure 'ta_20260601093156.csv' is placed in the same repository folder.")
