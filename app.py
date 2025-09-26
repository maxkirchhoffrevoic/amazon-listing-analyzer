import streamlit as st
import pandas as pd
import re
import json
from io import BytesIO

# Optional: OpenAI SDK
# pip install openai
try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

st.set_page_config(layout="wide")
st.title("🛠️ Amazon Listing Editor mit Keyword-Highlighting")

# --- Erklärungstext unterhalb der Überschrift ---
st.markdown("""
## 📝 Funktionsweise des Tools

Dieses Tool dient zur Bearbeitung und Analyse von Amazon-Listing-Inhalten direkt im Browser.  
Du kannst eine Excel-Datei hochladen, deren Inhalte in einer komfortablen Oberfläche angezeigt, live bearbeitet und mit einer Keyword-Liste abgeglichen werden. Dabei werden genutzte Keywords farblich hervorgehoben, und die Zeichen- bzw. Byte-Längen der Felder werden in Echtzeit geprüft.  

Nach der Bearbeitung kannst du die aktualisierten Daten wieder als Excel herunterladen – mit allen Änderungen, einschließlich des geänderten Listing-Namens.

---

## 📂 Anforderungen an die hochzuladene Excel

Damit die Datei korrekt eingelesen wird, muss sie folgende Struktur erfüllen:

- **Format:** `.xlsx` (Excel-Datei, keine CSV oder andere Formate)  
- **Tabellenstruktur:**  
  - Die Spalten sollten wie folgt benannt sein, **dabei spielt die Reihenfolge der Spalten keine Rolle**:
    ```
    Product | Titel | Bullet1 | Bullet2 | Bullet3 | Bullet4 | Bullet5 | Description | SearchTerms | Keywords
    ```

---

## 🔍 Wichtige Hinweise
- Das Tool erkennt automatisch, welche Keywords im Content vorkommen, und markiert diese **sowohl in der Content-Vorschau als auch in der Keywordliste**.
- Die Spaltenlängen werden in Bytes gezählt, damit sie den Amazon-Limits entsprechen (z. B. Titel max. 150 Bytes, Bullet-Points max. 200 Bytes etc.).
""")

# ========= NEU: Kontext & Inputs + Prompt-Button =========
st.markdown("### ✍️ Kontext & Inputs für automatische Erstellung")
ctx_text = st.text_area(
    "Schreibe hier Produktdaten, USPs, Zielgruppe, besondere Keywords usw. hinein.",
    placeholder="Beispiel: Brotbox aus Edelstahl, 1.2 L, BPA-frei, auslaufsicher, spülmaschinenfest, Farbe Silber ...",
    height=180,
    key="ctx_textarea",
)

def _build_prompt(user_context: str) -> str:
    # Dein exaktes Prompt, mit Vorgaben + JSON-Ausgabeanweisung
    return f"""
Du bist Amazon Copywrighter und musst mir für nachfolgendes Produkt die Bullet Points, Description und Search Terms schreiben. Sprache des Listings ist deutsch. Achte ebenso darauf, dass wir auf Garantieversprechen verzichten. Das bedeutet keine Worte wie perfekt, garantiert etc. nutzen. Hier ist der Aufbau der Felder:

Titel: besteht aus 140-150 Zeichen, beginnt mit dem Produktnamen, danach die Key-Features und am Ende Dinge wie Farbe oder Stückzahl, falls vorhanden

Bullet Points: Insgesamt fünf Stück, bestehen aus 190-200 Zeichen, starten mit jeweils zwei Worten in Versalien und einem Doppelpunkt. Sie enden jeweils ohne Punktuation. Achte darauf das die Bullet Points jeweils ein übergeordnetes Thema haben. Ebenso sollen sie nach dem Doppelpunkt aus einem kompletten deutschen Satz bestehen.

Description: besteht aus 3 Absätzen mit jeweils einer kurzen Überschrift. Insgesamt hat diese 1600-1800 Zeichen.

Search Terms: haben insgesamt 220-250 Zeichen und stellen nur Keywords dar, vor allem die, die im vorherigen Content nicht genutzt wurden. schreibe sie mir einfach ohne Komma oder ähnliches hintereinander weg.

Input für dieses Produkt ist folgendes:

{user_context}

Gib die Antwort **ausschließlich** als kompaktes JSON im folgenden Schema zurück:
{{
  "Titel": "...",
  "Bullet1": "...",
  "Bullet2": "...",
  "Bullet3": "...",
  "Bullet4": "...",
  "Bullet5": "...",
  "Description": "...",
  "SearchTerms": "..."
}}
""".strip()

# Session-Container für generierte Listings (damit Bearbeitung + Export wie beim Upload funktioniert)
if "generated_rows" not in st.session_state:
    st.session_state["generated_rows"] = []

