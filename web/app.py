import streamlit as st
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt

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

viz = st.sidebar.selectbox("Select visualization", ["Geographical Development", "Production Development"])

# st.dataframe(data)

## Map plot

if viz == "Geographical Development":
    st.header("Geo Development") 
    st.subheader("The map below shows the development of EasyGreen's customers over time.")


    # Group by user_id and get the first usage_date and sum of totalProductPower
    data = data.groupby('user_id').agg({'usage_date': 'min', 'totalProductPower': 'sum', 'latitude': 'mean',
                                                  'longitude': 'mean', 'age': 'mean'}).reset_index()
            
    
    # totalProductPower color
    cmap = plt.cm.get_cmap('Greens')
    norm = plt.Normalize(data['totalProductPower'].min(), data['totalProductPower'].max())
    data['colorProductPower'] = data['totalProductPower'].apply(lambda x: matplotlib.colors.rgb2hex(cmap(norm(x))))

    # age color
    cmap = plt.cm.get_cmap('Purples')
    norm = plt.Normalize(data['age'].min(), data['age'].max())
    data['colorAge'] = data['age'].apply(lambda x: matplotlib.colors.rgb2hex(cmap(norm(x))))

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

    data.reset_index(inplace=True)

    ## Color by
    color = st.sidebar.radio("Color by", ('None', 'Production', 'Age'))
    
    if color == 'Production':
        color = 'colorProductPower'
    elif color == 'Age':
        color = 'colorAge'
    else:
        color = '#7CFC00'

    # Adjust sizes of the points

    st.map(data, color=color)    

    if color == 'colorProductPower':
        st.image('greens.png', use_column_width=True, caption='Color scale for production: low --> high')
    elif color == 'colorAge':
        st.image('purples.png', use_column_width=True, caption='Color scale for age: young --> old')



    # TODO Create size and color column for the map plot▶️


    

# Accumulated production per month

if viz == "Production Development":

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