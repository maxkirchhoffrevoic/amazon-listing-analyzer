import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Amazon Listing Analyzer", layout="wide")

st.title("📊 Amazon Listing Analyzer")
st.markdown("Lade deine **Content-Datei** und **Keyword-Liste** hoch, um automatisch Zeichenanzahl, Byteanzahl und Keyword-Abdeckung zu analysieren.")

# ==== Upload-Bereich ====
content_file = st.file_uploader("🔠 Content Excel (Titel, Bullets, Description, Search Terms)", type=["xlsx"])
keyword_file = st.file_uploader("🔑 Keyword Excel (eine Spalte)", type=["xlsx"])

if content_file and keyword_file:
    content_df = pd.read_excel(content_file)
    keywords_df = pd.read_excel(keyword_file)

    if not keywords_df.empty:
        st.success("Dateien erfolgreich geladen. Analyse läuft...")

        # Keywordliste bereinigen
        keywords = keywords_df.iloc[:, 0].dropna().astype(str).str.lower().tolist()

        result_df = content_df.copy()

        for col in content_df.columns:
            result_df[col] = result_df[col].fillna("").astype(str)

            result_df[f'{col}_CharCount'] = result_df[col].apply(len)
            result_df[f'{col}_ByteCount'] = result_df[col].apply(lambda x: len(x.encode('utf-8')))

            def match_keywords(text):
                text_lower = text.lower()
                matched = [kw for kw in keywords if kw in text_lower]
                return ", ".join(matched)

            result_df[f'{col}_MatchedKeywords'] = result_df[col].apply(match_keywords)

        st.subheader("📋 Vorschau der Ergebnisse")
        st.dataframe(result_df, use_container_width=True)

        # ==== Download vorbereiten ====
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Analyse')
                workbook = writer.book
                worksheet = writer.sheets['Analyse']
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)
            output.seek(0)
            return output

        excel_data = to_excel(result_df)

        st.download_button(
            label="📥 Ergebnis als Excel herunterladen",
            data=excel_data,
            file_name="Amazon_Content_Analyse.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Die Keyword-Datei scheint leer zu sein.")
else:
    st.info("Bitte lade beide Dateien hoch, um fortzufahren.")
