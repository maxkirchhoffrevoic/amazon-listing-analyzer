
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Amazon Listing Editor", layout="wide")

st.title("🛠️ Amazon Listing Editor mit Keyword-Highlighting & Byte-Warnung")

uploaded_file = st.file_uploader("📁 Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    expected_columns = ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms', 'Keywords']
    if not all(col in df.columns for col in expected_columns):
        st.error("❌ Die Datei muss folgende Spalten enthalten: " + ", ".join(expected_columns))
    else:
        # Sidebar: Keywordliste
        st.sidebar.header("🔑 Keyword-Liste")

        for idx, row in df.iterrows():
            st.markdown(f"## 📝 Listing {idx + 1}")
            st.sidebar.markdown(f"### Listing {idx + 1}")

            raw_keywords = str(row['Keywords'])
            keywords = [kw.strip() for kw in raw_keywords.lower().split(",") if kw.strip()]
            used_keywords = set()

            def highlight_keywords(text, keywords):
                if not isinstance(text, str):
                    return text, 0, set()
                byte_count = len(text.encode("utf-8"))
                found = set()

                # Funktion zum Ersetzen
                def replacer(match):
                    kw = match.group(0)
                    found.add(kw.lower())
                    return f'<span style="background-color:#ffeb3b">{kw}</span>'

                for kw in sorted(keywords, key=len, reverse=True):
                    pattern = re.compile(rf'(?i)\b{re.escape(kw)}\b')
                    text = pattern.sub(replacer, text)
                return text, byte_count, found

            def byte_limit(section, byte_len):
                limits = {
                    'Titel': 150,
                    'Bullet1': 200, 'Bullet2': 200, 'Bullet3': 200,
                    'Bullet4': 200, 'Bullet5': 200,
                    'Description': 2000,
                    'SearchTerms': 250
                }
                return byte_len > limits.get(section, 9999)

            new_row = {}
            for section in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
                content = row.get(section, "")
                edited = st.text_area(f"{section}", value=content, key=f"{section}_{idx}")
                new_row[section] = edited

                highlighted, byte_len, found_kw = highlight_keywords(edited, keywords)
                used_keywords.update(found_kw)

                over_limit = byte_limit(section, byte_len)
                header_color = "red" if over_limit else "black"
                st.markdown(f"<div style='color:{header_color}; font-weight:bold'>{section} ({byte_len} Bytes)</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='border:1px solid #ccc; padding:10px; border-radius:5px'>{highlighted}</div>", unsafe_allow_html=True)
                st.markdown("---")

            # Seitenleiste – Keywordliste mit Markierung
            highlighted_keywords = []
            for kw in keywords:
                if kw in used_keywords:
                    highlighted_keywords.append(f"<span style='background-color:#c8e6c9'>{kw}</span>")
                else:
                    highlighted_keywords.append(f"<span>{kw}</span>")
            st.sidebar.markdown("<br>".join(highlighted_keywords), unsafe_allow_html=True)

            # Update DataFrame
            for key in new_row:
                df.at[idx, key] = new_row[key]

        # Download überarbeitetes Excel
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Edited')
            output.seek(0)
            return output

        st.success("✅ Änderungen vorgenommen – du kannst die bearbeitete Datei jetzt exportieren.")
        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Überarbeitete Datei herunterladen", data=excel_data, file_name="Listing_Edited.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
