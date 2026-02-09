# Lokales Hosting - Amazon Listing Analyzer

## ⚠️ ZUKUNFTSOPTION - Noch nicht aktiv empfohlen

Diese Anleitung beschreibt eine **zukünftige Option** für lokales Hosting, um Wartezeiten von Onlinedatenbanken zu vermeiden.

**Aktueller Status:** 🚧 Die Funktionalität ist im Code vorhanden, aber noch nicht für den produktiven Einsatz empfohlen.

**Aktuelle Lösung:** Verwenden Sie weiterhin Supabase (siehe `README.md`)

---

Diese Anleitung zeigt, wie Sie das Amazon Listing Analyzer Tool lokal hosten können, um Wartezeiten von Onlinedatenbanken zu vermeiden und unternehmensweit nutzbar zu machen.

## Vorteile des lokalen Hostings

- ✅ **Keine Wartezeiten**: Lokale Datenbank bietet sofortige Antwortzeiten
- ✅ **Unternehmensweit nutzbar**: Über das lokale Netzwerk erreichbar
- ✅ **Datenkontrolle**: Alle Daten bleiben im Unternehmen
- ✅ **Kostenlos**: Keine Cloud-Datenbankkosten
- ✅ **Schnellere Performance**: Keine Netzwerk-Latenz

## Voraussetzungen

- Docker und Docker Compose installiert
- Python 3.8+ installiert
- Port 5432 (PostgreSQL) und 8501 (Streamlit) verfügbar

## Schnellstart

### 1. Datenbank starten

```bash
# Starte die lokale PostgreSQL-Datenbank
docker-compose up -d postgres

# Prüfe ob die Datenbank läuft
docker-compose ps
```

### 2. Konfiguration einrichten

Erstellen Sie eine `.streamlit/secrets.toml` Datei im Projektverzeichnis:

```bash
mkdir -p .streamlit
```

Fügen Sie folgende Konfiguration hinzu:

```toml
# .streamlit/secrets.toml

# Datenbank-Modus: 'local' für lokale DB, 'supabase' für Online-DB
db_mode = "local"

# Lokale Datenbank-Konfiguration
db_host = "localhost"
db_port = "5432"
db_name = "amazon_listings"
db_user = "postgres"
db_password = "postgres"  # Ändern Sie dies für Produktion!

# Optional: Google Gemini API Key (falls verwendet)
# gemini_api_key = "your_key_here"
```

**Wichtig**: Ändern Sie das Passwort für Produktionsumgebungen!

### 3. Anwendung starten

```bash
# Installiere Abhängigkeiten (falls noch nicht geschehen)
pip install -r requirements.txt

# Starte die Streamlit-Anwendung
streamlit run app.py
```

Die Anwendung ist jetzt unter `http://localhost:8501` erreichbar.

## ⚠️ WICHTIG: Für unternehmensweite Nutzung einen Server verwenden!

**Nicht auf Ihrem Arbeitsrechner laufen lassen!**
- ❌ Tool ist offline, wenn Ihr Rechner aus ist
- ❌ Tool ist offline, wenn Sie im Homeoffice sind
- ❌ Andere können nicht zugreifen, wenn Sie nicht da sind

**Lösung:** Verwenden Sie einen **dedizierten Server** (siehe `SERVER_SETUP.md`)

## Unternehmensweite Nutzung

### Option 1: Auf einem Server (Empfohlen) ✅

**Für unternehmensweite Nutzung sollte das Tool auf einem Server laufen, der immer eingeschaltet ist.**

Siehe `SERVER_SETUP.md` für detaillierte Anleitung.

### Option 2: Lokales Netzwerk (Nur für Tests)

**⚠️ Nur für Tests, nicht für Produktion!**

