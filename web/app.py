import streamlit as st
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
from streamlit.components.v1 import html
import pydeck as pdk
import altair as alt


st.set_page_config(
    page_title="Social Data Analysis | Solar Energy Project",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="auto",
)

# read only data if it is not in session state
if 'data' not in st.session_state:
    data = pd.read_csv("../final/data/dfMerged.csv")
    data['usage_date'] = pd.to_datetime(data['usage_date'])
    
    # remove max value from data['totalUsePower']

    usePowerMax = data['totalUsePower'].max()
    data['totalUsePower'] = data['totalUsePower'].apply(lambda x: x if x < usePowerMax else 0)

    st.session_state.data = data
else:
    data = st.session_state.data


test, logo, _ = st.sidebar.columns([0.5, 1, 0.5])

with logo:
    st.image('images/dtuLogo.png', width=150)

st.sidebar.write('---')
st.sidebar.title('Social Data Analysis')
st.sidebar.write("Welcome to the Solar Energy Project. This project aims to analyze solar energy data from the danish company EasyGreen.")
st.sidebar.write("Please filter the data from the sidebar and the plots will apply your filters on change.")

st.write('')

viz = st.sidebar.selectbox("Select visualization", ["Solar Energy Data in Denmark", "EasyGreen Map Data", "EasyGreen Production Development"])


if viz == "Solar Energy Data in Denmark":
    # Integrafe html plot
    st.title("General Solar Energy Data in Denmark")
    st.write('')
    #st.header("")
    
    # Google Data
    googleData = pd.read_csv('../final/data/multiTimeline.csv', header=1)
    googleData['Week'] = googleData['Uge']
    googleData['Week'] = pd.to_datetime(googleData['Week'], format='%Y-%m-%d')
    googleData['Index'] = googleData['Solcelle: (Danmark)'].astype(float)

    # Energinet Data
    energinetData = pd.read_csv('../final/data/energinetForecast.csv', sep=';', error_bad_lines=False, usecols=['HourDK', 'ForecastCurrent'])    
    energinetData['HourDK'] = pd.to_datetime(energinetData['HourDK'])
    energinetData['Production (MWh per hour)'] = energinetData['ForecastCurrent'].str.replace(',', '.').astype(float)    
    
    energinetData.set_index('HourDK', inplace=True)
    energinetData = energinetData.resample('W').agg({'Production (MWh per hour)': 'sum'}).reset_index()
    energinetData.rename(columns={'HourDK': 'Week'}, inplace=True)

    # Sort by 'Week'
    energinetData = energinetData.sort_values(by='Week')

    # set minimum date to match in both dataframes. Use the maximum of the two minimum dates
    minDate = max(energinetData['Week'].min(), googleData['Week'].min())
    energinetData = energinetData[energinetData['Week'] >= minDate]
    googleData = googleData[googleData['Week'] >= minDate]    

    # accumulate the forecast data
    energinetData['Accumulated Production (MWh per hour)'] = energinetData['Production (MWh per hour)'].cumsum()

    # help: source https://www.energidataservice.dk/tso-electricity/Forecasts_Hour
    st.subheader("Production from Solar Power in Denmark per week")    

    energinetData['Above_15000'] = energinetData['Production (MWh per hour)'] > 15000
    energinetData['Segment'] = energinetData['Above_15000'].astype(int).diff().ne(0).cumsum()
    df_endpoints = energinetData.copy()
    df_endpoints['Week'] = df_endpoints['Week'].shift(-1)
    df_endpoints['Production (MWh per hour)'] = df_endpoints['Production (MWh per hour)'].shift(-1)
    df_final = pd.concat([energinetData, df_endpoints]).sort_values(by=['Week', 'Segment']).dropna()
    base = alt.Chart(df_final).encode(
        x='Week:O',  # Ordinal data
        y='Production (MWh per hour):Q',  # Quantitative data
        detail='Segment:N'  # Use segment number as detail to differentiate lines
    )
    lines = base.mark_line().encode(
        x=alt.X('Week:T'), 
        color=alt.condition(
            alt.datum.Above_15000,
            alt.value('lightgreen'),  # True color
            alt.value('green')  # False color
        )
    )
    st.altair_chart(lines, use_container_width=True)

    st.subheader("Accumulated Production from Solar Power in Denmark")
    st.altair_chart(alt.Chart(energinetData).mark_line(color='#228B22').encode(
        x='Week',
        y='Accumulated Production (MWh per hour)'
    ).properties(
        width='container'
    ), use_container_width=True)

    # help: source https://trends.google.com/trends/explore?date=today%205-y&geo=DK&q=%2Fm%2F078kl
    st.subheader("Google Searches for Solar Power in Denmark per week")
    st.altair_chart(alt.Chart(googleData).mark_line().encode(
        x='Week',
        y='Index'
    ).properties(
        width='container'
    ), use_container_width=True)

