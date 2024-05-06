import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
import pydeck as pdk
import altair as alt
import os


st.set_page_config(
    page_title="Social Data Analysis | Solar Energy Project",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="auto",
)

# list of files in the directory
# st.write(os.getcwd())
# st.write(os.listdir())

# change working directory to SocialDataGroup4/web if not already
if 'web' not in os.getcwd():
    os.chdir('web')

# read only data if it is not in session state
if 'data' not in st.session_state:
    data = pd.read_csv("../final/data/dfMerged.csv")
    data['usage_date'] = pd.to_datetime(data['usage_date'])
    
    df_age=pd.read_csv('../final/data/user_id-age.csv',sep=';')
    df_age.rename(columns={'Kunde ID':'user_id','Fødselsdato':'birth_date'},inplace=True)
    df_age['birth_date']=pd.to_datetime(df_age['birth_date'], errors='coerce',format='%d/%m/%Y')
    df_age['age']=2024-df_age['birth_date'].dt.year

    data.drop(columns=['age'],inplace=True)
    data=pd.merge(data,df_age[['user_id','age']],on='user_id',how='left')

    #remove outliers
    data=data[(data.totalUsePower<500) & (data.totalProductPower<500) & (data.totalSelfUsePower<500) & (data.totalBuyPower<500)]
    data=data[(data.age>=18) & (data.age<=99)]
    # remove max value from data['totalUsePower']

    # usePowerMax = data['totalUsePower'].max()
    # data['totalUsePower'] = data['totalUsePower'].apply(lambda x: x if x < usePowerMax else 0)

    st.session_state.data = data
else:
    data = st.session_state.data


st.sidebar.image('images/dtuLogo.png')

# st.sidebar.title('Social Data Analysis')
# st.sidebar.write("Welcome to the Solar Energy Project. This project aims to analyze solar energy data from the Danish company EasyGreen.")
#st.sidebar.write("Please filter the data from the sidebar and the plots will apply your filters on change.")

st.write('')

viz = st.sidebar.selectbox("Select page", ["Home","Solar Energy Data in Denmark", "EasyGreen Geospatial Data", "EasyGreen Production Development","Summary and Conclusions","Sources"])

if viz=="Home":
    st.title("Course 02806 | Analysis of Solar Energy Usage and Production in Denmark")
    st.write("Welcome to our Solar Energy Project. Here, we delve into the fascinating world of solar power production and usage in Denmark. Please select the page you wish to explore on the sidebar to the left. There, you can also filter the data to customize your analysis.")
    st.write('')
    st.write("Our project is organized into three primary sections. The first section deals with total solar energy production and demand in Denmark in the context of rising gas prices. The second and third section are both based on data from the private solar energy company “EasyGreen”. Their dataset contains information on daily electricity usage and production on a household level. Geospatial visualizations as well as comparisons of production and self-usage can be explored. Subsequently, the main findings of the comparative analysis are summarized.")
    st.write('')
    st.image('images/houses_solar_panels.jpeg',width=500)
    st.caption("Figure 1: Image created using Microsoft Copilot with the prompt Houses with solar panels")
