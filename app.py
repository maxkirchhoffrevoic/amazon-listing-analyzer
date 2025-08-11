# ... Dein bisheriger funktionierender Code oben ...

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # --- Keywords-only auto-detect (zusätzliche Funktion, ersetzt nichts am bestehenden Import) ---
    expected_cols = ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms","Keywords"]
    cols_lower = [str(c).strip().lower() for c in df.columns]

    # Fall A: nur 1 Spalte -> als Keywords interpretieren
    if df.shape[1] == 1:
        kw_col = df.columns[0]
        df = pd.DataFrame({
            "Titel": [""] * len(df),
            "Bullet1": [""] * len(df),
            "Bullet2": [""] * len(df),
            "Bullet3": [""] * len(df),
            "Bullet4": [""] * len(df),
            "Bullet5": [""] * len(df),
            "Description": [""] * len(df),
            "SearchTerms": [""] * len(df),
            "Keywords": df[kw_col].astype(str).fillna("")
        })

    # Fall B: es gibt eine 'Keywords'-Spalte, aber keine Content-Spalten -> ebenfalls Keywords-only
    elif ("keywords" in cols_lower) and not any(
        c in cols_lower for c in ["titel","bullet1","bullet2","bullet3","bullet4","bullet5","description","searchterms","search terms"]
    ):
        df = df.rename(columns={c: ("Keywords" if str(c).strip().lower() == "keywords" else c) for c in df.columns})
        df["Keywords"] = df["Keywords"].astype(str).fillna("")
        for col in ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms"]:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_cols]

# ... Rest deines funktionierenden Codes unten ...
