# Dein bestehender Code, nur der fehlerhafte Einrückungsbereich wurde korrigiert

# Beispielkorrektur für den problematischen Block
if 'df' in locals() and not df.empty:
    cols_lower = [str(c).strip().lower() for c in df.columns]
    # Restliche Logik unverändert hier einfügen
