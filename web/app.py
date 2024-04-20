import streamlit as st
import os

def main():
    st.write(os.getcwd())
    st.title('Hello, Streamlit!')

    menu = ["Home", "About", 'Test']
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        # Your code goes here

    elif choice == "About":
        st.subheader("About")
        # Your code goes here

if __name__ == "__main__":
    main()