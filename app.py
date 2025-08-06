import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Amazon Listing Visualizer", layout="wide")

st.title("🖍️ Amazon Listing Visualizer mit Keyword-Highlighting")
st.markdown("Lade eine Excel-Datei hoch mit Amazon-Content und Keywords in **einer Datei**.")

# Datei-Upload
uploaded_file = st.file_uploader("📁 Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Sicherstellen, dass Spalten korrekt benannt sind
    expected_columns = ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms', 'Keywords']
    if not all(col in df.columns for col in expected_columns):
        st.error("❌ Die Datei muss folgende Spalten enthalten: " + ", ".join(expected_columns))
    else:
        def highlight_keywords(text, keywords):
            if not isinstance(text, str):
                return "", 0
            byte_count = len(text.encode("utf-8"))
            for kw in sorted(keywords, key=len, reverse=True):
                kw_escaped = re.escape(kw)
                pattern = re.compile(f"(?i)({kw_escaped})")
                text = pattern.sub(r'<span style="background-color:#ffeb3b">\1</span>', text)
            return text, byte_count

        for idx, row in df.iterrows():
            st.markdown(f"## 📝 Listing {idx + 1}")

            keywords = str(row['Keywords']).lower().split(",")
            keywords = [kw.strip() for kw in keywords if kw.strip()]

            for section in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
                raw_text = row.get(section, "")
                highlighted, byte_len = highlight_keywords(str(raw_text), keywords)

                st.markdown(f"**{section}** ({byte_len} Bytes):", unsafe_allow_html=True)
                st.markdown(f"<div style='border:1px solid #ccc; padding:10px; border-radius:5px'>{highlighted}</div>", unsafe_allow_html=True)
                st.markdown("---")