## Map plot

if viz == "EasyGreen Map Data":
    st.header("EasyGreen Map Data") 
    st.subheader("The map below shows the development of EasyGreen's customers over time.")


    # Group by user_id and get the first usage_date and sum of totalProductPower
    data = data.groupby('user_id').agg({'usage_date': 'min',
                                        'totalProductPower': 'mean',
                                        'totalSelfUsePower': 'mean',
                                        'latitude': 'mean',
                                        'longitude': 'mean',
                                        'age': 'mean'}).reset_index()
                

    # Drop rows with missing latitude or longitude
    data.dropna(subset=['latitude', 'longitude', 'totalProductPower', 'totalSelfUsePower', 'age'], inplace=True)

    # Sort by usage_date
    data = data.sort_values(by='usage_date')

    # Filters

    ## example return (datetime.date(2024, 1, 31), datetime.date(2024, 3, 28))
    selected_date_range = st.sidebar.date_input("Filter map by system installation date", value=(data['usage_date'].min(), data['usage_date'].max()), min_value=data['usage_date'].min(), max_value=data['usage_date'].max())
    selected_date_range = pd.to_datetime(selected_date_range)

    if len(selected_date_range.unique()) < 2:
        st.spinner('Please select a date range of at least two different dates.')
    else:
        data = data[(data['usage_date'] >= selected_date_range[0]) & (data['usage_date'] <= selected_date_range[1])]

    ## Age range
    age_range = st.sidebar.slider("Filter map by customer age range", 0, 100, (0, 100))
    data = data[(data['age'] >= age_range[0]) & (data['age'] <= age_range [1])]

    ## Production range
    max_range = int(data['totalProductPower'].max())
    production_range = st.sidebar.slider("Filter map by daily production range", 0, max_range, (0, max_range))
    data = data[(data['totalProductPower'] >= production_range[0]) & (data['totalProductPower'] <= production_range[1])]

    data.reset_index(inplace=True)

    elevation = st.sidebar.radio("Analyze by", ('Average Production Per Day', 'Average Utilized Production Per Day', 'Age'))
    
    if elevation == 'Average Production Per Day':
        elevation_weight = 'totalProductPower'
    elif elevation == 'Average Utilized Production Per Day':
        elevation_weight = 'totalSelfUsePower'
    elif elevation == 'Age':
        elevation_weight = 'age'

    layer = pdk.Layer(
        "HexagonLayer" if elevation_weight != 'age' else "HeatmapLayer",
        data=data,
        get_position="[longitude, latitude]",
        auto_highlight=True,
        elevation_scale=3000,
        pickable=True,
        get_polygon="-",
        get_fill_color=[0, 0, 0, 20],
        stroked=False,
        elevation_range=[0, max_range],
        extruded=True,
        coverage=1,
        get_elevation_weight = elevation_weight,
    )

    view_state = pdk.ViewState(
        longitude=10.38831, latitude=55.79594, zoom=6.2, min_zoom=5, max_zoom=11 if elevation_weight != 'age' else 7, pitch=41 if elevation_weight != 'age' else 0, bearing=20 if elevation_weight != 'age' else 0, height=700
    )



    # Combined all of it and render a viewport
    r = pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v9",
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
                "html":f"<b>{elevation}:</b> {{elevationValue}}<br>",
                "style": {"color": "white"}}        
    )

    st.pydeck_chart(r)    

# Accumulated production per month

