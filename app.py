import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Fallas Air Pollution Analysis",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 10rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 4rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">Fallas Air Pollution Analysis</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">To what extent do pyrotechnic activities during Valencia\'s Fallas increase particulate matter air pollution?</p>', unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    """Load and prepare the pollution data"""
    try:
        # Try to load from data folder
        df = pd.read_csv('data/all_pollution_data.csv')
    except:
        # If not found, try current directory
        df = pd.read_csv('all_pollution_data.csv')
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df

# Load the data
try:
    df = load_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please make sure 'all_pollution_data.csv' is in the 'data/' folder or the same directory as app.py")
    data_loaded = False

if data_loaded:
    # Sidebar filters
    st.sidebar.header("🔍 Filter Options")
    
    # Year selection
    available_years = sorted([y for y in df['Year'].unique() if pd.notna(y)])
    default_years = [y for y in [2022, 2023, 2024, 2025] if y in available_years]
    
    selected_years = st.sidebar.multiselect(
        "Select Years",
        options=available_years,
        default=default_years if default_years else available_years[-3:]
    )
    
    # Pollutant selection
    pollutant_options = {
        'PM2.5 (Fine Particulate Matter)': 'PM2.5(µg/m³)',
        'PM10 (Coarse Particulate Matter)': 'PM10(µg/m³)',
        'NO2 (Nitrogen Dioxide)': 'NO2(µg/m³)',
        'NOx (Nitrogen Oxides)': 'NOx(µg/m³)'
    }
    
    selected_pollutant_name = st.sidebar.selectbox(
        "Select Pollutant",
        options=list(pollutant_options.keys()),
        index=0
    )
    
    selected_pollutant = pollutant_options[selected_pollutant_name]
    
    # Filter data
    filtered_df = df[df['Year'].isin(selected_years)] if selected_years else df
    
    # WHO Guidelines
    who_guidelines = {
        'PM2.5(µg/m³)': 15,
        'PM10(µg/m³)': 45,
        'NO2(µg/m³)': 25
    }
    
    # Calculate key metrics
    pre_fallas = filtered_df[filtered_df['Period'] == 'Pre-Fallas (Mar 1-14)'][selected_pollutant].mean()
    fallas = filtered_df[filtered_df['Period'] == 'Fallas (Mar 15-19)'][selected_pollutant].mean()
    post_fallas = filtered_df[filtered_df['Period'] == 'Post-Fallas (Mar 20-31)'][selected_pollutant].mean()
    rest_year = filtered_df[filtered_df['Period'] == 'Rest of Year'][selected_pollutant].mean()
    
    # Key Metrics Display
    st.markdown("### 📊 Key Findings")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Pre-Fallas Average",
            value=f"{pre_fallas:.1f} µg/m³"
        )
    
    with col2:
        delta = fallas - pre_fallas
        delta_pct = ((fallas - pre_fallas) / pre_fallas * 100) if pre_fallas > 0 else 0
        st.metric(
            label="During Fallas",
            value=f"{fallas:.1f} µg/m³",
            delta=f"{delta:+.1f} µg/m³ ({delta_pct:+.1f}%)"
        )
    
    with col3:
        st.metric(
            label="Post-Fallas Average",
            value=f"{post_fallas:.1f} µg/m³"
        )
    
    with col4:
        if selected_pollutant in who_guidelines:
            who_limit = who_guidelines[selected_pollutant]
            exceeds = "⚠️ EXCEEDS" if fallas > who_limit else "✅ Within"
            st.metric(
                label="WHO Guideline",
                value=f"{who_limit} µg/m³",
                delta=exceeds
            )
    
    # Tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Time Series", "📊 Period Comparison", "📅 Year-by-Year", "⚠️ Health Impact"])
    
    with tab1:
        st.markdown("### Time Series: Pollution Levels During March")
        
        # Filter for March data
        march_df = filtered_df[filtered_df['Month'] == 3].copy()
        
        if len(march_df) > 0:
            fig = px.line(
                march_df,
                x='Day',
                y=selected_pollutant,
                color='Year',
                title=f"{selected_pollutant_name} Levels Throughout March",
                labels={'Day': 'Day of March', selected_pollutant: 'Concentration (µg/m³)'},
                markers=True
            )
            
            # Add Fallas period shading
            fig.add_vrect(
                x0=14.5, x1=19.5,
                fillcolor="red", opacity=0.15,
                annotation_text="Fallas Period (15-19)", 
                annotation_position="top left"
            )
            
            # Add WHO guideline if applicable
            if selected_pollutant in who_guidelines:
                fig.add_hline(
                    y=who_guidelines[selected_pollutant],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"WHO 24hr Guideline ({who_guidelines[selected_pollutant]} µg/m³)"
                )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No March data available for selected years")
    
    with tab2:
        st.markdown("### Period Comparison: Pre, During, and Post Fallas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Box plot
            period_order = ['Pre-Fallas (Mar 1-14)', 'Fallas (Mar 15-19)', 
                          'Post-Fallas (Mar 20-31)', 'Rest of Year']
            
            plot_df = filtered_df[filtered_df['Period'].isin(period_order)].copy()
            
            fig_box = px.box(
                plot_df,
                x='Period',
                y=selected_pollutant,
                title="Distribution by Period",
                labels={selected_pollutant: 'Concentration (µg/m³)'},
                color='Period',
                category_orders={'Period': period_order}
            )
            
            # Add WHO guideline
            if selected_pollutant in who_guidelines:
                fig_box.add_hline(
                    y=who_guidelines[selected_pollutant],
                    line_dash="dash",
                    line_color="orange"
                )
            
            fig_box.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)
        
        with col2:
            # Bar chart with averages
            period_avg = plot_df.groupby('Period')[selected_pollutant].mean().reindex(period_order)
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=period_order,
                    y=period_avg.values,
                    marker_color=['lightblue', 'red', 'lightgreen', 'lightgray'],
                    text=[f'{v:.1f}' for v in period_avg.values],
                    textposition='auto'
                )
            ])
            
            fig_bar.update_layout(
                title="Average Concentration by Period",
                xaxis_title="Period",
                yaxis_title="Concentration (µg/m³)",
                height=400
            )
            
            # Add WHO guideline
            if selected_pollutant in who_guidelines:
                fig_bar.add_hline(
                    y=who_guidelines[selected_pollutant],
                    line_dash="dash",
                    line_color="orange"
                )
            
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab3:
        st.markdown("### Year-by-Year Analysis")
        
        # Calculate year-by-year statistics
        yearly_stats = []
        march_df = filtered_df[filtered_df['Month'] == 3]
        
        for year in selected_years:
            year_data = march_df[march_df['Year'] == year]
            pre = year_data[year_data['Period'] == 'Pre-Fallas (Mar 1-14)'][selected_pollutant].mean()
            during = year_data[year_data['Period'] == 'Fallas (Mar 15-19)'][selected_pollutant].mean()
            
            if pd.notna(pre) and pd.notna(during):
                pct_change = ((during - pre) / pre * 100) if pre > 0 else 0
                yearly_stats.append({
                    'Year': int(year),
                    'Pre-Fallas': pre,
                    'During Fallas': during,
                    '% Change': pct_change
                })
        
        if yearly_stats:
            yearly_df = pd.DataFrame(yearly_stats)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Grouped bar chart
                fig_yearly = go.Figure()
                
                fig_yearly.add_trace(go.Bar(
                    name='Pre-Fallas',
                    x=yearly_df['Year'],
                    y=yearly_df['Pre-Fallas'],
                    marker_color='lightblue'
                ))
                
                fig_yearly.add_trace(go.Bar(
                    name='During Fallas',
                    x=yearly_df['Year'],
                    y=yearly_df['During Fallas'],
                    marker_color='red'
                ))
                
                fig_yearly.update_layout(
                    title="Pre-Fallas vs During Fallas by Year",
                    xaxis_title="Year",
                    yaxis_title="Concentration (µg/m³)",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig_yearly, use_container_width=True)
            
            with col2:
                # Percentage change chart
                colors = ['green' if x < 0 else 'red' for x in yearly_df['% Change']]
                
                fig_pct = go.Figure(data=[
                    go.Bar(
                        x=yearly_df['Year'],
                        y=yearly_df['% Change'],
                        marker_color=colors,
                        text=[f'{v:+.1f}%' for v in yearly_df['% Change']],
                        textposition='outside'
                    )
                ])
                
                fig_pct.update_layout(
                    title="Percentage Change During Fallas",
                    xaxis_title="Year",
                    yaxis_title="% Change from Pre-Fallas",
                    height=400
                )
                
                fig_pct.add_hline(y=0, line_color="black", line_width=1)
                
                st.plotly_chart(fig_pct, use_container_width=True)
            
            # Data table
            st.markdown("#### Detailed Statistics")
            st.dataframe(
                yearly_df.style.format({
                    'Pre-Fallas': '{:.1f}',
                    'During Fallas': '{:.1f}',
                    '% Change': '{:+.1f}%'
                }),
                use_container_width=True
            )
    
    with tab4:
        st.markdown("### Health Impact Assessment")
        
        if selected_pollutant in who_guidelines:
            who_limit = who_guidelines[selected_pollutant]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Calculate exceedance days
                fallas_data = filtered_df[filtered_df['Period'] == 'Fallas (Mar 15-19)']
                exceedance_days = len(fallas_data[fallas_data[selected_pollutant] > who_limit])
                total_fallas_days = len(fallas_data[fallas_data[selected_pollutant].notna()])
                
                st.info(f"""
                **WHO Air Quality Guideline for {selected_pollutant_name}**
                
                24-hour mean: **{who_limit} µg/m³**
                
                During Fallas period:
                - Average concentration: **{fallas:.1f} µg/m³**
                - Days exceeding guideline: **{exceedance_days} out of {total_fallas_days}**
                - Exceedance rate: **{(exceedance_days/total_fallas_days*100):.1f}%**
                """)
                
                # Health implications
                if 'PM2.5' in selected_pollutant or 'PM10' in selected_pollutant:
                    st.warning("""
                    **Health Implications of Particulate Matter:**
                    
                    - **Short-term exposure:** Respiratory irritation, asthma exacerbation
                    - **Vulnerable groups:** Children, elderly, people with heart/lung conditions
                    - **PM2.5 specifically:** Can penetrate deep into lungs and bloodstream
                    
                    **Recommendations during Fallas:**
                    - Limit outdoor activities during peak hours (mascletàs at 2 PM, cremà at night)
                    - Vulnerable populations should stay indoors when pollution is high
                    - Use N95 masks if exposure is unavoidable
                    """)
            
            with col2:
                # Gauge chart showing current level vs WHO
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=fallas,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"{selected_pollutant_name}<br>During Fallas"},
                    delta={'reference': who_limit, 'suffix': ' vs WHO'},
                    gauge={
                        'axis': {'range': [None, max(fallas * 1.5, who_limit * 2)]},
                        'bar': {'color': "darkred" if fallas > who_limit else "green"},
                        'steps': [
                            {'range': [0, who_limit], 'color': "lightgreen"},
                            {'range': [who_limit, max(fallas * 1.5, who_limit * 2)], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': who_limit
                        }
                    }
                ))
                
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("WHO guidelines are most stringent for particulate matter (PM2.5 and PM10). Select these pollutants to see health impact assessment.")
    
    # Footer with data source and research question
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Data Sources:**
        - Valencia Municipal Air Quality Network (Centro Station, 2018-2025)
        - Sensor.community Citizen Science Network (Sensor #79124, Plaça de l'Ajuntament)
        """)
    
    with col2:
        st.markdown("""
        **Research Question:**
        
        *To what extent do pyrotechnic activities during Valencia's Fallas 
        increase particulate matter air pollution?*
        """)
    
    st.markdown("""
    **Key Findings:**
    - PM2.5 and PM10 show consistent dramatic increases during Fallas (up to 180%)
    - Traffic-related pollutants (NO2, NOx) decrease, confirming pyrotechnics as the source
    - Pollution levels exceed WHO guidelines in most years
    - Recovery to baseline occurs within days after the festival
    """)

else:
    st.error("Unable to load data. Please check the data file location.")