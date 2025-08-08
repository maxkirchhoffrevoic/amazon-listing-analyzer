
import streamlit as st
import pandas as pd
import re
from io import BytesIO
from openpyxl import Workbook

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-right: 2rem !important;
        }
        .listing-container {
            width: 100%;
            max-width: 1600px;
            margin: auto;
        }
        .keyword-highlight {
            background-color: yellow;
            font-weight: bold;
        }
        .used-keyword {
            background-color: lightgreen;
        }
        textarea {
            font-family: monospace;
        }
        .byte-info {
            font-size: 0.8em;
            color: grey;
            margin-bottom: 4px;
        }
        details {
            margin-bottom: 1rem;
        }
        summary {
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            outline: none;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Amazon Listing Editor mit Keyword-Erkennung & Byte-Zähler")

uploaded_file = st.file_uploader("📤 Excel-Datei mit Listings hochladen", type=["xlsx"])

def count_bytes(text):
    return len(text.encode('utf-8'))

def highlight_keywords(text, keywords):
    def replacer(match):
        return f'<span class="keyword-highlight">{match.group(0)}</span>'
    for kw in sorted(keywords, key=len, reverse=True):
        text = re.sub(rf"(?i)(?<!\w)({re.escape(kw)})(?!\w)", replacer, text)
    return text

def render_field(field_label, text, byte_limit, keywords, key):
    col1, col2 = st.columns([3, 5])
    with col1:
        edited = st.text_area(field_label, text, key=key)
        byte_count = count_bytes(edited)
        byte_color = "red" if byte_count > byte_limit else "grey"
        st.markdown(f'<div class="byte-info" style="color:{byte_color}">Bytes: {byte_count} / {byte_limit}</div>', unsafe_allow_html=True)
    with col2:
        highlighted = highlight_keywords(edited, keywords)
        st.markdown(f'<div style="border:1px solid #ccc; padding:10px;">{highlighted}</div>', unsafe_allow_html=True)
    return edited

if "listings" not in st.session_state:
    st.session_state.listings = []

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    for i, row in df.iterrows():
        listing_id = f"Listing {i+1}"
        keywords_raw = str(row.get("Keywords", ""))
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        used_keywords = set()

        with st.container():
            with st.expander(f"📦 {listing_id} – einklappen/ausklappen", expanded=False):
                st.markdown('<div class="listing-container">', unsafe_allow_html=True)
                col1, col2 = st.columns([2, 5])

                with col1:
                    st.markdown(f"#### 📝 Keywords für {listing_id}")
                    keyword_input = st.text_area("Keywords (durch Komma getrennt)", value=keywords_raw, key=f"kw_{i}")
                    keyword_list = [k.strip() for k in keyword_input.split(",") if k.strip()]
                    st.session_state.listings.append({"keywords": keyword_list})

                with col2:
                    updated_row = {}
                    for field, limit in [("Titel", 150), ("Bullet1", 200), ("Bullet2", 200), ("Bullet3", 200)]:
                        original_text = str(row.get(field, ""))
                        updated_text = render_field(field, original_text, limit, keyword_list, f"{field}_{i}")
                        updated_row[field] = updated_text
                        for kw in keyword_list:
                            if re.search(rf"(?i)(?<!\w){re.escape(kw)}(?!\w)", updated_text):
                                used_keywords.add(kw)

                highlighted_keywords = [
                    f'<span class="used-keyword">{kw}</span>' if kw in used_keywords else kw
                    for kw in keyword_list
                ]
                html_keywords = ", ".join(highlighted_keywords)
                st.markdown(f'<div style="font-size:0.9em;">Verwendete Keywords: {html_keywords}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 📥 Download aktualisierte Listings")
    result_df = pd.DataFrame([{
        "Keywords": ", ".join(l["keywords"]),
        **{f: st.session_state.get(f"{f}_{i}", "") for f in ["Titel", "Bullet1", "Bullet2", "Bullet3"]}
    } for i, l in enumerate(st.session_state.listings)])

    output = BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    st.download_button("📥 Excel herunterladen", data=output.getvalue(), file_name="aktualisierte_listings.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