if viz == "Solar Energy Data in Denmark":
    # Integrafe html plot
    st.title("An Introduction to the Danish Solar Power Landscape")
    st.write('')
    st.write("Solar energy as a renewable source of power production has become increasingly prominent and relevant in Denmark. Not only efforts to slow down catastrophic climate change, but also recent geopolitical events such as the war in Ukraine leading to a shortage of natural gas in many European countries have moved many Danish households to consider installing solar panels on their rooftops.")
    st.write('')
    st.write("Therefore, this section investigates the usage of and demand for solar energy, as well as the influence of rising gas prices.")
    #st.header("")
    
    # Google Data
    googleData = pd.read_csv('../final/data/multiTimeline.csv', header=1)
    googleData['Week'] = googleData['Uge']
    googleData['Week'] = pd.to_datetime(googleData['Week'], format='%Y-%m-%d')
    googleData['Index'] = googleData['Solcelle: (Danmark)'].astype(float)

    # Energinet Data
    energinetData = pd.read_csv('../final/data/energinetForecast.csv', sep=';', usecols=['HourDK', 'ForecastCurrent'])    
    energinetData['HourDK'] = pd.to_datetime(energinetData['HourDK'])
    energinetData['Production (MWh per hour)'] = energinetData['ForecastCurrent'].str.replace(',', '.').astype(float)    
    
    energinetData.set_index('HourDK', inplace=True)
    energinetData = energinetData.resample('W').agg({'Production (MWh per hour)': 'sum'}).reset_index()
    energinetData.rename(columns={'HourDK': 'Week'}, inplace=True)

    # Gas Prices Data. Source: https://ens.dk/service/statistik-data-noegletal-og-kort/priser-paa-el-og-gas
    gasPrices = pd.read_csv('../final/data/gasPrices.csv', sep=',')
    gasPrices['Date'] = pd.to_datetime(gasPrices['month'], format='%YM%m')
    gasPrices['Price DKK/GJ'] = gasPrices['price kr/GJ']

    # Start date from energinetData minimum date
    startDate = energinetData['Week'].min()
    gasPrices = gasPrices[gasPrices['Date'] >= startDate]    

    # Sort by 'Week'
    energinetData = energinetData.sort_values(by='Week')

    # set minimum date to match in both dataframes. Use the maximum of the two minimum dates
    minDate = max(energinetData['Week'].min(), googleData['Week'].min())
    energinetData = energinetData[energinetData['Week'] >= minDate]
    googleData = googleData[googleData['Week'] >= minDate]        

    # accumulate the forecast data
    energinetData['Accumulated Production (MWh per hour)'] = energinetData['Production (MWh per hour)'].cumsum()

    # Filters
    dateRange = st.sidebar.date_input("Filter data by date range", value=(energinetData['Week'].min(), energinetData['Week'].max()), min_value=energinetData['Week'].min(), max_value=energinetData['Week'].max())
    
    # help: source https://www.energidataservice.dk/tso-electricity/Forecasts_Hour
    st.subheader("Denmark's Solar Power Surge and Seasonal Trends in Response to Rising Gas Prices")    
    st.write('This time series graph portrays the solar power production in Denmark from 2020 through April 2024 in MWh per hour. The data exhibits clear seasonality, with production escalating in summer due to more sunlight and receding in winter. Interestingly, before the pronounced production dip at the end of 2023, there\'s an exceptional peak surpassing other summer highs. This peak corresponds to a dramatic hike in gas prices in the winter 2022, reaching 27 kr per m³ in its highest, prompting increased dependency on solar energy. Additionally, the early onset of the 2024 summer production peak suggests an acceleration in solar investments by private households and others, resulting in a more substantial and earlier increase in solar power generation.')

    showPeaks = st.checkbox('Highlight Peaks', value=False, key='showPeaks')

    energinetData['Date'] = energinetData['Week'].dt.date
    googleData['Date'] = googleData['Week'].dt.date
    gasPrices['Date'] = gasPrices['Date'].dt.date

    if len(dateRange) < 2:
        st.spinner('Please select a date range of at least two different dates.')
    else:
        energinetData = energinetData[(energinetData['Date'] >= dateRange[0]) & (energinetData['Date'] <= dateRange[1])]
        googleData = googleData[(googleData['Date'] >= dateRange[0]) & (googleData['Date'] <= dateRange[1])]
        gasPrices = gasPrices[(gasPrices['Date'] >= dateRange[0]) & (gasPrices['Date'] <= dateRange[1])]

    energinetData['Above_15000'] = energinetData['Production (MWh per hour)'] > 15000
    energinetData['Segment'] = energinetData['Above_15000'].astype(int).diff().ne(0).cumsum()
    df_endpoints = energinetData.copy()
    df_endpoints['Date'] = df_endpoints['Date'].shift(-1)
    df_endpoints['Production (MWh per hour)'] = df_endpoints['Production (MWh per hour)'].shift(-1)
    df_final = pd.concat([energinetData, df_endpoints]).sort_values(by=['Date', 'Segment']).dropna()
    base = alt.Chart(df_final).encode(
        x='Week:O',  # Ordinal data
        y='Production (MWh per hour):Q',  # Quantitative data
        detail='Segment:N'  # Use segment number as detail to differentiate lines
    )
    lines = base.mark_line().encode(
        x=alt.X('Date:T'), 
        color=alt.condition(
            alt.datum.Above_15000,
            alt.value('lightgreen' if showPeaks else 'green'),  # True color
            alt.value('green')  # False color
        )
    )
    st.altair_chart(lines, use_container_width=True)
    st.caption("Figure 2: Total solar power production in Denmark [MWh/hour]")


    # The following plot is does not contain any new information

    # st.subheader("Denmark's Solar Energy Growth: Accelerated Accumulation Amidst Gas Price Surge and Solar Investments")
    # st.write("The accumulated solar power production curve for Denmark, from 2020 to April 2024, shows a steady climb in megawatt-hours. The rate of accumulation notably spikes in 2023, reflecting a response to a surge in gas prices and an increase in solar investments. Entering 2024, the earlier rise in the curve indicates a stronger and earlier seasonal peak, suggesting an expansion in solar capacity due to new installations by private households and other contributors.")

    # st.altair_chart(alt.Chart(energinetData).mark_line(color='#228B22').encode(
    #     x='Date',
    #     y='Accumulated Production (MWh per hour)'
    # ).properties(
    #     width='container'
    # ), use_container_width=True)





    # help: source https://trends.google.com/trends/explore?date=today%205-y&geo=DK&q=%2Fm%2F078kl
    st.subheader("Google Trends: Solar Power Search Interest in Denmark")
    st.write('This Google Trends graph tracks the search interest for solar power in Denmark from 2020 to April 2024. It shows a variable interest level over the years, with a significant spike in the winter of 2022. This spike correlates with the substantial increase in gas prices during that period, which likely prompted the public to explore solar power as an alternative. Following this heightened interest, solar power production peaked in the summer of 2023, suggesting a direct link between search behavior and actual adoption of solar solutions. The graph indicates that as gas prices escalated, Danish citizens turned to online searches to inform decisions on solar energy investments.')
    showGasPrice = st.checkbox('Show Gas Prices', value=False, key='showGasPrices')
    # Create a chart with two y-axes 

    googleData['Date'] = pd.to_datetime(googleData['Date'])
    gasPrices['Date'] = pd.to_datetime(gasPrices['Date'])
    date_range = pd.date_range(start=googleData['Date'].min(), end=googleData['Date'].max())
    date_df = pd.DataFrame(date_range, columns=['Date'])
    googleData = pd.merge(date_df, googleData, on='Date', how='outer')
    gasPrices = pd.merge(date_df, gasPrices, on='Date', how='outer')
    googleData['Index'] = googleData['Index'].interpolate(method='linear')
    gasPrices['Price DKK/GJ'] = gasPrices['Price DKK/GJ'].interpolate(method='linear')
    mergedData = pd.merge(googleData, gasPrices, on='Date', how='outer')

    # Base chart
    base = alt.Chart(mergedData).encode(
        alt.X('Date:T')
    )

    # First line chart
    line1 = base.mark_line(color='blue').encode(
        alt.Y('Index', axis=alt.Axis(title='Index', titleColor='blue'))
    )

    # Second line chart
    line2 = base.mark_line(color='red').encode(
        alt.Y('Price DKK/GJ', axis=alt.Axis(title='Price DKK/GJ', titleColor='red', grid=True))
    )

    
    chart = alt.layer(line1, line2).resolve_scale(y='independent')

    if showGasPrice:
        st.altair_chart(chart, use_container_width=True)
    else:
        st.altair_chart(line1, use_container_width=True)

    st.caption("Figure 3: Solar power search interest and gas prices in Denmark")

