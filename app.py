
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(layout="wide")

st.markdown("""
<style>
.block-container {
    padding-right: 2rem !important;
}
.listing-container {
    width: 100%;
    max-width: 1400px;
}
textarea {
    font-family: monospace;
}
.highlight {
    background-color: #ffff00;
    font-weight: bold;
}
.byte-count {
    font-size: 0.8em;
    color: gray;
}
.byte-warning {
    color: red;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

MAX_BYTES = {
    'Titel': 150,
    'Bullet1': 200,
    'Bullet2': 200,
    'Bullet3': 200,
    'Bullet4': 200,
    'Bullet5': 200,
    'Description': 2000,
    'SearchTerms': 250
}

def calculate_bytes(text):
    return len(text.encode('utf-8'))

def highlight_keywords(text, keywords):
    def replacer(match):
        return f'<span class="highlight">{match.group(0)}</span>'
    for kw in sorted(keywords, key=len, reverse=True):
        pattern = re.compile(rf'(?<!\w)({re.escape(kw)})(?!\w)', re.IGNORECASE)
        text = pattern.sub(replacer, text)
    return text

def render_listing(listing, idx, all_keywords):
    with st.expander(f"📦 Listing {idx + 1} – einklappen/ausklappen", expanded=False):
        cols = st.columns([1, 3])

        with cols[0]:
            st.markdown(f"### ✏️ Keywords für Listing {idx + 1}")
            keyword_input = st.text_area("Keywords (durch Komma getrennt)", value=", ".join(all_keywords[idx]), key=f"kw_input_{idx}")
            updated_keywords = [k.strip() for k in keyword_input.split(",") if k.strip()]
            all_keywords[idx] = updated_keywords

        with cols[1]:
            st.markdown(f'<div class="listing-container">', unsafe_allow_html=True)
            for field in ['Titel', 'Bullet1', 'Bullet2', 'Bullet3', 'Bullet4', 'Bullet5', 'Description', 'SearchTerms']:
                content = listing.get(field, "")
                max_bytes = MAX_BYTES.get(field, 9999)
                new_text = st.text_area(f"{field}", value=content, key=f"{field}_{idx}", height=100)
                byte_len = calculate_bytes(new_text)
                byte_display = f'<span class="byte-count">Bytes: {byte_len} / {max_bytes}</span>'
                if byte_len > max_bytes:
                    byte_display = f'<span class="byte-count byte-warning">Bytes: {byte_len} / {max_bytes}</span>'
                st.markdown(byte_display, unsafe_allow_html=True)
                st.markdown(highlight_keywords(new_text, updated_keywords), unsafe_allow_html=True)
                listing[field] = new_text
            st.markdown("</div>", unsafe_allow_html=True)

        return listing, updated_keywords

st.title("🛠️ Amazon Listing Editor mit WYSIWYG-Highlighting & Excel-Support")

uploaded_file = st.file_uploader("📤 Excel mit Listings hochladen", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    listings = df.to_dict(orient='records')
    if 'Keywords' in df.columns:
        keyword_lists = [str(row).split(",") if pd.notna(row) else [] for row in df['Keywords']]
        keyword_lists = [[k.strip() for k in kws] for kws in keyword_lists]
    else:
        keyword_lists = [[] for _ in listings]

    updated_listings = []
    updated_keywords_all = []

    for i, listing in enumerate(listings):
        updated_listing, updated_keywords = render_listing(listing, i, keyword_lists)
        updated_listings.append(updated_listing)
        updated_keywords_all.append(updated_keywords)

    # Excel Download
    st.subheader("📥 Download aktualisierte Listings")
    result_df = pd.DataFrame(updated_listings)
    result_df["Keywords"] = [", ".join(kws) for kws in updated_keywords_all]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        result_df.to_excel(writer, index=False)
    st.download_button("📄 Download als Excel", output.getvalue(), file_name="updated_listings.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
