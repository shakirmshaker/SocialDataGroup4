import streamlit as st
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
from streamlit.components.v1 import html
import pydeck as pdk

st.set_page_config(
    page_title="Social Data Analysis | Solar Energy Project",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="auto",
)

# read only data if it is not in session state
if 'data' not in st.session_state:
    data = pd.read_csv("final/data/dfMerged.csv")
    data['usage_date'] = pd.to_datetime(data['usage_date'])
    st.session_state.data = data
else:
    data = st.session_state.data

# st.sidebar.title('Social Data Analysis | Solar Energy Project')
# st.sidebar.write("Welcome to the Solar Energy Project. This project aims to analyze solar energy data from the danish company EasyGreen.")
# st.sidebar.write("Please filter the data from the sidebar and the plots will apply your filters on change.")

# test, logo, _ = st.sidebar.columns([0.5, 1, 0.5])

# with logo:
#     st.image('dtuLogo.png', width=150)

st.write('')

viz = st.sidebar.selectbox("Select visualization", ["Solar Energy Data in Denmark", "EasyGreen Map Data", "EasyGreen Production Development"])

# st.dataframe(data)

if viz == "Solar Energy Data in Denmark":
    # Integrafe html plot
    st.title("General Solar Energy Data in Denmark")
    st.write('')
    #st.header("")
    
    # Google Data
    googleData = pd.read_csv('final/data/multiTimeline.csv', header=1)
    googleData['Week'] = googleData['Uge']
    googleData['Week'] = pd.to_datetime(googleData['Week'], format='%Y-%m-%d')
    googleData['Index'] = googleData['Solcelle: (Danmark)'].astype(float)

    # Energinet Data
    energinetData = pd.read_csv('final/data/energinetForecast.csv', sep=';', error_bad_lines=False, usecols=['HourDK', 'ForecastCurrent'])    
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

    st.subheader("Production from Solar Power in Denmark per week")
    st.line_chart(energinetData, x = 'Week', y = 'Production (MWh per hour)', color='#228B22')
    st.subheader("Accumulated Production from Solar Power in Denmark")
    st.line_chart(energinetData, x = 'Week', y = 'Accumulated Production (MWh per hour)', color='#228B22')
    st.subheader("Google Searches for Solar Power in Denmark per week")
    st.line_chart(googleData, x = 'Week', y = 'Index')

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
    data = data.dropna(subset=['latitude', 'longitude'])

    # Sort by usage_date
    data = data.sort_values(by='usage_date')

    # Filters

    ## example return (datetime.date(2024, 1, 31), datetime.date(2024, 3, 28))
    selected_date_range = st.sidebar.date_input("Select date", value=(data['usage_date'].min(), data['usage_date'].max()), min_value=data['usage_date'].min(), max_value=data['usage_date'].max())
    selected_date_range = pd.to_datetime(selected_date_range)

    if len(selected_date_range.unique()) < 2:
        st.spinner('Please select a date range of at least two different dates.')
    else:
        data = data[(data['usage_date'] >= selected_date_range[0]) & (data['usage_date'] <= selected_date_range[1])]

    ## Age range
    age_range = st.sidebar.slider("Select age range", 0, 100, (0, 100))
    data = data[(data['age'] >= age_range[0]) & (data['age'] <= age_range [1])]

    ## Production range
    production_range = st.sidebar.slider("Select production range", 0, 10000, (0, 10000))
    data = data[(data['totalProductPower'] >= production_range[0]) & (data['totalProductPower'] <= production_range[1])]

    data.reset_index(inplace=True)

    ## Color by
    elevation = st.sidebar.radio("Analyze by", ('Average Production', 'Average Utilized Production', 'Age'))
    
    if elevation == 'Average Production':
        elevation_weight = 'totalProductPower'
    elif elevation == 'Average Utilized Production':
        elevation_weight = 'totalSelfUsePower'
    elif elevation == 'Age':
        elevation_weight = 'age'

    # Add more colors?

    max_range = int(data['totalProductPower'].max())

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
        longitude=10.38831, latitude=55.79594, zoom=6.2, min_zoom=5, max_zoom=11 if elevation_weight != 'age' else 7, pitch=41 if elevation_weight != 'age' else 0, bearing=20 if elevation_weight != 'age' else 0, height=1000
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

    st.header("Production Analysis")
    st.subheader("The plot below shows the production of EasyGreen's customers over time.")

    # Create a barchart for production from the column "totalProductPower". x-axis: usage_month, y-axis: mean of totalProductPower
    data['usage_month'] = data['usage_date'].dt.strftime('%m')
    data['totalProductPower'] = data['totalProductPower'].astype(float)
    data['totalProductPower'] = data['totalProductPower'].apply(lambda x: x if x > 0 else 0)
    data['totalProductPower'] = data['totalProductPower'].apply(lambda x: x if x < 10000 else 0)

    # Plot the barchart
    production_data = data.groupby('usage_month')['totalProductPower'].mean()
    st.bar_chart(production_data)




# st.sidebar.write('---')
# st.sidebar.write("This project was created in the 02806 Social data analysis and visualization course at DTU. The group consists of the following members:")
# st.sidebar.write(" * Shakir Maytham Shaker")
# st.sidebar.write(" * Magnus Mac Doberenz")
# st.sidebar.write(" * Yili Ge")
# st.sidebar.download_button("Download Complete Notebook", open("../final/explainer.ipynb").read(), 'SolarEnergyProject.ipynb')