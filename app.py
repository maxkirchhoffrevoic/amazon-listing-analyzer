
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Amazon Listing Editor – Custom WYSIWYG", layout="wide")
st.title("🛠️ Amazon Listing Editor mit echtem WYSIWYG-Highlighting (Custom JS-Komponente)")

st.markdown("Diese Version nutzt eine eingebettete benutzerdefinierte JavaScript-Komponente für echtes Inline-Keyword-Highlighting während der Bearbeitung.")

# Beispielhafte HTML-Komponente mit einfacher Textarea und Markierung
custom_editor_html = """
<div style="font-family: sans-serif;">
  <label for="editor" style="font-weight: bold; font-size: 16px;">Titel (mit Keyword-Highlight)</label><br>
  <textarea id="editor" rows="5" style="width:100%; padding:10px; font-size: 14px;" oninput="highlight()"></textarea>
  <div id="preview" style="margin-top:10px; padding:10px; background:#f9f9f9; border:1px solid #ddd;"></div>
</div>

<script>
  const keywords = ["brotbox", "edelstahl", "bpa-frei", "kompakt"];
  const colors = ["#fff176", "#ffab91", "#b9f6ca", "#b39ddb"];

  function highlight() {
    let input = document.getElementById("editor").value;
    let result = input;

    keywords.forEach((kw, index) => {
      const color = colors[index % colors.length];
      const regex = new RegExp("(" + kw + ")", "gi");
      result = result.replace(regex, "<mark style='background-color:" + color + "'>$1</mark>");
    });

    document.getElementById("preview").innerHTML = "<b>Live-Vorschau:</b><br>" + result;
  }

  window.onload = highlight;
</script>
"""

components.html(custom_editor_html, height=300)
