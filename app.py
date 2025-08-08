
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Amazon Listing Editor", layout="wide")

st.title("🛠️ Amazon Listing Editor – Byte-Check, Keyword-Highlighting & Direkte Bearbeitung")

uploaded_file = st.file_uploader("📁 Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    expected_columns = ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms', 'Keywords']
    if not all(col in df.columns for col in expected_columns):
        st.error("❌ Die Datei muss folgende Spalten enthalten: " + ", ".join(expected_columns))
    else:
        limits = {
            'Titel': 150,
            'Bullet1': 200, 'Bullet2': 200, 'Bullet3': 200,
            'Bullet4': 200, 'Bullet5': 200,
            'Description': 2000,
            'SearchTerms': 250
        }

        for idx, row in df.iterrows():
            with st.expander(f"📝 Listing {idx + 1}", expanded=False):
                st.subheader(f"Listing {idx + 1}")

                # Direkt editierbares Keyword-Feld in der Sidebar
                with st.sidebar.expander(f"✏️ Keywords bearbeiten – Listing {idx + 1}", expanded=False):
                    current_keywords = row.get('Keywords', '')
                    new_keywords = st.text_area("Keywords (durch Komma getrennt)", value=current_keywords, key=f"Keywords_{idx}", height=100)
                    df.at[idx, 'Keywords'] = new_keywords

                # Keyword-Liste aufbereiten
                keywords = [kw.strip() for kw in new_keywords.lower().split(",") if kw.strip()]
                used_keywords = set()

                def highlight_keywords(text, keywords):
                    if not isinstance(text, str):
                        return text, 0, set()
                    byte_count = len(text.encode("utf-8"))
                    found = set()

                    def replacer(match):
                        kw = match.group(0)
                        found.add(kw.lower())
                        return f'<span style="background-color:#ffeb3b">{kw}</span>'

                    for kw in sorted(keywords, key=len, reverse=True):
                        pattern = re.compile(rf'(?i)\b{re.escape(kw)}\b')
                        text = pattern.sub(replacer, text)
                    return text, byte_count, found

                # Content-Felder bearbeiten (nur noch 1 Feld pro Abschnitt)
                for section in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
                    content = row.get(section, "")
                    byte_limit = limits.get(section, 9999)

                    st.markdown(f"<div style='margin-top:1em; font-weight:bold; font-size:16px'>{section}</div>", unsafe_allow_html=True)

                    edited = st.text_area(
                        f"{section} Inhalt",
                        value=content,
                        key=f"{section}_{idx}",
                        label_visibility="collapsed",
                        height=100
                    )
                    df.at[idx, section] = edited

                    current_bytes = len(edited.encode('utf-8'))
                    over_limit = current_bytes > byte_limit
                    color = "#ff4d4d" if over_limit else "#999999"
                    st.markdown(f"<div style='font-size:11px; color:{color}; margin-bottom:4px;'>Bytes: {current_bytes} / {byte_limit}</div>", unsafe_allow_html=True)

                    highlighted, _, found_kw = highlight_keywords(edited, keywords)
                    used_keywords.update(found_kw)

                    st.markdown(f"<div style='border:1px solid #eee; padding:10px; border-radius:5px; background-color:#fafafa'>{highlighted}</div>", unsafe_allow_html=True)

        # Download überarbeitete Datei
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Edited')
            output.seek(0)
            return output

        st.success("✅ Änderungen übernommen – du kannst die Datei jetzt herunterladen.")
        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Excel-Datei herunterladen", data=excel_data, file_name="Listing_Edited.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