## Map plot

if viz == "EasyGreen Geospatial Data":
    st.title("EasyGreen Geospatial Data")     

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

    # ## Age range
    # age_range = st.sidebar.slider("Filter map by customer age range", 0, 100, (0, 100))
    # data = data[(data['age'] >= age_range[0]) & (data['age'] <= age_range [1])]

    ## Age groups
    age_groups=st.sidebar.multiselect("Filter map by age groups", ["18-44","45-53","54-63","64-99"])
    age_group_ind=[(data.age>17) & (data.age<=44),
                    (data.age>44) & (data.age<=53),
                    (data.age>53) & (data.age<=64),
                    (data.age>64) & (data.age<=99)]
    
    if len(age_groups)>0:

        age_data=data[data.index<0]
        for i,age_group in enumerate(age_groups):
            if age_group:
                age_data=pd.concat([age_data,data[age_group_ind[i]]])
        data=age_data.copy()

    ## Production range
    max_range = int(data['totalProductPower'].max())
    production_range = st.sidebar.slider("Filter map by daily production range", 0, max_range, (0, max_range))
    data = data[(data['totalProductPower'] >= production_range[0]) & (data['totalProductPower'] <= production_range[1])]

    data.reset_index(inplace=True)

    elevation = st.sidebar.radio("Analyze Map By", ('Average Production Per Day','Average Utilized Production Per Day', 'Age'))
    
    if elevation == 'Average Production Per Day':
        elevation_weight = 'totalProductPower'
    elif elevation == 'Average Utilized Production Per Day':
        elevation_weight = 'totalSelfUsePower'
    elif elevation == 'Age':
        elevation_weight = 'age'
    
    if elevation == 'Average Production Per Day':
        st.subheader("Visualization of Solar Power Production by EasyGreen Customers Across Denmark")
        st.write('')
        st.write("One way to represent data provided by EasyGreen is to spatially visualize the solar power production of their customers across Denmark. The age group and location of each household are provided and allow for a detailed analysis. Feel free to explore the data by adjusting the sliders on the sidebar.")
        st.write('The plot displays a 3D hexagonal bin map visualization centered over Denmark, highlighting solar power production data for EasyGreen\'s customers. Each hexagonal column represents the geographic clustering of customers, and the height of the columns is proportional to the average daily solar power production. The highest solar power outputs are indicated by the tallest columns, color-coded in red and orange. The map provides geographic and quantitative insights into solar power distribution among EasyGreen\'s customer base.')
    elif elevation == 'Age':
        st.subheader("Visualization of EasyGreen's Customer Age Distribution Across Denmark")
        st.write('The plot displays a heatmap distribution of EasyGreen\'s customers across Denmark, color-coded by age. The most concentrated areas with the oldest customer base are shown in red, with decreasing age groups represented by cooler colors, yellow to white. The densest area of older customers is located in the eastern part of Denmark. The heatmap settings have been configured to restrict zooming capabilities to safeguard privacy, ensuring individual customer data cannot be discerned, allowing only a macro view of the age distribution.')


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
        #longitude=10.38831, latitude=55.79594, zoom=6.2, min_zoom=5, max_zoom=11 if elevation_weight != 'age' else 7, pitch=41 if elevation_weight != 'age' else 0, bearing=20 if elevation_weight != 'age' else 0, height=700
        longitude=10.38831, latitude=55.79594, zoom=6.2, min_zoom=5, max_zoom=11 if elevation_weight != 'age' else 7, pitch=41 if elevation_weight != 'age' else 0, height=700
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
    st.caption("Figure 4: Geospatial distribution of EasyGreen's customers based on solar power production and age")

