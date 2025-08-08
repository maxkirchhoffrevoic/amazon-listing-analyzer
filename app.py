
import streamlit as st
import pandas as pd
import base64
import re

st.set_page_config(layout="wide")

st.markdown("""
<style>
    .block-container {padding-right: 2rem !important;}
    .listing-container {width: 100%; max-width: 1000px;}
    .field-title {font-weight: bold; font-size: 1.1rem; margin-bottom: 0.2rem;}
    .byte-count {font-size: 0.8rem; color: grey; margin-bottom: 0.5rem;}
    .over-limit {color: red;}
    .keyword-highlight { background-color: yellow; font-weight: bold; }
    .listing-header {font-size: 1.4rem; font-weight: 700; margin-top: 2rem;}
    .expander-header {font-size: 1.2rem;}
</style>
""", unsafe_allow_html=True)

st.title("📦 Amazon Listing Editor mit Excel-Upload und -Download")

uploaded_file = st.file_uploader("📤 Excel mit Listings und Keywords hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.fillna("", inplace=True)

    # Funktion zur Byte-Berechnung
    def count_bytes(text):
        return len(text.encode("utf-8"))

    # Funktion zur Hervorhebung von Keywords
    def highlight_keywords(text, keywords):
        for kw in sorted(keywords, key=len, reverse=True):
            pattern = r'(?i)(?<!\w)(' + re.escape(kw.strip()) + r')(?!\w)'
            text = re.sub(pattern, r'<span class="keyword-highlight">\1</span>', text)
        return text

    new_data = []

    for idx, row in df.iterrows():
        with st.expander(f"📦 Listing {idx + 1} – einklappen/ausklappen", expanded=False):
            st.markdown('<div class="listing-container">', unsafe_allow_html=True)

            # KEYWORDS
            st.markdown(f'<div class="field-title">✏️ Keywords für Listing {idx+1}</div>', unsafe_allow_html=True)
            keyword_str = st.text_area("Keywords (durch Komma getrennt)", row.get("Keywords", ""), key=f"kw_{idx}")
            keywords = [k.strip() for k in keyword_str.split(",") if k.strip()]

            listing_fields = {
                "Titel": {"value": row.get("Titel", ""), "limit": 150},
                "Bullet1": {"value": row.get("Bullet1", ""), "limit": 200},
                "Bullet2": {"value": row.get("Bullet2", ""), "limit": 200},
                "Bullet3": {"value": row.get("Bullet3", ""), "limit": 200},
                "Bullet4": {"value": row.get("Bullet4", ""), "limit": 200},
                "Bullet5": {"value": row.get("Bullet5", ""), "limit": 200},
                "Description": {"value": row.get("Description", ""), "limit": 2000},
                "Search Terms": {"value": row.get("Search Terms", ""), "limit": 250},
            }

            edited = {}

            for field, info in listing_fields.items():
                content = st.text_area(f"{field}", info["value"], key=f"{field}_{idx}", height=100)
                byte_len = count_bytes(content)
                byte_limit = info["limit"]
                is_over = byte_len > byte_limit

                byte_text = f"{byte_len} / {byte_limit} Bytes"
                byte_class = "byte-count over-limit" if is_over else "byte-count"
                st.markdown(f'<div class="{byte_class}">📏 {byte_text}</div>', unsafe_allow_html=True)

                # Vorschau mit Keyword-Highlight
                highlighted = highlight_keywords(content, keywords)
                st.markdown(highlighted, unsafe_allow_html=True)

                edited[field] = content

            edited["Keywords"] = keyword_str
            new_data.append(edited)

            st.markdown("</div>", unsafe_allow_html=True)

    # Download-Funktion
    st.markdown("---")
    st.subheader("📥 Download aktualisierte Listings")

    result_df = pd.DataFrame(new_data)
    output = result_df.to_excel(index=False, engine='openpyxl')
    b64 = base64.b64encode(output).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="updated_listings.xlsx">📥 Download Excel-Datei</a>'
    st.markdown(href, unsafe_allow_html=True)
