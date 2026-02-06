# 🚀 Deployment Guide - STDF Wafermap Analyzer

Diese Anleitung erklärt, wie Sie die Web-Applikation auf verschiedene Arten bereitstellen können.

---

## Option 1: Lokal starten (Entwicklung/Test)

### Voraussetzungen
- Python 3.10+ installiert
- Netzwerk-Zugriff auf STDF-Daten

### Schritte

```bash
# 1. In das Projektverzeichnis wechseln
cd c:\Users\szenklarz\Desktop\VS_Folder

# 2. Virtuelle Umgebung erstellen (optional, empfohlen)
python -m venv venv
venv\Scripts\activate

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. App starten
streamlit run src/stdf_analyzer/web/app.py

# 5. Browser öffnen: http://localhost:8501
```

### Für Kollegen im selben Netzwerk
```bash
# IP-Adresse anzeigen
ipconfig

# App mit Netzwerk-Zugriff starten
streamlit run src/stdf_analyzer/web/app.py --server.address 0.0.0.0

# Kollegen öffnen: http://IHRE-IP:8501
```

---

## Option 2: Docker Container (Empfohlen für Server)

### Voraussetzungen
- Docker Desktop installiert
- Zugriff auf Netzwerk-Shares

### Schritte

```bash
# 1. Docker Image bauen
docker build -t stdf-analyzer .

# 2. Container starten
docker run -d \
  --name stdf-analyzer \
  -p 8501:8501 \
  -v "//server/stdf_data:/data/stdf:ro" \
  stdf-analyzer

# 3. Browser öffnen: http://localhost:8501
```

### Mit Docker Compose (einfacher)

```bash
# docker-compose.yml anpassen (Pfade zu Netzwerk-Shares)

# Starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

---

## Option 3: Linux Server (Produktion)

### 1. Code auf Server kopieren

```bash
# Von Windows
scp -r VS_Folder/ user@server:/opt/stdf-analyzer/

# Oder mit Git
git clone <repo-url> /opt/stdf-analyzer
```

### 2. Systemd Service erstellen

Datei: `/etc/systemd/system/stdf-analyzer.service`

```ini
[Unit]
Description=STDF Wafermap Analyzer
After=network.target

[Service]
Type=simple
User=stdf-app
Group=stdf-app
WorkingDirectory=/opt/stdf-analyzer
Environment="PATH=/opt/stdf-analyzer/venv/bin"
ExecStart=/opt/stdf-analyzer/venv/bin/streamlit run \
    src/stdf_analyzer/web/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Service aktivieren

```bash
# User erstellen
sudo useradd -r -s /bin/false stdf-app

# Berechtigungen setzen
sudo chown -R stdf-app:stdf-app /opt/stdf-analyzer

# Virtuelle Umgebung erstellen
sudo -u stdf-app python3 -m venv /opt/stdf-analyzer/venv
sudo -u stdf-app /opt/stdf-analyzer/venv/bin/pip install -r requirements.txt

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable stdf-analyzer
sudo systemctl start stdf-analyzer

# Status prüfen
sudo systemctl status stdf-analyzer
```

### 4. Nginx Reverse Proxy (Optional, für HTTPS)

Datei: `/etc/nginx/sites-available/stdf-analyzer`

```nginx
server {
    listen 80;
    server_name stdf-analyzer.your-domain.com;

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

```bash
sudo ln -s /etc/nginx/sites-available/stdf-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Konfiguration

### Netzwerk-Pfade anpassen

In `src/stdf_analyzer/web/app.py` die `DEFAULT_SHARE_PATHS` anpassen:

```python
DEFAULT_SHARE_PATHS = [
    r"\\server\stdf_data",
    r"\\nas\semiconductor\wafer_tests",
    r"/mnt/data/stdf",  # Linux
]
```

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `STREAMLIT_SERVER_PORT` | HTTP Port | 8501 |
| `STREAMLIT_SERVER_ADDRESS` | Bind-Adresse | 0.0.0.0 |
| `STDF_DATA_PATH` | Standard-Datenpfad | - |

---

## Troubleshooting

### Container startet nicht
```bash
docker logs stdf-analyzer
```

### Keine Verbindung zu Netzwerk-Share
- Windows: Share als Laufwerk mounten
- Docker: Volume-Mounts prüfen
- Linux: cifs-utils installieren, Credentials prüfen

### Langsame Performance bei großen STDF-Dateien
- Mehr RAM für Container: `docker run -m 4g ...`
- Daten lokal cachen

---

## Support

Bei Fragen: Krzysztof Szenklarz (szenklarz@meta.com)