# Accumulated production per month

if viz == "EasyGreen Production Development":

    ## Production

    st.title("Energy Dynamics: Comparing Production and Usage")
    st.write("The EasyGreen dataset contains several intriguing features related to solar energy. These include daily solar power production, self-used electricity generated by solar panels, and total electricity consumption in individual households. These measurements help us better understand the interplay between solar energy production and usage within private homes. The following interactive figures provide a more detailed visualization of this relationship.")
    st.subheader("EasyGreen's Solar Power Production and Utilization")
    st.write("The bar chart presents the average solar power production per month for EasyGreen's customers, measured in kWh/day. Each bar corresponds to a month, with its total height reflecting the average daily production and the darker green portion indicating the average utilized production. There is a clear seasonal trend, with the highest production occurring in the summer months, peaking in July, and the lowest in December, showcasing the variance in solar power generation and utilization throughout the year.")
    st.write('')

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
        y=alt.Y('totalProductPower:Q', title='Production in kWh per day'),  # Specify quantitative data with :Q
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
            y=alt.Y('totalUsePower:Q', title= 'Usage in kWh per day'),
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
    st.caption("Figure 5: Average monthly solar power production (and utilized production) in kWh/day")

    st.subheader('Day and Night Electricity Usage')
    st.write('The bar chart represents the average daily electricity usage at home, measured in kWh, for each month. Each bar reflects the total average consumption per day within the respective month. Usage is highest in January and decreases through to the warmer months, with the lowest consumption in June, and then rises again towards the end of the year, with December showing a significant increase, suggesting seasonal influences on electricity demand among households.')    
    st.write('')
    st.altair_chart(use_chart+nightUsage_chart if showNightUsage else use_chart, use_container_width=True)
    st.caption("Figure 6: Average monthly electricity usage (and night usage) per month in kWh/day")

