
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🛠️ Amazon Listing Editor mit Keyword-Highlighting")

# --- Hilfsfunktionen ---
def highlight_keywords(text, keywords):
    if not text:
        return ""
    for kw in sorted(keywords, key=len, reverse=True):
        escaped_kw = re.escape(kw.strip())
        text = re.sub(f"(?i)({escaped_kw})", r'<mark>\1</mark>', text)
    return text

def byte_length(text):
    return len(text.encode("utf-8"))

# --- Upload ---
uploaded_file = st.file_uploader("📤 Excel-Datei mit Listings hochladen", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    updated_rows = []

    # Prüfe auf optionale "Product"-Spalte (nur Anzeigezweck)
    has_product = "Product" in df.columns

    # --- (Optional) Keywords-only Auto-Detect: nur 'Keywords' ohne Content-Spalten ---
    expected_cols = ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms","Keywords"]
    cols_lower = [str(c).strip().lower() for c in df.columns]

    # Sonderfall A (df.shape[1] == 1) entfernt

    if ("keywords" in cols_lower) and not any(
        c in cols_lower for c in ["titel","bullet1","bullet2","bullet3","bullet4","bullet5","description","searchterms","search terms"]
    ):
        df = df.rename(columns={c: ("Keywords" if str(c).strip().lower() == "keywords" else c) for c in df.columns})
        df["Keywords"] = df["Keywords"].astype(str).fillna("")
        for col in ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms"]:
            if col not in df.columns:
                df[col] = ""
        order = (["Product"] if "Product" in df.columns else []) + expected_cols
        df = df[order]
        has_product = "Product" in df.columns


    # --- Bearbeitungsmaske ---
    for i, row in df.iterrows():
        listing_label = row["Product"] if has_product and pd.notna(row.get("Product", "")) and str(row.get("Product", "")).strip() != "" else f"Listing {i+1}"

        with st.expander(f"📦 {listing_label} – einklappen/ausklappen", expanded=False):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown(f"### ✏️ Keywords für {listing_label}")
                keywords_raw = str(row.get("Keywords", ""))
                # Komma ODER Zeilenumbruch als Trenner
                keywords_input = st.text_area("Keywords (Komma oder Zeilenumbruch)", value=keywords_raw, key=f"kw_input_{i}")
                keywords = [kw.strip() for kw in re.split(r"[,\n]", keywords_input) if kw.strip()]

            with col2:
                # Überschriften-Style (größer & deutlicher) – unverändert zu deiner Version
                st.markdown("""
                    <style>
                    .field-label{
                      font-weight:700;
                      font-size:1.15rem;
                      color:#111827;
                      line-height:1.25;
                      margin:1rem 0 .35rem 0;
                      display:inline-block;
                      padding:4px 10px;
                      border-left:5px solid #4F46E5;
                      background:#F3F4F6;
                      border-radius:6px;
                    }
                    </style>
                """, unsafe_allow_html=True
                )

                def render_field(field_name, limit):
                    st.markdown(f"<div class='field-label'>{field_name}</div>", unsafe_allow_html=True)
                    value = st.text_area(field_name, value=str(row.get(field_name, "")), key=f"{field_name}_{i}", label_visibility="collapsed", height=90)
                    blen = byte_length(value)
                    st.markdown(f"<div style='font-size:.8rem;color:{'red' if blen>limit else '#6b7280'}'>Bytes: {blen} / {limit}</div>", unsafe_allow_html=True)
                    preview = highlight_keywords(value, keywords)
                    st.markdown(f"<div style='padding:.5rem;border:1px solid #e5e7eb;border-radius:6px;background:#fafafa'>{preview}</div>", unsafe_allow_html=True)
                    return value

                listing_data = {}
                limits = {
                    "Titel": 150, "Bullet1": 200, "Bullet2": 200, "Bullet3": 200,
                    "Bullet4": 200, "Bullet5": 200, "Description": 2000, "SearchTerms": 250
                }
                for fname, lim in limits.items():
                    listing_data[fname] = render_field(fname, lim)
                listing_data["Keywords"] = keywords_input
                if has_product:
                    listing_data["Product"] = row.get("Product", "")

            # --- HIER: Dynamische Keyword-Hervorhebung basierend auf aktuellem Content ---
            all_text = " ".join(
                str(listing_data.get(f, ""))
                for f in ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms"]
            )
                    # Robuster, sofortiges Live‑Highlighting ohne Regex-Grenzfälle
            used = {
                kw for kw in keywords
                if kw and kw.strip() and kw.lower() in all_text.lower()
            }

            chips = " ".join(
                f"<span style='background:{('#d4edda' if kw in used else '#f3f4f6')};"
                f"border:1px solid #e5e7eb;border-radius:6px;padding:2px 6px;margin:2px;display:inline-block'>{kw}</span>"
                for kw in keywords
            )
            with col1:
                st.markdown(chips, unsafe_allow_html=True)

            updated_rows.append(listing_data)

    # --- Download --- (Product als erste Spalte, falls vorhanden)
    st.markdown("---")
    st.header("📥 Download aktualisierte Listings")

# Build DataFrame aus den bearbeiteten Zeilen
    result_df = pd.DataFrame(updated_rows)

# ➜ NEU: 'Product' IMMER vorhanden machen und an die erste Stelle setzen
    if "Product" not in result_df.columns:
        result_df["Product"] = ""          # leere Product-Spalte hinzufügen

    cols = ["Product"] + [c for c in result_df.columns if c != "Product"]
    result_df = result_df[cols]


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
