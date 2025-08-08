
import streamlit as st
import pandas as pd
import base64
import uuid

st.set_page_config(layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-right: 2rem !important;
        padding-left: 2rem !important;
    }
    .listing-container {
        width: 100%;
        max-width: 1100px;
        margin: auto;
    }
    .field-label {
        font-weight: 600;
        font-size: 1rem;
        margin-top: 1rem;
        margin-bottom: 0.3rem;
    }
    .byte-count {
        font-size: 0.75rem;
        color: #999;
        margin-bottom: 0.5rem;
    }
    .over-limit {
        color: red !important;
    }
    .highlight {
        background-color: yellow;
        font-weight: bold;
    }
    .stTextArea textarea {
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Amazon Listing Editor mit WYSIWYG-Highlighting, Byte-Zähler & Keyword-Analyse")

def byte_len(text):
    return len(text.encode('utf-8'))

def highlight_keywords(text, keywords):
    for kw in sorted(keywords, key=len, reverse=True):
        text = text.replace(kw, f'<span class="highlight">{kw}</span>')
    return text

# Default Test DataFrame
df = pd.DataFrame([{
    "Titel": "Kurze Brotdose Brotdox wdkaokdoaslkldsklaksdkalkösdalködsalkdlf",
    "Bullet1": "BPA-frei",
    "Bullet2": "Praktisch",
    "Bullet3": "Robust",
    "Bullet4": "",
    "Bullet5": "",
    "Description": "Diese Brotdose ist kompakt, leicht und bpa-frei. Sie passt in jede Tasche.",
    "SearchTerms": "edelstahl, brotdose, kompakt",
    "Keywords": "brotdox, edelstahl, bpa-frei, kompakt, leicht, robust"
}])

# Listing Container
for i, row in df.iterrows():
    with st.expander(f"📦 Listing {i+1} – einklappen/ausklappen", expanded=False):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown(f"### ✏️ Keywords für Listing {i+1}")
            keywords_text = st.text_area("Keywords (durch Komma getrennt)", row["Keywords"], key=f"kw_{i}")
            keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]

        with col2:
            st.markdown('<div class="listing-container">', unsafe_allow_html=True)

            def render_field(label, value, key, byte_limit):
                st.markdown(f'<div class="field-label">{label}</div>', unsafe_allow_html=True)
                text = st.text_area(f"{label}", value, key=key)
                byte_count = byte_len(text)
                byte_class = "byte-count over-limit" if byte_count > byte_limit else "byte-count"
                st.markdown(f'<div class="{byte_class}">Bytes: {byte_count} / {byte_limit}</div>', unsafe_allow_html=True)
                st.markdown(highlight_keywords(text, keywords), unsafe_allow_html=True)
                return text

            new_title = render_field("Titel", row["Titel"], f"title_{i}", 150)
            new_b1 = render_field("Bullet1", row["Bullet1"], f"b1_{i}", 200)
            new_b2 = render_field("Bullet2", row["Bullet2"], f"b2_{i}", 200)
            new_b3 = render_field("Bullet3", row["Bullet3"], f"b3_{i}", 200)
            new_b4 = render_field("Bullet4", row["Bullet4"], f"b4_{i}", 200)
            new_b5 = render_field("Bullet5", row["Bullet5"], f"b5_{i}", 200)
            new_desc = render_field("Description", row["Description"], f"desc_{i}", 2000)
            new_st = render_field("SearchTerms", row["SearchTerms"], f"st_{i}", 250)

            st.markdown("</div>", unsafe_allow_html=True)