if viz == "Summary and Conclusions":
    st.title("Summary and Conclusions")
    
    # st.write("The analysis of solar power production and usage data in Denmark provides valuable insights into the country's energy dynamics, customer distribution, and response to gas market fluctuations. The project delves into the seasonal trends in solar power generation, highlighting the peak production months and the corresponding dip in winter. The data also reveals a direct correlation between the surge in gas prices and the increased interest in solar power solutions among Danish citizens, leading to a rise in solar investments and production.")
    # st.write('')
    # st.write("The geospatial analysis of EasyGreen's customer data showcases the distribution of solar power production and customer age across Denmark. The 3D hexagonal bin map visualizes the clustering of customers based on their solar power production, providing insights into the geographic concentration of solar energy generation. The heatmap representation of customer age distribution reveals the age demographics of EasyGreen's customers, with the eastern part of Denmark showing a higher concentration of older customers.")
    # st.write('')
    # st.write("The monthly production and usage analysis demonstrates the seasonal trends in solar power generation and electricity consumption. The bar charts display the average daily solar power production, utilized production, and electricity usage per month, highlighting the fluctuations in solar power generation and consumption throughout the year. The data indicates a direct relationship between solar power production and electricity usage, with the highest production and consumption occurring in the winter months.")
    # st.write('')
    # st.write("In conclusion, the project provides a comprehensive analysis of solar power dynamics in Denmark, offering insights into solar energy production, customer distribution, and energy usage. The findings underscore the importance of solar power as a sustainable energy source and its potential to mitigate the impact of rising gas prices. The project aims to inform policymakers, energy companies, and the public about the benefits of solar energy and the need for increased investments in renewable energy solutions.")
    # st.write('')

if viz == "Sources":
    st.title("Sources")
    st.write("The data used in this project was provided by EasyGreen, a Danish company specializing in solar energy solutions. The project utilized solar power production and usage data, as well as geospatial data on EasyGreen's customers, to analyze solar energy dynamics in Denmark.")
    st.write('')
    st.write("The project also incorporated data from Energiedataservie, Energistyrelsen and Google Trends. Please see the following links for more information.")
    st.write('')
    st.write("https://www.energidataservice.dk/tso-electricity/Forecasts_Hour")
    st.write('')
    st.write("https://ens.dk/service/statistik-data-noegletal-og-kort/priser-paa-el-og-gas")
    st.write('')
    st.write("https://trends.google.com/trends/explore?date=today%205-y&geo=DK&q=%2Fm%2F078kl")
st.sidebar.write('---')



st.sidebar.write("This project was created in the 02806 Social data analysis and visualization course at DTU. The group consists of the following members:")
st.sidebar.write(" * Shakir Maytham Shaker")
st.sidebar.write(" * Magnus Mac Doberenz")
st.sidebar.write(" * Yili Ge")
st.sidebar.download_button("Download Complete Notebook", open("../final/explainer.ipynb").read(), 'SolarEnergyProject.ipynb')
