import streamlit as st

def main():
    st.title("Streamlit Django App")
    st.write("Hello, Streamlit!")

    if st.button("Click me"):
        st.write("Button clicked!")

if __name__ == "__main__":
    main()