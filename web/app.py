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

st.sidebar.title('Social Data Analysis | Solar Energy Project')
st.sidebar.write("Welcome to the Solar Energy Project. This project aims to analyze solar energy data from the danish company EasyGreen.")
st.sidebar.write("Please select the data you would like to analyze from the sidebar.")

choice = st.sidebar.selectbox("Visualization", ["Geo Development", "Production Development", "Social Data Analysis"])

# create day, month, year columns from usage_date
data['usage_date'] = pd.to_datetime(data['usage_date'])
data['day'] = data['usage_date'].dt.day
data['month'] = data['usage_date'].dt.month
data['year'] = data['usage_date'].dt.year

if choice == "Geo Development":

    st.header("Geo Development")  
    
    idx = data.groupby('user_id')['usage_date'].idxmin()
    first_usage_df = data.loc[idx]
    first_usage_df = first_usage_df.dropna(subset=['latitude', 'longitude'])

    first_usage_df['month_year'] = first_usage_df['usage_date'].dt.strftime('%m-%Y')
    df_sorted = first_usage_df.sort_values(by='usage_date')
    sorted_month_year_options = df_sorted['month_year'].unique()

    selected_month_year = st.sidebar.select_slider("Select Month-Year", options=sorted_month_year_options, format_func=lambda x: x)

    selected_date = pd.to_datetime(selected_month_year, format='%m-%Y')

    # Filter DataFrame to only include rows with date less than or equal to selected date
    filtered_df = first_usage_df[first_usage_df['usage_date'] <= selected_date]
    
    st.map(filtered_df)


st.sidebar.download_button("Download Complete Notebook", open("../final/explainer.ipynb").read(), 'SolarEnergyProject.ipynb')

# read notebook into streamlit
# st.write("Notebook")