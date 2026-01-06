import streamlit as st
import pandas as pd
import re
import json
import uuid
from io import BytesIO
import os
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Optional: OpenAI SDK
# pip install openai
try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

# Database connection
def get_db_connection():
    """Erstellt eine Datenbankverbindung zur Supabase PostgreSQL Datenbank"""
    try:
        # Passwort aus Streamlit secrets oder Umgebungsvariable holen
        db_password = None
        
        # Zuerst Streamlit secrets versuchen (für lokale Entwicklung)
        try:
            if "supabase_db_password" in st.secrets:
                db_password = st.secrets["supabase_db_password"]
        except Exception:
            pass
        
        # Falls nicht in secrets, versuche Umgebungsvariable
        if not db_password:
            db_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if not db_password:
            return None
        
        # Connection String zusammenbauen
        connection_string = f"postgresql://postgres.povudekejufidhyuinro:{db_password}@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
        # Verbesserte Pool-Einstellungen für große Datenmengen
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,  # Prüft Connection vor Verwendung
            pool_recycle=300,    # Recyclet Connections nach 5 Minuten
            pool_size=5,         # Anzahl der Connections im Pool
            max_overflow=10,     # Zusätzliche Connections bei Bedarf
            pool_timeout=30,     # Timeout für Connection-Erstellung
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        )
        return engine
    except Exception as e:
        # Fehler nicht anzeigen, nur None zurückgeben (wird später gehandhabt)
        return None