if viz == "EasyGreen Production Development":

    ## Production

    st.header("Production and usage overview of EasyGreen's customers")

    #st.subheader("")

    showSelfUse = st.sidebar.toggle('Show Utilized Production', True)    
    showNightUsage = st.sidebar.toggle('Show Night Usage', False, help = 'Night usage is calculated as the usage between 18:00 and 06:00')
    
    data['usage_month'] = data['usage_date'].dt.month 

    # Ensure 'totalProductPower' is float and apply conditions
    data['totalProductPower'] = data['totalProductPower'].astype(float)
    data['totalProductPower'] = data['totalProductPower'].apply(lambda x: max(0, min(x, 10000)))

    # Convert 'usage_date' to month names
    data['usage_month'] = data['usage_date'].dt.strftime('%B')
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    data['usage_month'] = pd.Categorical(data['usage_month'], categories=month_order, ordered=True)

    # Ensure 'totalProductPower' is float and apply conditions
    data['totalProductPower'] = data['totalProductPower'].astype(float)
    data['totalProductPower'] = data['totalProductPower'].apply(lambda x: max(0, min(x, 10000)))

    # Chart data
    production_data = data.groupby('usage_month')['totalProductPower'].mean().reset_index()
    self_use_data = data.groupby('usage_month')['totalSelfUsePower'].mean().reset_index()
    totalUsePower_data = data.groupby('usage_month')['totalUsePower'].mean().reset_index()
    night_data = data.groupby('usage_month')['night_usage'].mean().reset_index()

    # Charts
    production_chart = alt.Chart(production_data).mark_bar(color = 'green', opacity=0.5).encode(
        x=alt.X('usage_month:N', title='Month', sort=month_order),  # Specify nominal data with :N
        y=alt.Y('totalProductPower:Q', title='Production in kWh'),  # Specify quantitative data with :Q
            tooltip=[
                alt.Tooltip('usage_month:N', title='Month'),
                alt.Tooltip('totalProductPower:Q', title='Average Production per Day')
            ]
    ).properties(
        height=600
    )

    selfUse_chart = alt.Chart(self_use_data).mark_bar(color = 'green').encode(
            x=alt.X('usage_month:N', sort=month_order),  # Specify nominal data with :N
            y=alt.Y('totalSelfUsePower:Q'),  # Specify quantitative data with :Q
            tooltip=[
                alt.Tooltip('usage_month:N', title='Month'),
                alt.Tooltip('totalSelfUsePower:Q', title='Average Utilized Production per Day')
            ]
        ).properties(
            height=600
    )

    use_chart = alt.Chart(totalUsePower_data).mark_bar(color = 'red', opacity=0.5).encode(
            x=alt.X('usage_month:N', sort=month_order, title = 'Month'),  # Specify nominal data with :N
            y=alt.Y('totalUsePower:Q', title= 'Usage in kWh'),
            tooltip=[
                alt.Tooltip('usage_month:N', title='Month'),
                alt.Tooltip('totalUsePower:Q', title='Usage in kWh per Day')
            ]
        ).properties(
            height=600
    )

    nightUsage_chart = alt.Chart(night_data).mark_bar(color = 'red').encode(
            x=alt.X('usage_month:N', sort=month_order),
            y=alt.Y('night_usage:Q'),
            tooltip=[
                alt.Tooltip('usage_month:N', title='Month'),
                alt.Tooltip('night_usage:Q', title='Avg. Night Usage per Day')
            ]
        ).properties(
            height=600
    )

    # Plots
    st.altair_chart(production_chart+selfUse_chart if showSelfUse else production_chart, use_container_width=True)
    st.altair_chart(use_chart+nightUsage_chart if showNightUsage else use_chart, use_container_width=True)

st.sidebar.write('---')
st.sidebar.write("This project was created in the 02806 Social data analysis and visualization course at DTU. The group consists of the following members:")
st.sidebar.write(" * Shakir Maytham Shaker")
st.sidebar.write(" * Magnus Mac Doberenz")
st.sidebar.write(" * Yili Ge")
st.sidebar.download_button("Download Complete Notebook", open("../final/explainer.ipynb").read(), 'SolarEnergyProject.ipynb')