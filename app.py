
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Amazon Listing WYSIWYG Editor", layout="wide")
st.title("🧰 Amazon Listing Editor mit WYSIWYG, Keyword-Highlighting & Byte-Zähler")

# --- Helper: Byte count ---
def count_bytes(text):
    return len(text.encode("utf-8"))

# --- Upload Excel ---
uploaded_file = st.file_uploader("📤 Excel-Datei mit Listings hochladen", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    listings = df.to_dict(orient="records")

    export_data = []

    for idx, row in enumerate(listings):
        with st.expander(f"📦 Listing {idx+1} – einklappen/ausklappen", expanded=False):
            # Keyword-Panel links
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"#### ✏️ Keywords für Listing {idx+1}")
                kw_text = st.text_area(
                    f"Keywords (durch Komma getrennt)", 
                    row.get("Keywords", ""), 
                    key=f"kw_input_{idx}"
                )
                keyword_list = [k.strip().lower() for k in kw_text.split(",") if k.strip()]

            with col2:
    st.markdown("""
        <style>
        .block-container {padding-right: 2rem !important;}
        .listing-container {width: 100%; max-width: 1000px;}
        </style>
        """, unsafe_allow_html=True)
    container_class = "listing-container"
                for field, limit in {
                    "Titel": 150, 
                    "Bullet1": 200, 
                    "Bullet2": 200, 
                    "Bullet3": 200, 
                    "Bullet4": 200, 
                    "Bullet5": 200,
                    "Description": 2000, 
                    "SearchTerms": 250
                }.items():
                    orig_text = str(row.get(field, ""))

                    # HTML WYSIWYG Editor
                    components.html(f"""
                    <div style="margin-bottom:20px;">
                        <label style="font-weight:bold; font-size:16px;">{field}</label><br>
                        <textarea id="editor_{field}_{idx}" rows="4" style="width:100%; padding:8px; font-size:14px;" 
                            oninput="highlight_{field}_{idx}()">{orig_text}</textarea>
                        <div id="preview_{field}_{idx}" style="margin-top:5px; padding:10px; background:#f9f9f9; border:1px solid #ddd; font-family:sans-serif;"></div>
                        <div id="bytes_{field}_{idx}" style="font-size:12px; color:#888; margin-top:2px;"></div>
                    </div>

                    <script>
                        const kw_{field}_{idx} = {keyword_list};
                        const colors_{field}_{idx} = ["#fff176", "#ffab91", "#b9f6ca", "#b39ddb"];

                        function highlight_{field}_{idx}() {{
                            let inputElem = document.getElementById("editor_{field}_{idx}");
                            let previewElem = document.getElementById("preview_{field}_{idx}");
                            let bytesElem = document.getElementById("bytes_{field}_{idx}");
                            let input = inputElem.value;
                            let result = input;

                            kw_{field}_{idx}.forEach((kw, i) => {{
                                let regex = new RegExp("(" + kw + ")", "gi");
                                let color = colors_{field}_{idx}[i % colors_{field}_{idx}.length];
                                result = result.replace(regex, "<mark style='background-color:" + color + "'>$1</mark>");
                            }});

                            previewElem.innerHTML = result;
                            let byteCount = new TextEncoder().encode(input).length;
                            bytesElem.innerHTML = "Bytes: " + byteCount + " / {limit}";
                            bytesElem.style.color = byteCount > {limit} ? "red" : "#888";
                        }}
                        window.onload = highlight_{field}_{idx};
                    </script>
                    """, height=220)

                    export_data.append({
                        "Listing": idx + 1,
                        "Feld": field,
                        "Text": orig_text
                    })

    # --- Export Excel ---
    if st.button("📥 Geänderte Inhalte als Excel herunterladen"):
        export_df = pd.DataFrame(export_data)
        output = export_df.pivot(index="Listing", columns="Feld", values="Text").reset_index()
        excel_file = output.to_excel(index=False, engine='openpyxl')
        b64 = base64.b64encode(excel_file).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="bearbeitetes_listing.xlsx">Download Excel-Datei</a>'
        st.markdown(href, unsafe_allow_html=True)
