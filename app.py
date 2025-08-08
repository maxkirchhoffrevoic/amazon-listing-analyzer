
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


# Zusätzlicher Import: Nur-Keyword-Excel hochladen
st.markdown("---")
st.subheader("🔁 Optional: Nur Keyword-Liste importieren")
keywords_only_file = st.file_uploader("📄 Excel mit reinen Keyword-Zeilen hochladen", type=["xlsx"], key="keywords_only")
if keywords_only_file:
    try:
        keyword_df = pd.read_excel(BytesIO(keywords_only_file.read()))
        keyword_column = keyword_df.columns[0]
        updated_rows = []
        for i, row in keyword_df.iterrows():
            kw_list = str(row[keyword_column])
            updated_rows.append({
                "Titel": "",
                "Bullet1": "",
                "Bullet2": "",
                "Bullet3": "",
                "Bullet4": "",
                "Bullet5": "",
                "Description": "",
                "SearchTerms": "",
                "Keywords": kw_list
            })
        df = pd.DataFrame(updated_rows)
        uploaded_file = True  # Trick: wir setzen die Haupt-Maske darunter in Gang
        st.success("Keywords erfolgreich importiert. Die Content-Felder sind leer.")
    except Exception as e:
        st.error(f"Fehler beim Lesen der Keyword-Datei: {e}")


if uploaded_file:
    from io import BytesIO
        df = pd.read_excel(BytesIO(uploaded_file.read()))
    updated_rows = []

    # Durch alle Listings iterieren
    for i, row in df.iterrows():
        with st.expander(f"📦 Listing {i+1} – einklappen/ausklappen", expanded=False):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown(f"### ✏️ Keywords für Listing {i+1}")
                keywords_raw = st.text_area("Keywords (durch Komma getrennt)", row.get("Keywords", ""), key=f"kw_input_{i}")
                keywords = [kw.strip() for kw in keywords_raw.split(",") if kw.strip()]
                
                


            with col2:
                st.markdown("<style>.field-label { font-weight: bold; margin-top: 1rem; }</style>", unsafe_allow_html=True)
                listing_data = {}
                fields = {
                    "Titel": 150,
                    "Bullet1": 200,
                    "Bullet2": 200,
                    "Bullet3": 200,
                    "Bullet4": 200,
                    "Bullet5": 200,
                    "Description": 2000,
                    "SearchTerms": 250
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
                
        # Dynamische Keyword-Highlighting-Liste
        highlighted_list = []
        all_content = " ".join(listing_data.get(field, "") for field in ["Titel", "Bullet1", "Bullet2", "Bullet3", "Bullet4", "Bullet5", "Description", "SearchTerms"])
        for kw in keywords:
            color = "#d4edda" if re.search(rf"\b{re.escape(kw)}\b", all_content, re.IGNORECASE) else "transparent"
            highlighted_list.append(f"<span style='background-color:{color}; padding:2px 4px; border-radius:4px; display:inline-block; margin:2px'>{kw}</span>")
        with col1:
            st.markdown(" ".join(highlighted_list), unsafe_allow_html=True)

        updated_rows.append(listing_data)

    # Neue Excel-Datei zum Download
    st.markdown("---")
    st.header("📥 Download aktualisierte Listings")
    result_df = pd.DataFrame(updated_rows)
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False)
    output.seek(0)
    st.download_button(
        label="📥 Download Excel-Datei",
        data=output,
        file_name="updated_listings.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
