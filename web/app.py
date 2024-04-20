import streamlit as st

def main():
    st.title('Hello, Streamlit!')

    menu = ["Home", "About"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        # Your code goes here

    elif choice == "About":
        st.subheader("About")
        # Your code goes here

if __name__ == "__main__":
    main()