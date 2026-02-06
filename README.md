# STDF Wafermap Analyzer

🔬 Ein Tool zur Analyse von Halbleiter-Testdaten aus STDF-Dateien, Erstellung von Wafermaps und Generierung von Reports.

## Features

- **STDF-Parsing**: Unterstützt Semi-ATE STDF und pystdf Bibliotheken
- **Wafermap-Visualisierung**: Interaktive Farbdarstellung nach Bin oder Testparameter
- **Multi-Wafer-Analyse**: Vergleich mehrerer Wafer in einer Ansicht
- **Statistiken**: Yield-Berechnung, Bin-Verteilung, Parameter-Statistiken
- **Export**: PowerPoint-Reports, CSV-Export
- **Google Integration**: Google Drive / Google Slides Upload
- **Web-Version**: Streamlit-basierte Web-Applikation (NEU!)

## Installation

### Basis-Installation

```bash
# Repository klonen
git clone <repository-url>
cd stdf-wafermap-analyzer

# Virtuelle Umgebung erstellen
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Basis-Abhängigkeiten installieren
pip install -e .
```

### Mit Web-Support (Streamlit)

```bash
pip install -e ".[web]"
```

### Mit Desktop-Support (PowerPoint)

```bash
pip install -e ".[desktop]"
```

### Vollständige Installation

```bash
pip install -e ".[all]"
```

## Projekt-Struktur

```
stdf-wafermap-analyzer/
├── src/
│   └── stdf_analyzer/
│       ├── core/              # Business-Logik (UI-unabhängig)
│       │   ├── binning.py     # Bin-Definitionen und Lookup
│       │   ├── stdf_parser.py # STDF/CSV Parsing
│       │   └── wafermap.py    # Wafermap-Generierung
│       │
│       ├── services/          # Externe Dienste
│       │   ├── google_drive.py
│       │   └── pptx_export.py
│       │
│       ├── gui/               # Tkinter Desktop-App
│       │   └── main_window.py
│       │
│       └── web/               # Streamlit Web-App
│           └── app.py
│
├── tests/                     # Unit Tests
├── main.py                    # Original Desktop-Anwendung
├── pyproject.toml             # Projekt-Konfiguration
└── README.md
```

## Verwendung

### Desktop-Anwendung (Original)

```bash
python main.py
```

### Web-Anwendung (Streamlit)

```bash
streamlit run src/stdf_analyzer/web/app.py
```

### Als Python-Modul

```python
from stdf_analyzer.core import parse_stdf_file, WafermapGenerator

# STDF-Datei laden
data = parse_stdf_file("wafer_data.stdf")

# Wafermap erstellen
generator = WafermapGenerator(data.dataframe, data.wafer_id)
fig = generator.create_plotly_figure(parameter="bin")
fig.show()

# Statistiken abrufen
print(f"Yield: {generator.get_yield():.2f}%")
print(generator.get_bin_summary())
```

## Core-Module API

### BinningLookup

```python
from stdf_analyzer.core import BinningLookup

binning = BinningLookup()
binning.load_from_excel("binning_table.xlsx")

# Bin für Test-Nummer ermitteln
bin_num = binning.get_bin_for_test(1234)
bin_name = binning.get_bin_name(bin_num)
```

### STDFParser

```python
from stdf_analyzer.core import parse_stdf_file, parse_csv_file

# STDF-Datei parsen
data = parse_stdf_file("wafer.stdf")
print(f"Wafer: {data.wafer_id}")
print(f"Dies: {data.die_count}")
print(f"Parameter: {data.parameter_count}")

# CSV-Datei parsen
csv_data = parse_csv_file("wafer.csv")
```

### WafermapGenerator

```python
from stdf_analyzer.core import WafermapGenerator

generator = WafermapGenerator(df, wafer_id="W001")

# Matplotlib-Figur (Desktop)
fig = generator.create_matplotlib_figure(parameter="bin")
fig.savefig("wafermap.png")

# Plotly-Figur (Web)
plotly_fig = generator.create_plotly_figure(parameter="bin")
plotly_fig.write_html("wafermap.html")

# Statistiken
print(f"Yield: {generator.get_yield():.2f}%")
print(generator.get_bin_summary())
```

## Versionierung

Dieses Projekt verwendet [Semantic Versioning](https://semver.org/):

- **MAJOR**: Inkompatible API-Änderungen
- **MINOR**: Neue Features (rückwärtskompatibel)
- **PATCH**: Bugfixes (rückwärtskompatibel)

### Changelog

#### v1.0.0 (2026-02-06)
- Initiale strukturierte Version
- Core-Module extrahiert
- Web-Support mit Streamlit hinzugefügt

## Entwicklung

### Tests ausführen

```bash
pytest tests/
```

### Code formatieren

```bash
black src/
ruff check src/ --fix
```

## Autor

**Krzysztof Szenklarz**  
Hardware Engineer - D&O Test, Metrology, Characterization and Data Team

## Lizenz

Proprietary - Meta Platforms, Inc.
