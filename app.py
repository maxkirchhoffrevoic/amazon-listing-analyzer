
import re

# Beispielhafter Rohstring der Keywords
keywords_raw = "brotbox, edelstahl\nplastikfrei, robust"

# Korrekte Aufsplittung nach Komma oder Zeilenumbruch
keywords = [kw.strip() for kw in re.split(r"[,
]", keywords_raw) if kw.strip()]

print(keywords)
