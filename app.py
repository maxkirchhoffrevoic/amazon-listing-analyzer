
import streamlit as st
import pandas as pd
import base64
import re

st.set_page_config(layout="wide")
st.title("🛠️ Amazon Listing Editor mit Keyword-Highlighting")

# Funktion zum Hervorheben von Keywords im Text
def highlight_keywords(text, keywords):
    if not text:
        return ""
    for kw in sorted(keywords, key=len, reverse=True):
        escaped_kw = re.escape(kw.strip())
        text = re.sub(f"(?i)({escaped_kw})", r'<mark>\1</mark>', text)
    return text

# Funktion zur Berechnung der Byte-Länge
def byte_length(text):
    return len(text.encode("utf-8"))

# Excel-Datei hochladen
uploaded_file = st.file_uploader("📤 Excel-Datei mit Listings hochladen", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    updated_rows = []

    # Durch alle Listings iterieren
    for i, row in df.iterrows():
        with st.expander(f"📦 Listing {i+1} – einklappen/ausklappen", expanded=False):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown(f"### ✏️ Keywords für Listing {i+1}")
                keywords_raw = st.text_area("Keywords (durch Komma getrennt)", row.get("Keywords", ""), key=f"kw_input_{i}")
                keywords = [kw.strip() for kw in keywords_raw.split(",") if kw.strip()]
                highlighted_list = []
                for kw in keywords:
                    color = "#d4edda" if any(re.search(rf"\b{re.escape(kw)}\b", str(row.get(field, "")), re.IGNORECASE) for field in ["Title", "Bullet1", "Bullet2", "Bullet3", "Bullet4", "Bullet5", "Description", "Search Terms"]) else "transparent"
                    highlighted_list.append(f"<span style='background-color:{color}; padding:2px 4px; border-radius:4px; display:inline-block; margin:2px'>{kw}</span>")
                st.markdown(" ".join(highlighted_list), unsafe_allow_html=True)

            with col2:
                st.markdown("<style>.field-label { font-weight: bold; margin-top: 1rem; }</style>", unsafe_allow_html=True)
                listing_data = {}
                fields = {
                    "Title": 150,
                    "Bullet1": 200,
                    "Bullet2": 200,
                    "Bullet3": 200,
                    "Bullet4": 200,
                    "Bullet5": 200,
                    "Description": 2000,
                    "Search Terms": 250
                }
                for field, max_bytes in fields.items():
                    content = st.text_area(f"{field}", row.get(field, ""), key=f"{field}_{i}")
                    byte_count = byte_length(content)
                    color = "red" if byte_count > max_bytes else "gray"
                    st.markdown(f"<small style='color:{color}'>Bytes: {byte_count} / {max_bytes}</small>", unsafe_allow_html=True)
                    preview = highlight_keywords(content, keywords)
                    st.markdown(f"<div style='padding: 0.5rem; border: 1px solid #eee;'>{preview}</div>", unsafe_allow_html=True)
                    listing_data[field] = content
                listing_data["Keywords"] = keywords_raw
                updated_rows.append(listing_data)

    # Neue Excel-Datei zum Download
    st.markdown("---")
    st.header("📥 Download aktualisierte Listings")
   result_df = pd.DataFrame(updated_rows)

# Excel in einen BytesIO-Puffer schreiben
output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    result_df.to_excel(writer, index=False)
output.seek(0)

# Download-Button anzeigen
st.download_button(
    label="📥 Excel herunterladen",
    data=output,
    file_name="updated_listings.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