1. **Finden Sie die IP-Adresse des Host-Rechners:**
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "
   
   # Windows
   ipconfig
   ```

2. **Starten Sie Streamlit mit der Host-IP:**
   ```bash
   streamlit run app.py --server.address 0.0.0.0 --server.port 8501
   ```

3. **Andere Rechner im Netzwerk können jetzt zugreifen:**
   ```
   http://[IHRE-IP-ADRESSE]:8501
   ```
   
**Problem:** Tool ist offline, wenn Ihr Rechner aus ist!

### Option 2: Reverse Proxy mit Nginx (Für Produktion)

Für eine professionelle Lösung mit Domain-Namen und HTTPS:

1. Installieren Sie Nginx
2. Konfigurieren Sie einen Reverse Proxy:

```nginx
server {
    listen 80;
    server_name listing-analyzer.ihre-firma.de;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### Option 3: Docker Container (Empfohlen für Produktion)

Erstellen Sie eine `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

Dann können Sie alles mit Docker Compose starten:

```yaml
# Erweitern Sie docker-compose.yml:
services:
  # ... postgres service ...
  
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DB_MODE=local
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=amazon_listings
      - DB_USER=postgres
      - DB_PASSWORD=postgres
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app-network
```

## Datenbank-Verwaltung

### pgAdmin (Optional)

Für eine grafische Datenbankverwaltung können Sie pgAdmin starten:

```bash
docker-compose --profile admin up -d pgadmin
```

Zugriff unter: `http://localhost:5050`

**Login:**
- Email: `admin@example.com` (oder wie in `.env` konfiguriert)
- Passwort: `admin` (oder wie in `.env` konfiguriert)

**Server hinzufügen:**
- Host: `postgres` (wenn pgAdmin im Docker-Netzwerk) oder `localhost`
- Port: `5432`
- Database: `amazon_listings`
- Username: `postgres`
- Password: `postgres` (oder wie konfiguriert)

### Datenbank-Backup

```bash
# Backup erstellen
docker exec amazon-listing-analyzer-db pg_dump -U postgres amazon_listings > backup.sql

# Backup wiederherstellen
docker exec -i amazon-listing-analyzer-db psql -U postgres amazon_listings < backup.sql
```

## Umgebungsvariablen (Alternative zu secrets.toml)

Statt `secrets.toml` können Sie auch Umgebungsvariablen verwenden:

```bash
export DB_MODE=local
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=amazon_listings
export DB_USER=postgres
export DB_PASSWORD=postgres

streamlit run app.py
```

## Migration von Supabase zu lokaler DB

Falls Sie bereits Daten in Supabase haben:

1. **Exportieren Sie die Daten aus Supabase:**
   ```bash
   pg_dump -h aws-1-eu-west-1.pooler.supabase.com -U postgres.povudekejufidhyuinro -d postgres > supabase_backup.sql
   ```

2. **Importieren Sie in die lokale Datenbank:**
   ```bash
   docker exec -i amazon-listing-analyzer-db psql -U postgres amazon_listings < supabase_backup.sql
   ```

## Troubleshooting

### Datenbank-Verbindungsfehler

```bash
# Prüfe ob die Datenbank läuft
docker-compose ps

# Prüfe Logs
docker-compose logs postgres

# Starte die Datenbank neu
docker-compose restart postgres
```

### Port bereits belegt

Ändern Sie den Port in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Verwende Port 5433 statt 5432
```

Und passen Sie die Konfiguration entsprechend an.

### Performance-Optimierung

Für bessere Performance können Sie die PostgreSQL-Einstellungen anpassen:

```yaml
# In docker-compose.yml
environment:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  POSTGRES_DB: amazon_listings
  # Performance-Tuning
  POSTGRES_INITDB_ARGS: "-E UTF8 --locale=C"
```

## Sicherheit

⚠️ **Wichtig für Produktion:**

1. Ändern Sie alle Standard-Passwörter
2. Verwenden Sie Firewall-Regeln für Datenbankzugriff
3. Implementieren Sie HTTPS (z.B. mit Let's Encrypt)
4. Regelmäßige Backups einrichten
5. Zugriff auf die Anwendung beschränken (z.B. VPN)

## Support

Bei Fragen oder Problemen:
- Prüfen Sie die Logs: `docker-compose logs`
- Prüfen Sie die Streamlit-Logs in der Konsole
- Stellen Sie sicher, dass alle Ports verfügbar sind

