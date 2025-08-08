
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Amazon Listing Editor", layout="wide")

st.title("🛠️ Amazon Listing Editor mit Byte-Warnung, Keyword-Highlighting & Editierfunktion")

uploaded_file = st.file_uploader("📁 Excel-Datei hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    expected_columns = ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms', 'Keywords']
    if not all(col in df.columns for col in expected_columns):
        st.error("❌ Die Datei muss folgende Spalten enthalten: " + ", ".join(expected_columns))
    else:
        st.sidebar.header("🔑 Keyword-Liste")

        limits = {
            'Titel': 150,
            'Bullet1': 200, 'Bullet2': 200, 'Bullet3': 200,
            'Bullet4': 200, 'Bullet5': 200,
            'Description': 2000,
            'SearchTerms': 250
        }

        for idx, row in df.iterrows():
            with st.expander(f"📝 Listing {idx + 1}", expanded=False):
                st.sidebar.markdown(f"### Listing {idx + 1}")

                raw_keywords = str(row['Keywords'])
                keywords = [kw.strip() for kw in raw_keywords.lower().split(",") if kw.strip()]
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

                new_row = {}
                for section in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
                    content = row.get(section, "")
                    byte_limit = limits.get(section, 9999)
                    edited = st.text_area(
                        f"{section} (Max: {byte_limit} Bytes)",
                        value=content,
                        key=f"{section}_{idx}",
                        help=f"Maximale Byteanzahl: {byte_limit}"
                    )
                    new_row[section] = edited

                    # Echtzeit-Byte-Anzeige
                    current_bytes = len(edited.encode('utf-8'))
                    over_limit = current_bytes > byte_limit
                    color = "red" if over_limit else "black"
                    st.markdown(f"<span style='color:{color}'>Aktuelle Bytes: {current_bytes} / {byte_limit}</span>", unsafe_allow_html=True)

                    # Vorschau mit Keyword-Highlighting
                    highlighted, byte_len, found_kw = highlight_keywords(edited, keywords)
                    used_keywords.update(found_kw)

                    st.markdown(f"<div style='border:1px solid #ccc; padding:10px; border-radius:5px'>{highlighted}</div>", unsafe_allow_html=True)
                    st.markdown("---")

                # Sidebar Keywordliste mit Markierung
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
