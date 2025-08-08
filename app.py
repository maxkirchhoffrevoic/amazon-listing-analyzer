
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🧰 Amazon Listing Editor & Keyword Visualizer")

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

uploaded_file = st.file_uploader("Excel-Datei mit Listings hochladen", type=["xlsx"])
uploaded_keyword_file = st.file_uploader("Oder alternativ nur Keyword-Liste hochladen", type=["xlsx"], key="keywords_only")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Fehler beim Lesen der Excel-Datei: {e}")

elif uploaded_keyword_file:
    try:
        df = pd.read_excel(BytesIO(uploaded_keyword_file.read()))
        df.columns = ['Keywords']
        for col in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
            df[col] = ""
    except Exception as e:
        st.error(f"Fehler beim Lesen der Keyword-Datei: {e}")
