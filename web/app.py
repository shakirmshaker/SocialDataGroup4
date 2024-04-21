import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Social Data Analysis | Solar Energy Project",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="auto",
)

data = pd.read_csv("../final/data/dfMerged.csv")
data['usage_date'] = pd.to_datetime(data['usage_date'])

st.sidebar.title('Social Data Analysis | Solar Energy Project')
st.sidebar.write("Welcome to the Solar Energy Project. This project aims to analyze solar energy data from the danish company EasyGreen.")
st.sidebar.write("Please filter the data from the sidebar and the plots will apply your filters on change.")

viz = st.sidebar.selectbox("Select visualization", ["Geographical Development", "Production Development"])

st.dataframe(data)

## Map plot

if viz == "Geographical Development":
    st.header("Geo Development") 
    st.subheader("The map below shows the development of EasyGreen's customers over time.")

    # Find customer installation date
    idx = data.groupby('user_id')['usage_date'].idxmin()
    first_usage_df = data.loc[idx]
    first_usage_df = first_usage_df.dropna(subset=['latitude', 'longitude'])
    first_usage_df['month_year'] = first_usage_df['usage_date'].dt.strftime('%m-%Y')
    df_sorted = first_usage_df.sort_values(by='usage_date')

    # Filters

    # Color picker
    color = st.sidebar.color_picker('Pick a color', '#008000')

    # Select Month-Year slider
    sorted_month_year_options = df_sorted['month_year'].unique()
    selected_month_year = st.sidebar.select_slider("Select customers up to date", options=sorted_month_year_options, value=sorted_month_year_options[-1])
    selected_date = pd.to_datetime(selected_month_year, format='%m-%Y')
    filtered_date_df_unique = first_usage_df[first_usage_df['usage_date'] <= selected_date]

    # Adjust sizes of the points

    st.map(filtered_date_df_unique, color=color)

    # Heat map for production

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




st.sidebar.write('---')
st.sidebar.write("This project was created in the 02806 Social data analysis and visualization course at DTU. The group consists of the following members:")
st.sidebar.write(" * Shakir Maytham Shaker")
st.sidebar.write(" * Magnus Mac Doberenz")
st.sidebar.write(" * Yili Ge")
st.sidebar.download_button("Download Complete Notebook", open("../final/explainer.ipynb").read(), 'SolarEnergyProject.ipynb')