def init_database(engine):
    """Erstellt die Tabelle falls sie nicht existiert"""
    if not engine:
        return False
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS listings (
        id SERIAL PRIMARY KEY,
        asin_ean_sku VARCHAR(255),
        mp VARCHAR(10),
        image TEXT,
        name VARCHAR(500),
        title TEXT,
        account VARCHAR(255),
        project VARCHAR(255),
        product VARCHAR(255),
        titel TEXT,
        bullet1 TEXT,
        bullet2 TEXT,
        bullet3 TEXT,
        bullet4 TEXT,
        bullet5 TEXT,
        description TEXT,
        search_terms TEXT,
        keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_asin ON listings(asin_ean_sku);
    CREATE INDEX IF NOT EXISTS idx_mp ON listings(mp);
    CREATE INDEX IF NOT EXISTS idx_account ON listings(account);
    CREATE INDEX IF NOT EXISTS idx_project ON listings(project);
    """
    
    try:
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))
        return True
    except SQLAlchemyError as e:
        st.error(f"Fehler beim Erstellen der Tabelle: {e}")
        return False

def save_listing_to_db(engine, listing_data, asin_ean_sku=None, mp=None, account=None, project=None):
    """Speichert ein Listing in der Datenbank (Insert oder Update)"""
    if not engine:
        return False
    
    # Prüfe ob Eintrag bereits existiert (basierend auf ASIN/EAN/SKU und MP)
    if asin_ean_sku and mp:
        check_sql = text("SELECT id FROM listings WHERE asin_ean_sku = :asin AND mp = :mp")
        with engine.connect() as conn:
            result = conn.execute(check_sql, {"asin": asin_ean_sku, "mp": mp}).fetchone()
            
        if result:
            # Update bestehender Eintrag
            update_sql = text("""
                UPDATE listings SET
                    image = :image,
                    name = :name,
                    title = :title,
                    account = :account,
                    project = :project,
                    product = :product,
                    titel = :titel,
                    bullet1 = :bullet1,
                    bullet2 = :bullet2,
                    bullet3 = :bullet3,
                    bullet4 = :bullet4,
                    bullet5 = :bullet5,
                    description = :description,
                    search_terms = :search_terms,
                    keywords = :keywords,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """)
            with engine.begin() as conn:
                conn.execute(update_sql, {
                    "id": result[0],
                    "image": listing_data.get("image"),
                    "name": listing_data.get("name"),
                    "title": listing_data.get("Title") or listing_data.get("title"),
                    "account": account,
                    "project": project,
                    "product": listing_data.get("Product", ""),
                    "titel": listing_data.get("Titel", ""),
                    "bullet1": listing_data.get("Bullet1", ""),
                    "bullet2": listing_data.get("Bullet2", ""),
                    "bullet3": listing_data.get("Bullet3", ""),
                    "bullet4": listing_data.get("Bullet4", ""),
                    "bullet5": listing_data.get("Bullet5", ""),
                    "description": listing_data.get("Description", ""),
                    "search_terms": listing_data.get("SearchTerms", ""),
                    "keywords": listing_data.get("Keywords", "")
                })
            return True
    
    # Neuer Eintrag
    insert_sql = text("""
        INSERT INTO listings (
            asin_ean_sku, mp, image, name, title, account, project,
            product, titel, bullet1, bullet2, bullet3, bullet4, bullet5,
            description, search_terms, keywords
        ) VALUES (
            :asin_ean_sku, :mp, :image, :name, :title, :account, :project,
            :product, :titel, :bullet1, :bullet2, :bullet3, :bullet4, :bullet5,
            :description, :search_terms, :keywords
        )
    """)
    
    try:
        with engine.begin() as conn:
            conn.execute(insert_sql, {
                "asin_ean_sku": asin_ean_sku,
                "mp": mp,
                "image": listing_data.get("image"),
                "name": listing_data.get("name"),
                "title": listing_data.get("Title") or listing_data.get("title"),
                "account": account,
                "project": project,
                "product": listing_data.get("Product", ""),
                "titel": listing_data.get("Titel", ""),
                "bullet1": listing_data.get("Bullet1", ""),
                "bullet2": listing_data.get("Bullet2", ""),
                "bullet3": listing_data.get("Bullet3", ""),
                "bullet4": listing_data.get("Bullet4", ""),
                "bullet5": listing_data.get("Bullet5", ""),
                "description": listing_data.get("Description", ""),
                "search_terms": listing_data.get("SearchTerms", ""),
                "keywords": listing_data.get("Keywords", "")
            })
        return True
    except SQLAlchemyError as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False

def load_listings_from_db(engine, filters=None):
    """Lädt Listings aus der Datenbank mit optionalen Filtern"""
    if not engine:
        return pd.DataFrame()
    
    base_query = "SELECT * FROM listings WHERE 1=1"
    params = {}
    
    if filters:
        if filters.get("asin_ean_sku"):
            base_query += " AND asin_ean_sku ILIKE :asin"
            params["asin"] = f"%{filters['asin_ean_sku']}%"
        if filters.get("mp"):
            base_query += " AND mp = :mp"
            params["mp"] = filters["mp"]
        if filters.get("account"):
            base_query += " AND account ILIKE :account"
            params["account"] = f"%{filters['account']}%"
        if filters.get("project"):
            base_query += " AND project ILIKE :project"
            params["project"] = f"%{filters['project']}%"
        if filters.get("name"):
            base_query += " AND name ILIKE :name"
            params["name"] = f"%{filters['name']}%"
    
    base_query += " ORDER BY updated_at DESC"
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(base_query), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df
    except SQLAlchemyError as e:
        st.error(f"Fehler beim Laden: {e}")
        return pd.DataFrame()

def get_distinct_values(engine, column):
    """Holt alle eindeutigen Werte einer Spalte für Filter-Dropdowns"""
    if not engine:
        return []
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT DISTINCT {column} FROM listings WHERE {column} IS NOT NULL ORDER BY {column}"))
            return [row[0] for row in result.fetchall()]
    except SQLAlchemyError:
        return []

def batch_save_listings_to_db(engine, listings_data, batch_size=100):
    """
    Speichert Listings in Batches für bessere Performance und Fehlerbehandlung.
    
    Args:
        engine: SQLAlchemy Engine
        listings_data: Liste von Dicts mit Listing-Daten
        batch_size: Anzahl der Listings pro Batch (Standard: 100)
    
    Returns:
        tuple: (success_count, error_count, skipped_count, errors)
    """
    if not engine:
        return 0, len(listings_data), 0, ["Keine Datenbankverbindung"]
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    # Verarbeite in Batches
    for batch_start in range(0, len(listings_data), batch_size):
        batch_end = min(batch_start + batch_size, len(listings_data))
        batch = listings_data[batch_start:batch_end]
        
        try:
            # Eine Connection pro Batch
            with engine.begin() as conn:
                for listing_info in batch:
                    listing_data = listing_info["data"]
                    asin = listing_info["asin"]
                    mp = listing_info["mp"]
                    account = listing_info.get("account")
                    project = listing_info.get("project")
                    check_existing = listing_info.get("check_existing", True)
                    overwrite = listing_info.get("overwrite", False)
                    
                    if not asin or not mp:
                        error_count += 1
                        errors.append(f"Fehlende ASIN oder MP")
                        continue
                    
                    # Prüfe ob existiert
                    if check_existing and not overwrite:
                        check_sql = text("SELECT id FROM listings WHERE asin_ean_sku = :asin AND mp = :mp")
                        existing = conn.execute(check_sql, {"asin": asin, "mp": mp}).fetchone()
                        
                        if existing:
                            skipped_count += 1
                            continue
                        else:
                            listing_id = None
                    elif check_existing and overwrite:
                        check_sql = text("SELECT id FROM listings WHERE asin_ean_sku = :asin AND mp = :mp")
                        existing = conn.execute(check_sql, {"asin": asin, "mp": mp}).fetchone()
                        listing_id = existing[0] if existing else None
                    else:
                        listing_id = None
                    
                    if listing_id:
                        # Update
                        update_sql = text("""
                            UPDATE listings SET
                                image = :image, name = :name, title = :title,
                                account = :account, project = :project, product = :product,
                                titel = :titel, bullet1 = :bullet1, bullet2 = :bullet2,
                                bullet3 = :bullet3, bullet4 = :bullet4, bullet5 = :bullet5,
                                description = :description, search_terms = :search_terms,
                                keywords = :keywords, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                        """)
                        conn.execute(update_sql, {
                            "id": listing_id,
                            "image": listing_data.get("image"),
                            "name": listing_data.get("name"),
                            "title": listing_data.get("Title") or listing_data.get("title"),
                            "account": account, "project": project,
                            "product": listing_data.get("Product", ""),
                            "titel": listing_data.get("Titel", ""),
                            "bullet1": listing_data.get("Bullet1", ""),
                            "bullet2": listing_data.get("Bullet2", ""),
                            "bullet3": listing_data.get("Bullet3", ""),
                            "bullet4": listing_data.get("Bullet4", ""),
                            "bullet5": listing_data.get("Bullet5", ""),
                            "description": listing_data.get("Description", ""),
                            "search_terms": listing_data.get("SearchTerms", ""),
                            "keywords": listing_data.get("Keywords", "")
                        })
                        success_count += 1
                    else:
                        # Insert
                        insert_sql = text("""
                            INSERT INTO listings (
                                asin_ean_sku, mp, image, name, title, account, project,
                                product, titel, bullet1, bullet2, bullet3, bullet4, bullet5,
                                description, search_terms, keywords
                            ) VALUES (
                                :asin_ean_sku, :mp, :image, :name, :title, :account, :project,
                                :product, :titel, :bullet1, :bullet2, :bullet3, :bullet4, :bullet5,
                                :description, :search_terms, :keywords
                            )
                        """)
                        conn.execute(insert_sql, {
                            "asin_ean_sku": asin, "mp": mp,
                            "image": listing_data.get("image"),
                            "name": listing_data.get("name"),
                            "title": listing_data.get("Title") or listing_data.get("title"),
                            "account": account, "project": project,
                            "product": listing_data.get("Product", ""),
                            "titel": listing_data.get("Titel", ""),
                            "bullet1": listing_data.get("Bullet1", ""),
                            "bullet2": listing_data.get("Bullet2", ""),
                            "bullet3": listing_data.get("Bullet3", ""),
                            "bullet4": listing_data.get("Bullet4", ""),
                            "bullet5": listing_data.get("Bullet5", ""),
                            "description": listing_data.get("Description", ""),
                            "search_terms": listing_data.get("SearchTerms", ""),
                            "keywords": listing_data.get("Keywords", "")
                        })
                        success_count += 1
                
                # Commit erfolgt automatisch durch engine.begin() context manager
        
        except Exception as batch_error:
            # Fehler bei diesem Batch
            error_count += len(batch)
            error_msg = str(batch_error)[:200]
            errors.append(f"Batch {batch_start//batch_size + 1} (Zeilen {batch_start + 1}-{batch_end}): {error_msg}")
            # Weiter mit nächstem Batch
            continue
    
    return success_count, error_count, skipped_count, errors

st.set_page_config(
    page_title="Amazon Listing Editor",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============ PASSWORT-AUTHENTIFIZIERUNG ============
def check_password():
    """Gibt True zurück, wenn der Nutzer das richtige Passwort eingegeben hat."""
    
    # Prüfe ob bereits eingeloggt
    if "authenticated" in st.session_state and st.session_state["authenticated"]:
        return True
    
    # Lade Passwort aus secrets oder Umgebungsvariable
    correct_password = None
    try:
        if "app_password" in st.secrets:
            correct_password = st.secrets["app_password"]
    except Exception:
        pass
    
    if not correct_password:
        correct_password = os.getenv("APP_PASSWORD")
    
    # Wenn kein Passwort gesetzt ist, erlaube Zugriff (für Entwicklung)
    if not correct_password:
        st.warning("⚠️ **Warnung:** Kein Passwort gesetzt. Setze `app_password` in `.streamlit/secrets.toml` oder `APP_PASSWORD` Umgebungsvariable für Produktion!")
        return True
    
    # Login-Formular anzeigen
    st.title("🔒 Anmeldung erforderlich")
    st.markdown("Bitte gib das Passwort ein, um auf das Tool zuzugreifen.")
    
    password_input = st.text_input(
        "Passwort",
        type="password",
        key="password_input",
        label_visibility="visible"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        login_button = st.button("🔓 Anmelden", type="primary", use_container_width=True)
    
    if login_button:
        if password_input == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ Falsches Passwort!")
            st.session_state["authenticated"] = False
    
    # Footer mit Info
    st.markdown("---")
    st.caption("🔒 Geschützter Bereich - Unauthorisierter Zugriff verboten")
    
    return False

# Prüfe Authentifizierung - zeige Login-Seite wenn nicht eingeloggt
if not check_password():
    st.stop()  # Stoppt die Ausführung, wenn nicht authentifiziert

# ============ MODERNES CSS-DESIGN ============
st.markdown("""
<style>
    /* Hauptfarben basierend auf React-Design */
    :root {
        --primary: hsl(27, 96%, 61%);
        --primary-foreground: hsl(0, 0%, 100%);
        --background: hsl(220, 15%, 97%);
        --foreground: hsl(220, 20%, 10%);
        --card: hsl(0, 0%, 100%);
        --border: hsl(220, 15%, 88%);
        --muted: hsl(220, 15%, 94%);
        --muted-foreground: hsl(220, 10%, 40%);
        --success: hsl(142, 76%, 36%);
        --warning: hsl(38, 92%, 50%);
        --destructive: hsl(0, 84%, 60%);
    }

    /* Hauptcontainer */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header Styling */
    .stApp > header {
        background-color: var(--card);
        border-bottom: 1px solid var(--border);
    }

    /* Titel Styling */
    h1 {
        color: var(--foreground);
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    /* Buttons */
    .stButton > button {
        background: var(--primary);
        color: var(--primary-foreground);
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: hsl(27, 96%, 55%);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Text Areas */
    .stTextArea > div > div > textarea {
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.875rem;
        transition: border-color 0.2s;
    }

    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(27, 96%, 61%, 0.1);
    }

    /* Text Input */
    .stTextInput > div > div > input {
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        transition: border-color 0.2s;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(27, 96%, 61%, 0.1);
    }

    /* File Uploader */
    .stFileUploader > div {
        border: 2px dashed var(--border);
        border-radius: 0.75rem;
        padding: 2rem;
        transition: all 0.3s;
    }

    .stFileUploader > div:hover {
        border-color: var(--primary);
        background: rgba(27, 96%, 61%, 0.05);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        padding: 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }

    .streamlit-expanderHeader:hover {
        background: var(--muted);
    }

    .streamlit-expanderContent {
        background: var(--card);
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 0.5rem 0.5rem;
        padding: 1.5rem;
    }

    /* Progress Bar Container */
    .progress-container {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .progress-bar {
        width: 100%;
        height: 6px;
        background: var(--muted);
        border-radius: 3px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: var(--primary);
        transition: width 0.3s;
        border-radius: 3px;
    }

    .progress-fill.over-limit {
        background: var(--destructive);
    }

    /* Field Label - verbessert */
    .field-label {
        font-weight: 600;
        font-size: 1rem;
        color: var(--foreground);
        line-height: 1.25;
        margin: 1rem 0 0.5rem 0;
        display: inline-block;
        padding: 0.5rem 1rem;
        border-left: 4px solid var(--primary);
        background: var(--muted);
        border-radius: 0.5rem;
    }

    /* Preview Box - verbessert mit Dark Mode Support */
    .preview-box {
        padding: 0.75rem;
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        background: var(--muted);
        margin-top: 0.5rem;
        min-height: 60px;
        color: #1f2937 !important; /* Dunkle Schrift für Light Mode */
    }

    /* Dark Mode Anpassungen - für System Dark Mode */
    @media (prefers-color-scheme: dark) {
        .preview-box {
            background: hsl(220, 18%, 20%) !important;
            color: hsl(220, 10%, 95%) !important;
            border-color: hsl(220, 15%, 30%) !important;
        }
        
        .field-label {
            background: hsl(220, 18%, 25%) !important;
            color: hsl(220, 10%, 95%) !important;
        }
        
        .keyword-chip.unused {
            background: hsl(220, 18%, 25%) !important;
            color: hsl(220, 10%, 85%) !important;
            border-color: hsl(220, 15%, 35%) !important;
        }
        
        .byte-counter.under-limit {
            color: hsl(220, 10%, 75%) !important;
        }
    }
    
    /* Streamlit Dark Mode Support */
    [data-theme="dark"] .preview-box,
    .stApp[data-theme="dark"] .preview-box {
        background: hsl(220, 18%, 20%) !important;
        color: hsl(220, 10%, 95%) !important;
        border-color: hsl(220, 15%, 30%) !important;
    }
    
    [data-theme="dark"] .field-label,
    .stApp[data-theme="dark"] .field-label {
        background: hsl(220, 18%, 25%) !important;
        color: hsl(220, 10%, 95%) !important;
    }
    
    [data-theme="dark"] .keyword-chip.unused,
    .stApp[data-theme="dark"] .keyword-chip.unused {
        background: hsl(220, 18%, 25%) !important;
        color: hsl(220, 10%, 85%) !important;
        border-color: hsl(220, 15%, 35%) !important;
    }
    
    [data-theme="dark"] .byte-counter.under-limit,
    .stApp[data-theme="dark"] .byte-counter.under-limit {
        color: hsl(220, 10%, 75%) !important;
    }

    .preview-box mark {
        background: rgba(27, 96%, 61%, 0.3);
        padding: 0.125rem 0.25rem;
        border-radius: 0.25rem;
        font-weight: 500;
        color: inherit;
    }
    
    /* Dark Mode: Dunklere, weniger grelle Highlight-Farbe für bessere Lesbarkeit */
    @media (prefers-color-scheme: dark) {
        .preview-box mark {
            background: hsl(220, 50%, 35%) !important; /* Dunkles Blau-Grau statt Gelb */
            color: hsl(220, 20%, 95%) !important; /* Helle Schrift */
            border: 1px solid hsl(220, 50%, 45%) !important;
        }
    }
    
    [data-theme="dark"] .preview-box mark,
    .stApp[data-theme="dark"] .preview-box mark {
        background: hsl(220, 50%, 35%) !important; /* Dunkles Blau-Grau statt Gelb */
        color: hsl(220, 20%, 95%) !important; /* Helle Schrift */
        border: 1px solid hsl(220, 50%, 45%) !important;
    }
    
    /* Explizite Textfarbe für alle Text in Preview */
    .preview-box * {
        color: inherit !important;
    }
    
    /* Mark-Tags sollen ihre eigene Farbe behalten */
    .preview-box mark * {
        color: inherit !important;
    }

    /* Byte Counter */
    .byte-counter {
        font-size: 0.75rem;
        margin-top: 0.25rem;
        font-weight: 500;
    }

    .byte-counter.over-limit {
        color: var(--destructive);
        font-weight: 600;
    }

    .byte-counter.under-limit {
        color: var(--muted-foreground);
    }

    /* Keyword Chips - verbessert */
    .keyword-chip {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.125rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        border: 1px solid var(--border);
        transition: all 0.2s;
    }

    .keyword-chip.used {
        background: #d4edda;
        border-color: var(--success);
        color: #155724;
    }

    .keyword-chip.unused {
        background: var(--muted);
        border-color: var(--border);
        color: var(--muted-foreground);
    }

    /* Cards für Sections */
    .section-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    /* Hide Streamlit default elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Download Button */
    .stDownloadButton > button {
        background: var(--primary);
        color: var(--primary-foreground);
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stDownloadButton > button:hover {
        background: hsl(27, 96%, 55%);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============ DATENBANK-VERBINDUNG ============
db_engine = get_db_connection()
if db_engine:
    init_database(db_engine)

# Header mit Logout-Button
col_title, col_logout = st.columns([4, 1])
with col_title:
    st.title("🛠️ Amazon Listing Editor mit Keyword-Highlighting")
with col_logout:
    if st.button("🚪 Abmelden", key="btn_logout", help="Von der Anwendung abmelden"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- Content-Richtlinien & Workflow (ausklappbar) ---
with st.expander("📋 Content-Richtlinien & Workflow", expanded=False):
    st.markdown("""
    ### 🎯 Vorbereitung Content
    
    **Produkt studieren**
    - Infos sammeln (Website, evtl. bestehendes Amazon Listing, Googlesuche)
    - USPs ausarbeiten
    
    **Zielgruppe definieren**
    - Wer kauft das Produkt?
    - Ist es teuer oder günstig?
    - Wie ist die Qualität?
    - Welchen Standard hat ein Kunde, der dieses Produkt kaufen würde?
    - Spreche ich über etwas technisches oder emotionales?
    - Wie komplex ist das Produkt?
    - Ist Produkterklärung oder Produktgefühl wichtiger?
    
    **Bestehende Kundenbewertungen berücksichtigen**
    - Treten Fragen oder Punkte öfter auf?
    - Bleiben dem Kunden aktuell Fragen offen, die ich im neuen Listing direkt klarstellen will?
    
    **Saisonalitäten**
    - Müssen Saisonalitäten berücksichtigt werden?
    
    ---
    
    ### 🏢 Kunden Standards / Brand Guides
    
    **Do's & Dont's in Bezug auf Formulierungen**
    - Schreibweisen, gleichbleibende Bulletpoints
    - Schreibweise des Brand/Product Name
    - Ansprache (im Zweifel: neutrale Formulierung ohne Duzen/Siezen)
    - Slogans, Formulierungen, Wörter, Infos, die immer und überall genannt werden
    
    **Verbotene Begriffe**
    - Von Kundenseite (z.B. "Bluetooth" darf aus Lizenzgründen nicht genannt werden, "Hartje" ist verboten, bedingt durch Übermarke/Unternehmensstrukturen usw.)
    
    ---
    
    ### 🔍 Keywordrecherche
    
    - **Brainstorming**
    - **AMALYTIX**
    - **Amazon Suggest + Suchergebnisse**
    - **Wettbewerbslistings**
    - **ChatGPT** (Hinterfragen!)
    - **Google**
    - **Rezensionen**
    
    **Ausarbeitung der Inhalte für KI**
    - Vorbereiten einer Datei für KI-Listing
    - Manueller Doublecheck der Datei
    - Abgleich der Datei mit Standards (siehe oben)
    
    ---
    
    ### 📝 Allgemeine Content Richtlinien
    
    - ✅ **Bindestrich-Schreibweise nutzen!**
    - ✅ **Keyword Priorisierung** (1. Titel, 2. Search Terms, 3. Bulletpoints, 4. Description)
    - ❌ **Keine Fremdmarken erwähnen**
    - ❌ **Keine werbenden Formulierungen:** Garantieversprechen, Wirkversprechen, Preis, Rabatte, Wettbewerber nennen oder "klein machen", CTAs
    - ❌ **Nicht zugelassene Zeichen:** `!`, `$`, `?`, `_`, `{`, `}`, `^`, `¬`
    - ❌ **Keine Privaten Informationen** wie E-Mail-Adressen etc.
    - ❌ **Keine vulgären Ausdrücke**
    - ❌ **Kein wiederholender Text, Spam, mit Symbolen erstellte Bilder**
    - ❌ **Keine externe Links**
    - ❌ **Keine Plagiate**
    - ⚖️ **Spagat zwischen Keyword-Stuffing und seriöser Ansprache gewährleisten**
    
    ---
    
    ### ⚠️ Mögliche Hürden - aber keine direkte Richtlinie
    
    > Damit sind Gründe für Ablehnungen gemeint, die schonmal bei Produkten aufgekommen sind, die aber eigentlich gegen keine Richtlinie verstoßen:
    
    - Nicht zugelassene Begriffe (`ideal`, `perfekt`)
    - Dopplungen im Titel verboten
    - Kein Marken-Bullet am Ende erlaubt
    
    ---
    
    ### ✅ Nachbereitung Content
    
    > **MERKE:** Die Qualität der Vorbereitung entscheidet darüber, wie aufwändig die Nachbereitung wird!  
    > Je genauer und vollständiger die Infos sind, die wir der KI geben, desto genauer wird der Output.
    
    **Was machen wir, nachdem die KI uns ein Listing ausgespuckt hat?**
    
    Denn, **KI macht Fehler!**
    - KI kann (häufig) keine Bytes zählen
    - Formulierungen hören sich häufig komisch/falsch an
    - KI kriegt keine Priorisierung hin
    - KI erfindet Dinge dazu oder nennt falsche Informationen
    
    **Korrekturschleife Fact Check**
    - Brand Guides abgleichen
    - Produktinfos auf Richtigkeit prüfen
    - Keyword-Verwendung checken
    - Einhaltung der Richtlinien checken
    - ➡️ **Check-Liste durchgehen!!**
    
    **Korrekturschleife Rechtschreibung**
    - Rechtschreibcheck
    
    > **Ganz wichtig:** Auch wenn die KI uns die SEO-Contenterstellung erleichtert, passieren häufig später bei uns auch in der Nachbereitung Copy/Paste und Flüchtigkeitsfehler.  
    > Ein SEO Listing ist reine Fleißarbeit und erfordert enorme Konzentration, da sich sonst schnell Flüchtigkeitsfehler einschleichen.  
    > **Bitte gebt ein Listing erst an den Owner, wenn ihr es ausgiebig kontrolliert habt und der Meinung seid, dass ihr es so dem Kunden direkt schicken würdet.**
    
    **Korrekturschleife Owner**
    - Erst an den Owner in Korrekturschleife geben, wenn alle oben genannten Punkte vollständig erfüllt sind
    - Owner prüft nur Flüchtigkeitsfehler, keine Inhalte
    
    **Korrekturschleife vom Kunden**
    - Nur für Wünsche/Verbesserungen
    """)

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

st.info("💡 **Hinweis:** Mindestens eines der Felder 'Produktname', 'Produktspezifikationen' oder 'USPs' sollte ausgefüllt sein. Alle anderen Felder sind optional, helfen aber der KI dabei, bessere und genauere Listings zu erstellen.")

# Strukturierte Input-Felder basierend auf Content-Richtlinien
with st.expander("📝 Produktinformationen", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input(
            "Produktname * (empfohlen)",
            placeholder="z.B. Brotbox Edelstahl",
            key="input_product_name",
            help="Mindestens eines der markierten Felder sollte ausgefüllt sein"
        )
        product_specs = st.text_area(
            "Produktspezifikationen & Details * (empfohlen)",
            placeholder="z.B. 1.2 L Volumen, BPA-frei, Farbe Silber, Maße 20x15x8 cm, Material: Edelstahl 18/10",
            height=100,
            key="input_product_specs",
            help="Mindestens eines der markierten Felder sollte ausgefüllt sein"
        )
    with col2:
        target_audience = st.text_area(
            "Zielgruppe (optional)",
            placeholder="z.B. Gesundheitsbewusste Verbraucher, Familien, Preis-Leistungs-Orientiert, Qualitätsbewusst",
            height=80,
            key="input_target_audience"
        )
        seasonal_info = st.text_input(
            "Saisonalitäten (optional)",
            placeholder="z.B. Besonders beliebt im Sommer, Geschenkidee zu Weihnachten",
            key="input_seasonal"
        )

with st.expander("🎯 USPs & Verkaufsargumente", expanded=False):
    usps = st.text_area(
        "Unique Selling Points (USPs) * (empfohlen)",
        placeholder="z.B. Auslaufsicher, spülmaschinenfest, umweltfreundlich, langlebig, geruchsneutral",
        height=100,
        key="input_usps",
        help="Mindestens eines der markierten Felder sollte ausgefüllt sein"
    )

with st.expander("💬 Kundenbewertungen & Häufige Fragen (optional)", expanded=False):
    customer_feedback = st.text_area(
        "Häufige Fragen aus Bewertungen oder wichtige Punkte, die geklärt werden sollten",
        placeholder="z.B. Kunden fragen oft nach Kompatibilität mit Geschirrspüler, Größe für Familien, Geruchsbildung",
        height=100,
        key="input_customer_feedback"
    )

with st.expander("🏢 Brand Guidelines & Formulierungen (optional)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        brand_name_format = st.text_input(
            "Brand/Product Name Schreibweise (optional)",
            placeholder="z.B. BRANDNAME oder Brand-Name (genau wie es verwendet werden soll)",
            key="input_brand_format"
        )
        required_formulations = st.text_area(
            "Immer zu verwendende Slogans/Formulierungen/Wörter (optional)",
            placeholder="z.B. 'Premium-Qualität', 'Made in Germany', bestimmte technische Begriffe die immer genannt werden müssen",
            height=100,
            key="input_required_formulations"
        )
    with col2:
        forbidden_terms = st.text_area(
            "❌ Verbotene Begriffe (optional)",
            placeholder="z.B. Bluetooth, Hartje, Garantie, perfekt, ideal (kommagetrennt auflisten)",
            height=130,
            key="input_forbidden_terms"
        )

with st.expander("🔍 Keywords (optional)", expanded=False):
    keywords_input = st.text_area(
        "Recherchierte Keywords (kommagetrennt oder Zeilenumbruch)",
        placeholder="z.B. brotbox edelstahl, lunchbox, meal prep, auslaufsicher, spülmaschinenfest",
        height=100,
        key="input_keywords"
    )

def _build_prompt(input_data: dict) -> str:
    # Baue strukturierten Kontext aus allen Eingabefeldern
    context_parts = []
    
    if input_data.get("product_name"):
        context_parts.append(f"Produktname: {input_data['product_name']}")
    
    if input_data.get("product_specs"):
        context_parts.append(f"Produktspezifikationen: {input_data['product_specs']}")
    
    if input_data.get("usps"):
        context_parts.append(f"USPs und Verkaufsargumente: {input_data['usps']}")
    
    if input_data.get("target_audience"):
        context_parts.append(f"Zielgruppe: {input_data['target_audience']}")
    
    if input_data.get("customer_feedback"):
        context_parts.append(f"Wichtige Punkte aus Kundenbewertungen: {input_data['customer_feedback']}")
    
    if input_data.get("seasonal_info"):
        context_parts.append(f"Saisonalitäten: {input_data['seasonal_info']}")
    
    if input_data.get("brand_name_format"):
        context_parts.append(f"Brand/Product Name Schreibweise (genau so verwenden): {input_data['brand_name_format']}")
    
    if input_data.get("required_formulations"):
        context_parts.append(f"Immer zu verwendende Formulierungen/Slogans: {input_data['required_formulations']}")
    
    if input_data.get("forbidden_terms"):
        context_parts.append(f"VERBOTENE BEGRIFFE (niemals verwenden): {input_data['forbidden_terms']}")
    
    if input_data.get("keywords"):
        context_parts.append(f"Keywords für das Produkt: {input_data['keywords']}")
    
    user_context = "\n".join(context_parts) if context_parts else "Keine spezifischen Angaben"
    
    # Prompt mit allen Richtlinien
    return f"""
Du bist Amazon Copywrighter und musst mir für nachfolgendes Produkt die Bullet Points, Description und Search Terms schreiben. Sprache des Listings ist deutsch.

WICHTIGE RICHTLINIEN:
- KEINE Garantieversprechen (keine Worte wie "perfekt", "garantiert", "ideal")
- KEINE werbenden Formulierungen (keine Wirkversprechen, keine Preise, keine Rabatte, keine CTAs)
- KEINE verbotenen Zeichen verwenden: !, $, ?, _, {{, }}, ^, ¬
- KEINE Fremdmarken erwähnen
- Bindestrich-Schreibweise nutzen!
- Keyword Priorisierung: 1. Titel, 2. Search Terms, 3. Bulletpoints, 4. Description

Hier ist der Aufbau der Felder:

Titel: besteht aus 140-150 Zeichen, beginnt mit dem Produktnamen, danach die Key-Features und am Ende Dinge wie Farbe oder Stückzahl, falls vorhanden

Bullet Points: Insgesamt fünf Stück, bestehen aus 190-200 Zeichen, starten mit jeweils zwei Worten in Versalien und einem Doppelpunkt. Sie enden jeweils ohne Punktuation. Achte darauf, dass die Bullet Points jeweils ein übergeordnetes Thema haben. Ebenso sollen sie nach dem Doppelpunkt aus einem kompletten deutschen Satz bestehen.

Description: besteht aus 3 Absätzen mit jeweils einer kurzen Überschrift. Insgesamt hat diese 1600-1800 Zeichen.

Search Terms: haben insgesamt 220-250 Zeichen und stellen nur Keywords dar, vor allem die, die im vorherigen Content nicht genutzt wurden. Schreibe sie ohne Komma oder ähnliches hintereinander weg.

PRODUKTINFORMATIONEN:

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
            ]
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
    # Sammle alle Eingabefelder
    input_data = {
        "product_name": st.session_state.get("input_product_name", ""),
        "product_specs": st.session_state.get("input_product_specs", ""),
        "usps": st.session_state.get("input_usps", ""),
        "target_audience": st.session_state.get("input_target_audience", ""),
        "customer_feedback": st.session_state.get("input_customer_feedback", ""),
        "seasonal_info": st.session_state.get("input_seasonal", ""),
        "brand_name_format": st.session_state.get("input_brand_format", ""),
        "required_formulations": st.session_state.get("input_required_formulations", ""),
        "forbidden_terms": st.session_state.get("input_forbidden_terms", ""),
        "keywords": st.session_state.get("input_keywords", ""),
    }
    
    # Prüfe ob mindestens Grundinformationen vorhanden sind
    has_basic_info = input_data["product_name"].strip() or input_data["product_specs"].strip() or input_data["usps"].strip()
    
    if not has_basic_info:
        st.warning("⚠️ Bitte fülle mindestens die Felder 'Produktname', 'Produktspezifikationen' oder 'USPs' aus.")
    else:
        with st.spinner("🤖 Generiere Listing mit KI..."):
            prompt = _build_prompt(input_data)
            result = _call_openai_and_parse(prompt)
        if result:
            # Generiertes Listing in identisches Datenformat bringen
            product_name_for_listing = input_data["product_name"].strip() or "Generiert aus Kontext"
            keywords_for_listing = input_data["keywords"].strip() or ""
            
            st.session_state["generated_rows"].append({
                "Product": product_name_for_listing,
                "Titel": result.get("Titel", ""),
                "Bullet1": result.get("Bullet1", ""),
                "Bullet2": result.get("Bullet2", ""),
                "Bullet3": result.get("Bullet3", ""),
                "Bullet4": result.get("Bullet4", ""),
                "Bullet5": result.get("Bullet5", ""),
                "Description": result.get("Description", ""),
                "SearchTerms": result.get("SearchTerms", ""),
                "Keywords": keywords_for_listing
            })
            st.success("Inhalte generiert. Scrolle nach unten – das Listing erscheint in der Bearbeitungsmaske.")

# ================== DATENBANK-FUNKTIONEN ==================

# Datenbankansicht mit Filtern
if db_engine:
    st.markdown("---")
    st.header("💾 Datenbank-Verwaltung")
    
    db_tabs = st.tabs(["📊 Gespeicherte Listings", "⬆️ Supabase Upload", "⬆️ Optimierungen hochladen"])
    
    with db_tabs[0]:
        st.subheader("Filter & Suche")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_asin = st.text_input("ASIN/EAN/SKU", key="filter_asin")
            filter_mp = st.selectbox(
                "Marketplace",
                options=[""] + get_distinct_values(db_engine, "mp"),
                key="filter_mp"
            )
        
        with col2:
            filter_account = st.selectbox(
                "Account",
                options=[""] + get_distinct_values(db_engine, "account"),
                key="filter_account"
            )
        
        with col3:
            filter_project = st.selectbox(
                "Project",
                options=[""] + get_distinct_values(db_engine, "project"),
                key="filter_project"
            )
        
        with col4:
            filter_name = st.text_input("Produktname", key="filter_name")
        
        filters = {
            "asin_ean_sku": filter_asin if filter_asin else None,
            "mp": filter_mp if filter_mp else None,
            "account": filter_account if filter_account else None,
            "project": filter_project if filter_project else None,
            "name": filter_name if filter_name else None
        }
        filters = {k: v for k, v in filters.items() if v}
        
        col_filter_btn, col_reset_btn = st.columns([1, 1])
        with col_filter_btn:
            if st.button("🔍 Filtern", key="btn_filter", use_container_width=True):
                st.session_state["db_filters"] = filters
                st.rerun()
        
        with col_reset_btn:
            if st.button("🔄 Filter zurücksetzen", key="btn_reset_filters", use_container_width=True):
                if "db_filters" in st.session_state:
                    del st.session_state["db_filters"]
                st.rerun()
        
        if "db_filters" in st.session_state:
            filters = st.session_state["db_filters"]
        
        # Debug: Zeige Filter-Status und Gesamtzahl
        if db_engine:
            try:
                with db_engine.connect() as conn:
                    total_count_result = conn.execute(text("SELECT COUNT(*) as total FROM listings"))
                    total_count = total_count_result.fetchone()[0]
                    
                    if filters:
                        st.info(f"🔍 **Aktive Filter:** {len(filters)} Filter gesetzt. **Gesamt in DB:** {total_count} Listings")
                    else:
                        st.info(f"📊 **Gesamt in Datenbank:** {total_count} Listings")
            except Exception as e:
                st.warning(f"⚠️ Konnte Gesamtzahl nicht ermitteln: {e}")
        
        # Lade gefilterte Daten
        db_df = load_listings_from_db(db_engine, filters if filters else None)
        
        if not db_df.empty:
            st.subheader(f"Gefundene Listings ({len(db_df)})")
            
            # Debug: Zeige zusätzliche Info wenn Filter aktiv
            if filters:
                st.warning(f"⚠️ **Hinweis:** Es werden nur {len(db_df)} Listings angezeigt, da Filter aktiv sind. Gesamt in DB: {total_count if 'total_count' in locals() else 'unbekannt'}")
            
            # Zeige nur relevante Spalten in der Übersicht
            display_cols = ["asin_ean_sku", "mp", "name", "account", "project", "updated_at"]
            available_display_cols = [col for col in display_cols if col in db_df.columns]
            
            if available_display_cols:
                st.dataframe(
                    db_df[available_display_cols],
                    use_container_width=True,
                    height=400
                )
            
            # Detailansicht für einzelnes Listing
            if len(db_df) > 0:
                st.subheader("Listing-Details bearbeiten")
                selected_idx = st.selectbox(
                    "Listing auswählen",
                    options=range(len(db_df)),
                    format_func=lambda x: f"{db_df.iloc[x].get('name', 'Unbekannt')} - {db_df.iloc[x].get('asin_ean_sku', 'N/A')}",
                    key="selected_listing"
                )
                
                if selected_idx is not None:
                    selected_row = db_df.iloc[selected_idx]
                    
                    # Metadaten anzeigen
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**ASIN/EAN/SKU:** {selected_row.get('asin_ean_sku', 'N/A')}")
                    with col2:
                        st.info(f"**Marketplace:** {selected_row.get('mp', 'N/A')}")
                    with col3:
                        st.info(f"**Letzte Änderung:** {selected_row.get('updated_at', 'N/A')}")
                    
                    # Button zum Laden in Bearbeitungsmaske
                    if st.button("✏️ In Bearbeitungsmaske laden", key="btn_load_to_editor", type="primary"):
                        # Initialisiere Liste falls nicht vorhanden
                        if "db_listings_for_edit" not in st.session_state:
                            st.session_state["db_listings_for_edit"] = []
                        
                        # Erstelle neues Listing-Objekt mit eindeutiger ID
                        new_listing = {
                            "id": str(uuid.uuid4()),  # Eindeutige ID für jedes Listing
                            "Product": selected_row.get("product", ""),
                            "Titel": selected_row.get("titel", ""),
                            "Bullet1": selected_row.get("bullet1", ""),
                            "Bullet2": selected_row.get("bullet2", ""),
                            "Bullet3": selected_row.get("bullet3", ""),
                            "Bullet4": selected_row.get("bullet4", ""),
                            "Bullet5": selected_row.get("bullet5", ""),
                            "Description": selected_row.get("description", ""),
                            "SearchTerms": selected_row.get("search_terms", ""),
                            "Keywords": selected_row.get("keywords", ""),
                            "asin_ean_sku": selected_row.get("asin_ean_sku", ""),
                            "mp": selected_row.get("mp", ""),
                            "account": selected_row.get("account", ""),
                            "project": selected_row.get("project", ""),
                            "name": selected_row.get("name", "")
                        }
                        
                        # Prüfe ob Listing bereits geladen ist (basierend auf ASIN + MP)
                        listing_exists = any(
                            listing.get("asin_ean_sku") == new_listing["asin_ean_sku"] and 
                            listing.get("mp") == new_listing["mp"]
                            for listing in st.session_state["db_listings_for_edit"]
                        )
                        
                        if listing_exists:
                            st.warning("⚠️ Dieses Listing ist bereits in der Bearbeitungsmaske geladen.")
                        else:
                            st.session_state["db_listings_for_edit"].append(new_listing)
                            st.success("✅ Listing in Bearbeitungsmaske geladen! Scrolle nach unten zur Bearbeitung.")
                        st.rerun()
        else:
            st.info("Keine Listings gefunden. Verwende die Filter oder lade Optimierungen hoch.")
    
    with db_tabs[1]:
        st.subheader("📤 Supabase Upload")
        st.markdown("""
        **Lade deine Excel-Datei hoch, um Listings direkt in die Supabase Datenbank zu importieren.**
        
        Diese Funktion ist speziell für den reinen Datenbank-Upload gedacht und getrennt vom normalen Bearbeitungs-Workflow.
        """)
        
        supabase_upload_file = st.file_uploader(
            "📤 Excel-Datei für Supabase-Upload",
            type=["xlsx"],
            key="supabase_upload_file",
            help="Wähle eine Excel-Datei mit deinen Listings aus"
        )
        
        if supabase_upload_file:
            try:
                upload_df = pd.read_excel(supabase_upload_file)
                
                # Zeige Spalten-Info
                st.markdown("**Erkannte Spalten:**")
                st.code(", ".join(upload_df.columns.tolist()))
                
                # Spaltennamen normalisieren (flexibler) - vermeide Duplikate
                column_mapping = {}
                used_target_names = set()  # Verhindere doppelte Zielnamen
                
                for col in upload_df.columns:
                    col_lower = str(col).strip().lower()
                    target_name = None
                    
                    # Prüfe jeden Zielnamen und verwende nur den ersten Treffer
                    if "asin" in col_lower or "ean" in col_lower or "sku" in col_lower:
                        target_name = "asin_ean_sku"
                    elif col_lower == "mp" or col_lower == "marketplace":
                        target_name = "mp"
                    elif col_lower == "name" or col_lower == "produktname":
                        target_name = "name"
                    elif col_lower == "title" or col_lower == "titel":
                        target_name = "Titel"  # Wichtig: "Titel" mit großem T für deutsche Bearbeitungsmaske
                    elif col_lower == "account":
                        target_name = "account"
                    elif col_lower == "project" or col_lower == "projekt":
                        target_name = "project"
                    elif col_lower == "image" or col_lower == "bild":
                        target_name = "image"
                    
                    # Nur mappen, wenn Zielname noch nicht verwendet wurde
                    if target_name and target_name not in used_target_names:
                        column_mapping[col] = target_name
                        used_target_names.add(target_name)
                
                upload_df = upload_df.rename(columns=column_mapping)
                
                # Prüfe ob erforderliche Spalten vorhanden
                has_required = "asin_ean_sku" in upload_df.columns and "mp" in upload_df.columns
                
                if not has_required:
                    st.error("❌ Die Datei muss Spalten für ASIN/EAN/SKU und MP enthalten!")
                    st.info("💡 Gefundene Spaltennamen werden automatisch erkannt. Falls die Erkennung nicht funktioniert, benenne die Spalten um.")
                else:
                    st.success(f"✅ {len(upload_df)} Zeilen erfolgreich geladen")
                    
                    # Zeige Vorschau
                    st.markdown("**Vorschau (erste 5 Zeilen):**")
                    preview_cols = ["asin_ean_sku", "mp", "name", "account", "project"]
                    available_preview_cols = [c for c in preview_cols if c in upload_df.columns]
                    if available_preview_cols:
                        st.dataframe(upload_df[available_preview_cols].head(), use_container_width=True)
                    else:
                        st.dataframe(upload_df.head(), use_container_width=True)
                    
                    # Upload-Optionen
                    col1, col2 = st.columns(2)
                    with col1:
                        overwrite_existing_supabase = st.checkbox(
                            "Bestehende Einträge überschreiben",
                            value=False,
                            help="Wenn aktiviert, werden bestehende Listings (gleiche ASIN + MP) aktualisiert. Sonst werden sie übersprungen.",
                            key="overwrite_supabase"
                        )
                    
                    with col2:
                        show_details_supabase = st.checkbox(
                            "Details beim Upload anzeigen",
                            value=True,
                            key="show_details_supabase"
                        )
                    
                    if st.button("💾 In Supabase speichern", key="btn_supabase_save", type="primary"):
                        # Bereite Daten für Batch-Upload vor
                        listings_to_save = []
                        
                        if show_details_supabase:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            status_text.text("Bereite Daten vor...")
                        else:
                            progress_bar = None
                            status_text = None
                        
                        # Sammle alle Listings
                        for idx, row in upload_df.iterrows():
                            if show_details_supabase and progress_bar:
                                progress_bar.progress((idx + 1) / len(upload_df) * 0.5)  # 50% für Vorbereitung
                            
                            listing_data = {
                                "Product": str(row.get("Product", "")),
                                "Titel": str(row.get("Titel", "")),
                                "Bullet1": str(row.get("Bullet1", "")),
                                "Bullet2": str(row.get("Bullet2", "")),
                                "Bullet3": str(row.get("Bullet3", "")),
                                "Bullet4": str(row.get("Bullet4", "")),
                                "Bullet5": str(row.get("Bullet5", "")),
                                "Description": str(row.get("Description", "")),
                                "SearchTerms": str(row.get("SearchTerms", "")),
                                "Keywords": str(row.get("Keywords", "")),
                                "name": str(row.get("name", "")),
                                "image": str(row.get("image", "")) if "image" in row and pd.notna(row.get("image")) else None
                            }
                            
                            asin = str(row.get("asin_ean_sku", "")).strip()
                            mp = str(row.get("mp", "")).strip()
                            account = str(row.get("account", "")).strip() if "account" in row and pd.notna(row.get("account")) else None
                            project = str(row.get("project", "")).strip() if "project" in row and pd.notna(row.get("project")) else None
                            
                            if asin and mp:
                                listings_to_save.append({
                                    "data": listing_data,
                                    "asin": asin,
                                    "mp": mp,
                                    "account": account,
                                    "project": project,
                                    "check_existing": True,
                                    "overwrite": overwrite_existing_supabase
                                })
                        
                        # Batch-Upload durchführen
                        if show_details_supabase and status_text:
                            status_text.text(f"Speichere {len(listings_to_save)} Listings in Batches...")
                        
                        success_count, error_count, skipped_count, errors = batch_save_listings_to_db(
                            db_engine, 
                            listings_to_save, 
                            batch_size=100
                        )
                        
                        if show_details_supabase and progress_bar:
                            progress_bar.progress(1.0)  # 100% fertig
                        
                        if show_details_supabase and progress_bar:
                            progress_bar.empty()
                        if show_details_supabase and status_text:
                            status_text.empty()
                        
                        # Ergebnis anzeigen mit detaillierten Debug-Infos
                        st.markdown("### 📊 Upload-Statistik")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Gesamt verarbeitet", len(upload_df))
                        with col2:
                            st.metric("✅ Erfolgreich", success_count, delta=f"{success_count/len(upload_df)*100:.1f}%")
                        with col3:
                            st.metric("⏭️ Übersprungen", skipped_count, delta=f"{skipped_count/len(upload_df)*100:.1f}%")
                        with col4:
                            st.metric("❌ Fehler", error_count, delta=f"{error_count/len(upload_df)*100:.1f}%")
                        
                        # Debug: Prüfe tatsächliche Anzahl in DB nach Upload
                        if db_engine:
                            try:
                                with db_engine.connect() as conn:
                                    count_after = conn.execute(text("SELECT COUNT(*) FROM listings")).fetchone()[0]
                                    st.info(f"📊 **Aktuelle Anzahl in Datenbank nach Upload:** {count_after} Listings")
                            except Exception:
                                pass
                        
                        if success_count > 0:
                            st.success(f"✅ **{success_count}** Listings erfolgreich in Supabase gespeichert!")
                        if skipped_count > 0:
                            st.info(f"⏭️ **{skipped_count}** Listings übersprungen (bereits vorhanden - gleiche ASIN + MP Kombination)")
                        if error_count > 0:
                            st.warning(f"⚠️ **{error_count}** Listings konnten nicht gespeichert werden")
                            if errors and len(errors) <= 20:
                                with st.expander("Fehler-Details anzeigen"):
                                    for error in errors:
                                        st.text(error)
                            elif errors:
                                with st.expander("Fehler-Details anzeigen (erste 20)"):
                                    for error in errors[:20]:
                                        st.text(error)
                        
                        if success_count > 0 or skipped_count > 0:
                            st.balloons()
                            st.info("💡 Gehe zu 'Gespeicherte Listings' um die importierten Daten zu sehen und zu filtern.")
                            
            except Exception as e:
                st.error(f"❌ Fehler beim Verarbeiten der Datei: {e}")
                st.exception(e)
    
    with db_tabs[2]:
        st.subheader("Bestehende Optimierungen hochladen")
        st.markdown("""
        Lade eine Excel-Datei hoch, um bestehende Optimierungen in die Datenbank zu importieren.
        
        **Erforderliche Spalten:**
        - `ASIN / EAN / SKU` (oder `ASIN_EAN_SKU`)
        - `MP` (Marketplace, z.B. DE)
        - `Account` (optional)
        - `Project` (optional)
        - `Name` (Produktname)
        - `Product`, `Titel`, `Bullet1-5`, `Description`, `SearchTerms`, `Keywords`
        """)
        
        upload_file_db = st.file_uploader(
            "📤 Excel-Datei für Datenbank-Upload",
            type=["xlsx"],
            key="upload_db"
        )
        
        if upload_file_db:
            try:
                upload_df = pd.read_excel(upload_file_db)
                
                # Spaltennamen normalisieren - vermeide Duplikate
                column_mapping = {}
                used_target_names = set()
                
                # Definiere Mapping-Regeln (Zielname -> mögliche Quellspalten)
                mapping_rules = {
                    "asin_ean_sku": ["ASIN / EAN / SKU", "ASIN_EAN_SKU", "asin_ean_sku", "ASIN", "EAN", "SKU"],
                    "mp": ["MP", "mp", "Marketplace", "marketplace"],
                    "name": ["Name", "name", "Produktname", "produktname"],
                    "Titel": ["Title", "title", "Titel", "titel"],  # Wichtig: "Titel" mit großem T
                    "account": ["Account", "account"],
                    "project": ["Project", "project", "Projekt", "projekt"]
                }
                
                # Finde erste passende Spalte für jeden Zielnamen
                for target_name, possible_sources in mapping_rules.items():
                    if target_name not in used_target_names:
                        for source_name in possible_sources:
                            if source_name in upload_df.columns:
                                column_mapping[source_name] = target_name
                                used_target_names.add(target_name)
                                break
                
                # Zusätzlich: Suche nach ähnlichen Spaltennamen (flexibler)
                for col in upload_df.columns:
                    if col not in column_mapping:  # Nur wenn noch nicht gemappt
                        col_lower = str(col).strip().lower()
                        target_name = None
                        
                        if ("asin" in col_lower or "ean" in col_lower or "sku" in col_lower) and "asin_ean_sku" not in used_target_names:
                            target_name = "asin_ean_sku"
                        elif (col_lower == "mp" or "marketplace" in col_lower) and "mp" not in used_target_names:
                            target_name = "mp"
                        elif (col_lower == "name" or col_lower == "produktname") and "name" not in used_target_names:
                            target_name = "name"
                        elif (col_lower == "title" or col_lower == "titel") and "Titel" not in used_target_names:
                            target_name = "Titel"  # Wichtig: "Titel" mit großem T für deutsche Bearbeitungsmaske
                        elif col_lower == "account" and "account" not in used_target_names:
                            target_name = "account"
                        elif (col_lower == "project" or col_lower == "projekt") and "project" not in used_target_names:
                            target_name = "project"
                        
                        if target_name:
                            column_mapping[col] = target_name
                            used_target_names.add(target_name)
                
                upload_df = upload_df.rename(columns=column_mapping)
                
                st.success(f"✅ {len(upload_df)} Zeilen erfolgreich geladen")
                st.dataframe(upload_df.head(), use_container_width=True)
                
                if st.button("💾 In Datenbank speichern", key="btn_save_to_db"):
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, row in upload_df.iterrows():
                        status_text.text(f"Speichere Zeile {idx + 1} von {len(upload_df)}...")
                        progress_bar.progress((idx + 1) / len(upload_df))
                        
                        listing_data = {
                            "Product": str(row.get("Product", "")),
                            "Titel": str(row.get("Titel", "")),
                            "Bullet1": str(row.get("Bullet1", "")),
                            "Bullet2": str(row.get("Bullet2", "")),
                            "Bullet3": str(row.get("Bullet3", "")),
                            "Bullet4": str(row.get("Bullet4", "")),
                            "Bullet5": str(row.get("Bullet5", "")),
                            "Description": str(row.get("Description", "")),
                            "SearchTerms": str(row.get("SearchTerms", "")),
                            "Keywords": str(row.get("Keywords", "")),
                            "name": str(row.get("name", "")),
                            "image": str(row.get("image", "")) if "image" in row else None
                        }
                        
                        asin = str(row.get("asin_ean_sku", "")).strip()
                        mp = str(row.get("mp", "")).strip()
                        account = str(row.get("account", "")).strip() if pd.notna(row.get("account")) else None
                        project = str(row.get("project", "")).strip() if pd.notna(row.get("project")) else None
                        
                        if asin and mp:
                            if save_listing_to_db(db_engine, listing_data, asin, mp, account, project):
                                success_count += 1
                            else:
                                error_count += 1
                        else:
                            error_count += 1
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count} Listings erfolgreich gespeichert!")
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} Listings konnten nicht gespeichert werden (fehlende ASIN/MP)")
                    
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten der Datei: {e}")

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

# Session State für Upload-Modus
if "upload_mode" not in st.session_state:
    st.session_state["upload_mode"] = None  # None, "preview", "edit", "save"
if "uploaded_df" not in st.session_state:
    st.session_state["uploaded_df"] = None
if "show_edit_interface" not in st.session_state:
    st.session_state["show_edit_interface"] = False

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
            def render_field(field_name, limit):
                st.markdown(f"<div class='field-label'>{field_name}</div>", unsafe_allow_html=True)
                value = st.text_area(field_name, value=str(row.get(field_name, "")), key=f"{field_name}_{i}", label_visibility="collapsed", height=90)
                blen = byte_length(value)
                is_over = blen > limit
                percentage = min((blen / limit) * 100, 100)
                counter_class = "over-limit" if is_over else "under-limit"
                progress_class = "over-limit" if is_over else ""
                st.markdown(f"<div class='byte-counter {counter_class}'>Bytes: {blen} / {limit}</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill {progress_class}" style="width: {percentage}%"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                preview = highlight_keywords(value, keywords)
                st.markdown(f"<div class='preview-box'>{preview if preview else '<em>Kein Inhalt</em>'}</div>", unsafe_allow_html=True)
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
            f"<span class='keyword-chip {'used' if kw in used else 'unused'}'>{kw}</span>"
            for kw in keywords
        )
        with col1:
            st.markdown(chips, unsafe_allow_html=True)

    return listing_data

# ---- 1) Upload mit Vorschau und Auswahl ----
if uploaded_file:
    # Reset wenn neue Datei hochgeladen wird
    if st.session_state.get("upload_file_key") != uploaded_file.name:
        st.session_state["uploaded_df"] = None
        st.session_state["upload_mode"] = "preview"
        st.session_state["show_edit_interface"] = False
    
    # Lade DataFrame nur einmal
    if st.session_state["uploaded_df"] is None:
        try:
            df = pd.read_excel(uploaded_file)
            has_product = "Product" in df.columns
            expected_cols = ["Titel","Bullet1","Bullet2","Bullet3","Bullet4","Bullet5","Description","SearchTerms","Keywords"]
            cols_lower = [str(c).strip().lower() for c in df.columns]

            # Normalisiere Spaltennamen - mappe "Title" auf "Titel"
            column_normalization = {}
            for col in df.columns:
                col_lower = str(col).strip().lower()
                if col_lower == "title" and col != "Titel":  # Nur wenn noch nicht "Titel"
                    column_normalization[col] = "Titel"
            
            if column_normalization:
                df = df.rename(columns=column_normalization)

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
            
            st.session_state["uploaded_df"] = df
            st.session_state["upload_file_key"] = uploaded_file.name
            st.session_state["upload_mode"] = "preview"
            st.session_state["has_product"] = has_product
        except Exception as e:
            st.error(f"Fehler beim Laden der Datei: {e}")
            st.session_state["uploaded_df"] = None
    
    df = st.session_state["uploaded_df"]
    has_product = st.session_state.get("has_product", False)
    
    if df is not None and st.session_state["upload_mode"] == "preview":
        st.markdown("---")
        st.header("📊 Datei-Vorschau")
        
        st.success(f"✅ **{len(df)} Listings** erfolgreich geladen")
        
        # Zeige Übersicht
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Anzahl Listings", len(df))
        with col2:
            st.metric("Spalten", len(df.columns))
        with col3:
            if "Product" in df.columns:
                product_count = df["Product"].notna().sum()
                st.metric("Mit Produktname", product_count)
        
        # Zeige erste Zeilen
        st.subheader("Vorschau (erste 5 Zeilen)")
        preview_cols = ["Product"] if "Product" in df.columns else []
        preview_cols.extend([c for c in ["Titel", "Bullet1", "Bullet2"] if c in df.columns])
        if preview_cols:
            st.dataframe(df[preview_cols].head(), use_container_width=True)
        else:
            st.dataframe(df.head(), use_container_width=True)
        
        # Zeige alle Spalten
        with st.expander("Alle Spalten anzeigen"):
            st.code(", ".join(df.columns.tolist()))
        
        # Auswahl: Bearbeiten oder direkt speichern
        st.markdown("---")
        st.subheader("Was möchtest du tun?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✏️ Listings bearbeiten", key="btn_edit_listings", type="primary", use_container_width=True):
                st.session_state["show_edit_interface"] = True
                st.session_state["upload_mode"] = "edit"
                st.rerun()
        
        with col2:
            if db_engine:
                if st.button("💾 Direkt in Supabase speichern", key="btn_save_direct", type="secondary", use_container_width=True):
                    st.session_state["upload_mode"] = "save"
                    st.rerun()
            else:
                st.info("💾 Datenbank nicht verbunden")
        
        # Direkter Supabase-Save Modus
        if st.session_state["upload_mode"] == "save" and db_engine:
            st.markdown("---")
            st.subheader("💾 Direkt in Supabase speichern")
            
            # Upload-Optionen
            col1, col2 = st.columns(2)
            with col1:
                overwrite_direct = st.checkbox(
                    "Bestehende Einträge überschreiben",
                    value=False,
                    key="overwrite_direct"
                )
            with col2:
                show_details_direct = st.checkbox(
                    "Details beim Upload anzeigen",
                    value=True,
                    key="show_details_direct"
                )
            
            # Spalten-Mapping für Metadaten
            asin_cols = [c for c in df.columns if "asin" in c.lower() or "ean" in c.lower() or "sku" in c.lower()]
            mp_cols = [c for c in df.columns if c.upper() == "MP" or "marketplace" in c.lower()]
            
            if not asin_cols or not mp_cols:
                st.warning("⚠️ Die Datei muss Spalten für ASIN/EAN/SKU und MP enthalten, um direkt zu speichern.")
                st.info("💡 Alternativ kannst du die Listings bearbeiten und danach speichern.")
            else:
                if st.button("💾 Jetzt speichern", key="btn_save_now", type="primary"):
                    success_count = 0
                    error_count = 0
                    skipped_count = 0
                    
                    if show_details_direct:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    # Bereite Daten für Batch-Upload vor
                    listings_to_save = []
                    
                    if show_details_direct and status_text:
                        status_text.text("Bereite Daten vor...")
                    if show_details_direct and progress_bar:
                        progress_bar.progress(0.1)
                    
                    for idx, row in df.iterrows():
                        if show_details_direct and progress_bar:
                            progress_bar.progress((idx + 1) / len(df) * 0.5)  # 50% für Vorbereitung
                        
                        listing_data = {
                            "Product": str(row.get("Product", "")),
                            "Titel": str(row.get("Titel", "")),
                            "Bullet1": str(row.get("Bullet1", "")),
                            "Bullet2": str(row.get("Bullet2", "")),
                            "Bullet3": str(row.get("Bullet3", "")),
                            "Bullet4": str(row.get("Bullet4", "")),
                            "Bullet5": str(row.get("Bullet5", "")),
                            "Description": str(row.get("Description", "")),
                            "SearchTerms": str(row.get("SearchTerms", "")),
                            "Keywords": str(row.get("Keywords", ""))
                        }
                        
                        asin = str(row[asin_cols[0]]).strip() if pd.notna(row[asin_cols[0]]) else ""
                        mp = str(row[mp_cols[0]]).strip() if pd.notna(row[mp_cols[0]]) else ""
                        account = str(row.get("Account", "")).strip() if "Account" in row and pd.notna(row.get("Account")) else None
                        project = str(row.get("Project", "")).strip() if "Project" in row and pd.notna(row.get("Project")) else None
                        
                        if asin and mp:
                            listings_to_save.append({
                                "data": listing_data,
                                "asin": asin,
                                "mp": mp,
                                "account": account,
                                "project": project,
                                "check_existing": True,
                                "overwrite": overwrite_direct
                            })
                    
                    # Batch-Upload durchführen
                    if show_details_direct and status_text:
                        status_text.text(f"Speichere {len(listings_to_save)} Listings in Batches...")
                    
                    success_count, error_count, skipped_count, batch_errors = batch_save_listings_to_db(
                        db_engine,
                        listings_to_save,
                        batch_size=100
                    )
                    
                    errors = batch_errors if 'errors' not in locals() else errors + batch_errors
                    
                    if show_details_direct and progress_bar:
                        progress_bar.progress(1.0)
                    
                    if show_details_direct and progress_bar:
                        progress_bar.empty()
                    if show_details_direct and status_text:
                        status_text.empty()
                    
                    # Detaillierte Debug-Statistik
                    st.markdown("### 📊 Upload-Statistik")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Gesamt verarbeitet", len(df))
                    with col2:
                        st.metric("✅ Erfolgreich", success_count, delta=f"{success_count/len(df)*100:.1f}%")
                    with col3:
                        st.metric("⏭️ Übersprungen", skipped_count, delta=f"{skipped_count/len(df)*100:.1f}%")
                    with col4:
                        st.metric("❌ Fehler", error_count, delta=f"{error_count/len(df)*100:.1f}%")
                    
                    # Debug: Prüfe tatsächliche Anzahl in DB nach Upload
                    if db_engine:
                        try:
                            with db_engine.connect() as conn:
                                count_after = conn.execute(text("SELECT COUNT(*) FROM listings")).fetchone()[0]
                                st.info(f"📊 **Aktuelle Anzahl in Datenbank nach Upload:** {count_after} Listings")
                        except Exception:
                            pass
                    
                    if success_count > 0:
                        st.success(f"✅ **{success_count}** Listings erfolgreich gespeichert!")
                    if skipped_count > 0:
                        st.info(f"⏭️ **{skipped_count}** Listings übersprungen (bereits vorhanden - gleiche ASIN + MP Kombination)")
                    if error_count > 0:
                        st.warning(f"⚠️ **{error_count}** Fehler")
                    
                    if success_count > 0:
                        st.balloons()
                        st.session_state["upload_mode"] = "preview"
    
    # Bearbeitungs-Interface nur anzeigen, wenn explizit gewählt
    elif df is not None and st.session_state["show_edit_interface"]:
        st.markdown("---")
        st.header("✏️ Listings bearbeiten")
        st.info(f"📊 Bearbeite {len(df)} Listings. Verwende die Expander zum Ein- und Ausklappen.")
        
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

# ---- 3) Listings aus Datenbank zum Bearbeiten laden ----
if "db_listings_for_edit" in st.session_state and len(st.session_state["db_listings_for_edit"]) > 0:
    st.markdown("---")
    st.header("✏️ Listings aus Datenbank bearbeiten")
    st.info(f"📊 {len(st.session_state['db_listings_for_edit'])} Listing(s) in Bearbeitung")
    
    # Initialisiere bearbeitete Daten falls nicht vorhanden
    if "db_listings_edited" not in st.session_state:
        st.session_state["db_listings_edited"] = {}
    
    # Rendere jedes Listing in einem eigenen Expander
    for idx, db_listing in enumerate(st.session_state["db_listings_for_edit"]):
        listing_id = db_listing.get("id", str(idx))
        
        # Metadaten für Expander-Header
        listing_label = f"{db_listing.get('name', 'Unbekannt')} - {db_listing.get('asin_ean_sku', 'N/A')} ({db_listing.get('mp', 'N/A')})"
        
        with st.expander(f"📦 {listing_label}", expanded=True):
            # Metadaten anzeigen
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            with col1:
                st.info(f"**ASIN/EAN/SKU:** {db_listing.get('asin_ean_sku', 'N/A')}")
            with col2:
                st.info(f"**MP:** {db_listing.get('mp', 'N/A')}")
            with col3:
                st.info(f"**Account:** {db_listing.get('account', 'N/A')}")
            with col4:
                st.info(f"**Project:** {db_listing.get('project', 'N/A')}")
            with col5:
                # Button zum Entfernen
                if st.button("🗑️ Entfernen", key=f"btn_remove_{listing_id}", type="secondary", use_container_width=True):
                    st.session_state["db_listings_for_edit"] = [
                        l for l in st.session_state["db_listings_for_edit"] 
                        if l.get("id") != listing_id
                    ]
                    # Entferne auch bearbeitete Daten
                    if listing_id in st.session_state.get("db_listings_edited", {}):
                        del st.session_state["db_listings_edited"][listing_id]
                    st.rerun()
            
            # Konvertiere zu Format für render_listing (ohne Metadaten)
            listing_for_render = {
                "Product": db_listing.get("Product", ""),
                "Titel": db_listing.get("Titel", ""),
                "Bullet1": db_listing.get("Bullet1", ""),
                "Bullet2": db_listing.get("Bullet2", ""),
                "Bullet3": db_listing.get("Bullet3", ""),
                "Bullet4": db_listing.get("Bullet4", ""),
                "Bullet5": db_listing.get("Bullet5", ""),
                "Description": db_listing.get("Description", ""),
                "SearchTerms": db_listing.get("SearchTerms", ""),
                "Keywords": db_listing.get("Keywords", "")
            }
            
            # Render Listing mit eindeutigem Index basierend auf ID
            # Verwende Hash der ID für einen stabilen Index
            db_listing_index = hash(listing_id) % 1000000  # Modulo um Index zu begrenzen
            edited_listing_data = render_listing(listing_for_render, db_listing_index, has_product=True)
            
            # Speichere bearbeitete Daten
            st.session_state["db_listings_edited"][listing_id] = {
                "data": edited_listing_data,
                "original": db_listing
            }
    
    # Speichern-Bereich
    st.markdown("---")
    st.subheader("💾 Listings in Datenbank speichern")
    
    if db_engine:
        # Auswahl welche Listings gespeichert werden sollen
        available_listings = [
            (listing.get("id"), f"{listing.get('name', 'Unbekannt')} - {listing.get('asin_ean_sku', 'N/A')} ({listing.get('mp', 'N/A')})")
            for listing in st.session_state["db_listings_for_edit"]
        ]
        
        if available_listings:
            selected_listing_ids = st.multiselect(
                "Welche Listings sollen gespeichert werden?",
                options=[lid for lid, _ in available_listings],
                format_func=lambda lid: next(label for lid2, label in available_listings if lid2 == lid),
                default=[lid for lid, _ in available_listings],  # Alle standardmäßig ausgewählt
                key="select_listings_to_save"
            )
            
            # Überschreiben-Option
            overwrite_option = st.checkbox(
                "Bestehende Einträge überschreiben",
                value=True,  # Standardmäßig aktiviert
                help="Wenn aktiviert, werden bestehende Listings (gleiche ASIN + MP) aktualisiert. Sonst werden sie übersprungen.",
                key="overwrite_db_listings"
            )
            
            if st.button("💾 Ausgewählte Listings speichern", key="btn_save_db_listings", type="primary", use_container_width=True):
                if not selected_listing_ids:
                    st.warning("⚠️ Bitte wähle mindestens ein Listing aus, das gespeichert werden soll.")
                else:
                    success_count = 0
                    error_count = 0
                    skipped_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, listing_id in enumerate(selected_listing_ids):
                        status_text.text(f"Speichere Listing {idx + 1} von {len(selected_listing_ids)}...")
                        progress_bar.progress((idx + 1) / len(selected_listing_ids))
                        
                        if listing_id in st.session_state.get("db_listings_edited", {}):
                            edited_info = st.session_state["db_listings_edited"][listing_id]
                            edited_data = edited_info["data"]
                            original_listing = edited_info["original"]
                            
                            listing_data = {
                                "Product": edited_data.get("Product", ""),
                                "Titel": edited_data.get("Titel", ""),
                                "Bullet1": edited_data.get("Bullet1", ""),
                                "Bullet2": edited_data.get("Bullet2", ""),
                                "Bullet3": edited_data.get("Bullet3", ""),
                                "Bullet4": edited_data.get("Bullet4", ""),
                                "Bullet5": edited_data.get("Bullet5", ""),
                                "Description": edited_data.get("Description", ""),
                                "SearchTerms": edited_data.get("SearchTerms", ""),
                                "Keywords": edited_data.get("Keywords", ""),
                                "name": original_listing.get("name", "")
                            }
                            
                            asin = original_listing.get("asin_ean_sku", "")
                            mp = original_listing.get("mp", "")
                            account = original_listing.get("account") if original_listing.get("account") else None
                            project = original_listing.get("project") if original_listing.get("project") else None
                            
                            if asin and mp:
                                # Prüfe ob existiert und ob überschrieben werden soll
                                if overwrite_option:
                                    # Überschreiben - nutze save_listing_to_db (macht automatisch Update wenn existiert)
                                    if save_listing_to_db(db_engine, listing_data, asin, mp, account, project):
                                        success_count += 1
                                    else:
                                        error_count += 1
                                else:
                                    # Nicht überschreiben - prüfe ob existiert
                                    check_sql = text("SELECT id FROM listings WHERE asin_ean_sku = :asin AND mp = :mp")
                                    with db_engine.connect() as conn:
                                        existing = conn.execute(check_sql, {"asin": asin, "mp": mp}).fetchone()
                                    
                                    if existing:
                                        skipped_count += 1
                                    else:
                                        # Nicht vorhanden, speichere neu
                                        if save_listing_to_db(db_engine, listing_data, asin, mp, account, project):
                                            success_count += 1
                                        else:
                                            error_count += 1
                            else:
                                error_count += 1
                        else:
                            error_count += 1
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Ergebnisse anzeigen
                    if success_count > 0:
                        st.success(f"✅ {success_count} Listing(s) erfolgreich gespeichert!")
                    if skipped_count > 0:
                        st.info(f"⏭️ {skipped_count} Listing(s) übersprungen (bereits vorhanden und Überschreiben deaktiviert)")
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} Listing(s) konnten nicht gespeichert werden")
                    
                    if success_count > 0:
                        st.balloons()
                        # Entferne gespeicherte Listings aus der Bearbeitungsliste
                        st.session_state["db_listings_for_edit"] = [
                            l for l in st.session_state["db_listings_for_edit"]
                            if l.get("id") not in selected_listing_ids
                        ]
                        # Entferne auch bearbeitete Daten
                        for listing_id in selected_listing_ids:
                            if listing_id in st.session_state.get("db_listings_edited", {}):
                                del st.session_state["db_listings_edited"][listing_id]
                        st.rerun()
    else:
        st.error("❌ Datenbankverbindung nicht verfügbar")
    
    # Alle entfernen Button
    if st.button("🗑️ Alle Listings aus Bearbeitung entfernen", key="btn_remove_all_db", type="secondary"):
        st.session_state["db_listings_for_edit"] = []
        st.session_state["db_listings_edited"] = {}
        st.rerun()

# --- Download (Export) ---
if updated_rows_all:
    st.markdown("---")
    st.header("📥 Download & Speichern")
    result_df = pd.DataFrame(updated_rows_all)
    if "Product" not in result_df.columns:
        result_df["Product"] = ""
    cols = ["Product"] + [c for c in result_df.columns if c != "Product"]
    result_df = result_df[cols]

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 Excel herunterladen")
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
    
    with col2:
        if db_engine:
            st.subheader("💾 In Datenbank speichern")
            st.markdown("**Metadaten für alle Listings:**")
            
            default_account = st.session_state.get("save_account", "")
            default_project = st.session_state.get("save_project", "")
            
            save_account = st.text_input("Account (optional)", value=default_account, key="save_account")
            save_project = st.text_input("Project (optional)", value=default_project, key="save_project")
            
            st.markdown("**Für jedes Listing benötigt:** ASIN/EAN/SKU und Marketplace (MP)")
            st.info("💡 Die Metadaten (ASIN, MP) müssen in der Excel-Datei enthalten sein oder hier für alle Listings gleich sein.")
            
            # Option: Metadaten aus Excel oder manuell
            use_excel_metadata = st.checkbox("Metadaten aus Excel-Spalten verwenden (ASIN_EAN_SKU, MP)", value=True)
            
            if not use_excel_metadata:
                save_asin = st.text_input("ASIN/EAN/SKU (für alle Listings)", key="save_asin")
                save_mp = st.text_input("Marketplace (MP, z.B. DE)", key="save_mp")
            else:
                save_asin = None
                save_mp = None
            
            if st.button("💾 Alle Listings in Datenbank speichern", key="btn_save_all"):
                if use_excel_metadata:
                    # Versuche Metadaten aus DataFrame zu lesen
                    asin_cols = [c for c in result_df.columns if "asin" in c.lower() or "ean" in c.lower() or "sku" in c.lower()]
                    mp_cols = [c for c in result_df.columns if c.upper() == "MP" or c.lower() == "marketplace"]
                    
                    if not asin_cols or not mp_cols:
                        st.error("❌ Excel-Datei muss Spalten 'ASIN_EAN_SKU' (oder ähnlich) und 'MP' enthalten, wenn 'Metadaten aus Excel verwenden' aktiviert ist.")
                    else:
                        success_count = 0
                        error_count = 0
                        
                        for idx, row in result_df.iterrows():
                            asin = str(row[asin_cols[0]]).strip() if pd.notna(row[asin_cols[0]]) else None
                            mp = str(row[mp_cols[0]]).strip() if pd.notna(row[mp_cols[0]]) else None
                            
                            if asin and mp:
                                listing_data = {
                                    "Product": str(row.get("Product", "")),
                                    "Titel": str(row.get("Titel", "")),
                                    "Bullet1": str(row.get("Bullet1", "")),
                                    "Bullet2": str(row.get("Bullet2", "")),
                                    "Bullet3": str(row.get("Bullet3", "")),
                                    "Bullet4": str(row.get("Bullet4", "")),
                                    "Bullet5": str(row.get("Bullet5", "")),
                                    "Description": str(row.get("Description", "")),
                                    "SearchTerms": str(row.get("SearchTerms", "")),
                                    "Keywords": str(row.get("Keywords", ""))
                                }
                                
                                if save_listing_to_db(db_engine, listing_data, asin, mp, save_account or None, save_project or None):
                                    success_count += 1
                                else:
                                    error_count += 1
                            else:
                                error_count += 1
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count} Listings erfolgreich gespeichert!")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} Listings konnten nicht gespeichert werden (fehlende ASIN/MP)")
                else:
                    # Manuelle Metadaten
                    if save_asin and save_mp:
                        success_count = 0
                        for idx, row in result_df.iterrows():
                            listing_data = {
                                "Product": str(row.get("Product", "")),
                                "Titel": str(row.get("Titel", "")),
                                "Bullet1": str(row.get("Bullet1", "")),
                                "Bullet2": str(row.get("Bullet2", "")),
                                "Bullet3": str(row.get("Bullet3", "")),
                                "Bullet4": str(row.get("Bullet4", "")),
                                "Bullet5": str(row.get("Bullet5", "")),
                                "Description": str(row.get("Description", "")),
                                "SearchTerms": str(row.get("SearchTerms", "")),
                                "Keywords": str(row.get("Keywords", ""))
                            }
                            
                            if save_listing_to_db(db_engine, listing_data, save_asin, save_mp, save_account or None, save_project or None):
                                success_count += 1
                        
                        st.success(f"✅ {success_count} Listings erfolgreich gespeichert!")
                    else:
                        st.error("❌ Bitte gib ASIN/EAN/SKU und Marketplace (MP) an.")
        else:
            st.info("💡 Datenbankverbindung nicht verfügbar. Setze SUPABASE_DB_PASSWORD Umgebungsvariable.")
