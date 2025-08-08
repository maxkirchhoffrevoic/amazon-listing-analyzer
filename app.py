
import streamlit as st

# Beispielcode mit korrekter Einrückung
st.set_page_config(layout="wide")

with st.container():
    st.markdown("""
        <style>
        .block-container {
            padding-right: 2rem !important;
        }
        .listing-container {
            width: 100%;
            max-width: 1000px;
        }
        </style>
    """, unsafe_allow_html=True)
