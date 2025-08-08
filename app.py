
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Amazon Listing Editor", layout="wide")

st.title("🛠️ Amazon Listing Editor – Kompaktansicht mit Byteanzeige & Keywordkontrolle")

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

                # KEYWORDS bearbeiten
                with st.sidebar.expander(f"✏️ Keywords für Listing {idx + 1}", expanded=False):
                    current_keywords = row.get('Keywords', '')
                    new_keywords = st.text_area("Keywords (durch Komma getrennt)", value=current_keywords, key=f"Keywords_{idx}", height=100)
                    df.at[idx, 'Keywords'] = new_keywords

                keywords = [kw.strip() for kw in new_keywords.lower().split(",") if kw.strip()]

                def get_byte_count(text):
                    return len(text.encode("utf-8"))

                for section in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
                    content = row.get(section, "")
                    byte_limit = limits.get(section, 9999)

                    edited = st.text_area(
                        f"{section} (Max: {byte_limit} Bytes)",
                        value=content,
                        key=f"{section}_{idx}",
                        height=100
                    )
                    df.at[idx, section] = edited

                    current_bytes = get_byte_count(edited)
                    over = current_bytes > byte_limit
                    byte_color = "#ff4d4d" if over else "#888888"
                    st.markdown(
                        f"<div style='font-size:11px; color:{byte_color}; margin-top:-10px; margin-bottom:8px'>Bytes: {current_bytes} / {byte_limit}</div>",
                        unsafe_allow_html=True
                    )

        # EXPORT
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Edited')
            output.seek(0)
            return output

        st.success("✅ Du kannst die bearbeitete Datei jetzt exportieren.")
        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Excel-Datei herunterladen", data=excel_data, file_name="Listing_Edited.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
