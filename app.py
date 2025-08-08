
import streamlit as st
import pandas as pd

st.title("Amazon Listing Editor")

# Beispielhafte Felder für ein Listing
fields = ["Title", "Bullet1", "Bullet2", "Bullet3", "Bullet4", "Bullet5", "Description", "Search Terms"]

listings = []

uploaded_file = st.file_uploader("Upload Excel-Datei", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Datei erfolgreich geladen.")
    for idx, row in df.iterrows():
        listing = {}
        st.subheader(f"Listing {idx + 1}")
        for field in fields:
            listing[field] = st.text_input(f"{field} für Listing {idx + 1}", value=row.get(field, ""), key=f"{field}_{idx}")
        listings.append(listing)

if listings:
    result_df = pd.DataFrame(listings)
    try:
        output = result_df.to_excel(index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Fehler beim Exportieren: {e}")