def _call_openai_and_parse(prompt_text: str) -> dict:
    """
    Ruft (optional) OpenAI auf (Model: gpt-5) und parst die JSON-Antwort.
    Fällt beim Fehler auf {} zurück.
    """
    # Wenn OpenAI SDK fehlt oder kein API-Key gesetzt ist, brechen wir sauber ab.
    if not _HAS_OPENAI:
        st.warning("OpenAI SDK nicht installiert. Installiere mit `pip install openai` und setze die Umgebungsvariable OPENAI_API_KEY.")
        return {}

    try:
        client = OpenAI()  # nutzt OPENAI_API_KEY aus Environment
        resp = client.chat.completions.create(
            model="gpt-5",  # vom Nutzer gewünschtes Modell
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher, präziser Assistent."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip()
        # JSON extrahieren
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            st.error("Konnte kein JSON aus der Antwort extrahieren.")
            return {}
        return json.loads(m.group(0))
    except Exception as e:
        st.error(f"Generierung fehlgeschlagen: {e}")
        return {}

if st.button("✨ Listing automatisch erstellen (ChatGPT – gpt-5)"):
    if not ctx_text.strip():
        st.warning("Bitte zuerst Kontext/Inputs eingeben.")
    else:
        prompt = _build_prompt(ctx_text)
        result = _call_openai_and_parse(prompt)
        if result:
            # Generiertes Listing in identisches Datenformat bringen
            st.session_state["generated_rows"].append({
                "Product": "Generiert aus Kontext",
                "Titel": result.get("Titel", ""),
                "Bullet1": result.get("Bullet1", ""),
                "Bullet2": result.get("Bullet2", ""),
                "Bullet3": result.get("Bullet3", ""),
                "Bullet4": result.get("Bullet4", ""),
                "Bullet5": result.get("Bullet5", ""),
                "Description": result.get("Description", ""),
                "SearchTerms": result.get("SearchTerms", ""),
                "Keywords": ""  # optional leer; du kannst hier auch aus Kontext Keywords übernehmen
            })
            st.success("Inhalte generiert. Scrolle nach unten – das Listing erscheint in der Bearbeitungsmaske.")

# ================== Rest: Vorhandene App-Funktionen (Upload, Bearbeitung, Export) ==================

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
updated_rows_all = []  # Sammelbecken für Upload-Listings + generierte Listings

def render_listing(row, i, has_product):
    """Rendert ein Listing-Panel und gibt das (ggf. bearbeitete) Dict zurück."""
    default_name = (str(row.get("Product", "")).strip() if has_product else "") or f"Listing {i+1}"
    if f"product_{i}" not in st.session_state:
        st.session_state[f"product_{i}"] = default_name
    listing_label = st.session_state[f"product_{i}"]

    # Expander-Open-State je Listing
    open_key = f"exp_open_{i}"
    if open_key not in st.session_state:
        st.session_state[open_key] = False

    with st.expander(f"📦 {listing_label} – einklappen/ausklappen", expanded=st.session_state[open_key]):
        col1, col2 = st.columns([1, 3])

        with col1:
            # Beim Tippen offen halten
            def _keep_open_expander(key=open_key):
                st.session_state[key] = True

            st.text_input(
                "Listing-Name (Product)",
                value=st.session_state[f"product_{i}"],
                key=f"product_{i}",
                on_change=_keep_open_expander
            )

            st.markdown(f"### ✏️ Keywords für {st.session_state[f'product_{i}']}")
            keywords_raw = str(row.get("Keywords", ""))
            keywords_input = st.text_area("Keywords (Komma oder Zeilenumbruch)", value=keywords_raw, key=f"kw_input_{i}")
            keywords = [kw.strip() for kw in re.split(r"[,\n]", keywords_input) if kw.strip()]

        with col2:
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
            """, unsafe_allow_html=True)

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
            listing_data["Product"] = st.session_state.get(f"product_{i}", default_name)

        # Live-Keyword-Chips (links), basierend auf aktuellem Content
        all_text = " ".join(
            str(listing_data.get(f, ""))
            for f in ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms"]
        ).lower()
        used = {kw for kw in keywords if kw and kw.lower() in all_text}
        chips = " ".join(
            f"<span style='background:{('#d4edda' if kw in used else '#f3f4f6')};"
            f"border:1px solid #e5e7eb;border-radius:6px;padding:2px 6px;margin:2px;display:inline-block'>{kw}</span>"
            for kw in keywords
        )
        with col1:
            st.markdown(chips, unsafe_allow_html=True)

    return listing_data

# ---- 1) Upload rendern (wie gehabt) ----
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    has_product = "Product" in df.columns
    expected_cols = ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms","Keywords"]
    cols_lower = [str(c).strip().lower() for c in df.columns]

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

    for i, row in df.iterrows():
        listing_data = render_listing(row, i, has_product)
        updated_rows_all.append(listing_data)

# ---- 2) Generierte Listings rendern (falls vorhanden) ----
if st.session_state["generated_rows"]:
    st.markdown("---")
    st.subheader("🧠 Generierte Listings")
    start_index = len(updated_rows_all)
    for j, row in enumerate(st.session_state["generated_rows"]):
        # Für generierte Reihen: Product existiert; falls leer, nehmen wir Naming wie sonst
        listing_data = render_listing(row, start_index + j, has_product=("Product" in row))
        updated_rows_all.append(listing_data)

# --- Download (Export) ---
if updated_rows_all:
    st.markdown("---")
    st.header("📥 Download aktualisierte Listings")
    result_df = pd.DataFrame(updated_rows_all)
    if "Product" not in result_df.columns:
        result_df["Product"] = ""
    cols = ["Product"] + [c for c in result_df.columns if c != "Product"]
    result_df = result_df[cols]

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False)
    output.seek(0)
    st.download_button(
        label="📥 Excel herunterladen",
        data=output,
        file_name="updated_listings.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
