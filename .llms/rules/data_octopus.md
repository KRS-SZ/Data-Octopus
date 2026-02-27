# Data Octopus – Devmate Rules

> ⚠️ Diese Datei wird AUTOMATISCH bei jeder Session geladen.
> Sie enthält ALLE Learnings, Regeln, Projekt-Infos und Domänenwissen.
> Keine weiteren Dateien müssen zuerst gelesen werden.

---

## 1. PROJEKT-IDENTITÄT

| Eigenschaft         | Wert                                                          |
|---------------------|---------------------------------------------------------------|
| **Projektname**     | Data Octopus (STDF Wafermap Analyzer)                         |
| **GitHub Repo**     | https://github.com/KRS-SZ/Data-Octopus.git                   |
| **Eigentümer**      | Krzysztof Szenklarz (szenklarz@meta.com)                      |
| **Rolle**           | Hardware Engineer – D&O Test, Metrology, Characterization     |
| **Standort**        | Regensburg, Deutschland                                       |
| **Kommunikation**   | 🇩🇪 Deutsch (User↔Devmate) / 🇬🇧 Englisch (Code, GUI)       |
| **Python**          | 3.13 → `C:\Users\szenklarz\AppData\Local\Programs\Python\Python313\python.exe` |
| **GUI-Framework**   | tkinter + matplotlib (NICHT customtkinter!)                   |
| **Projektpfad**     | `c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\`         |
| **Aktuelle Version**| **v5.0.1** - Modulare Architektur mit Datalog Tab            |

---

## 2. PROJEKT-BESCHREIBUNG

Tool zur **Analyse von Halbleiter-Testdaten** aus STDF-Dateien:
- **STDF-Parsing**: Semi-ATE STDF und pystdf Bibliotheken
- **Wafermap-Visualisierung**: Farbdarstellung nach Bin oder Testparameter (matplotlib)
- **Multi-Wafer-Analyse**: Vergleich mehrerer Wafer
- **Statistiken**: Yield-Berechnung, Bin-Verteilung, Parameter-Statistiken
- **Pixel Analysis**: 25×25 Grid, PLM Image Processing
- **Export**: PowerPoint-Reports (python-pptx), CSV-Export
- **Google Integration**: Google Drive / Google Slides Upload
- **Web-Version**: Streamlit-basierte Web-Applikation

---

## 3. STARTEN DER ANWENDUNG

```bash
# Desktop-GUI (Standard) - WICHTIG: main.py ist die AKTUELLE Version (v4.0+)
& "C:\Users\szenklarz\AppData\Local\Programs\Python\Python313\python.exe" "c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\code\main.py"

# Web-App (Streamlit)
streamlit run "c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\code\src\stdf_analyzer\web\app.py"
```

⚠️ **IMMER Python 3.13 lokal verwenden** (nicht fb-python) – wegen tkinter!
⚠️ **IMMER main.py verwenden** (ab v4.0.0, früher main_v3.py)
⚠️ **DEVMATE: IMMER vom Terminal starten** – NIEMALS anders! Befehl oben kopieren und ausführen!
⚠️ **DEVMATE: execute_command mit `interactive: true`** – damit die Ausgabe im VS Code Terminal sichtbar ist!

---

## 4. ARCHITEKTUR & PROJEKT-STRUKTUR

```
Data Octopus/
├── code/                      # 🆕 ALLE CODE-DATEIEN (ab 26.02.2026)
│   ├── main.py                # Haupt-Desktop-Anwendung (~34.5k Zeilen) ← AKTUELLE VERSION v4.0+
│   ├── src/
│   │   └── stdf_analyzer/
│   │       ├── core/          # Business-Logik (UI-unabhängig)
│   │       │   ├── app_state.py    # 🆕 AppState-Klasse (zentrale State-Verwaltung)
│   │       │   ├── binning.py      # BinningLookup, get_bin_colormap, BIN_COLORS
│   │       │   ├── config.py       # 🆕 Konstanten (KNOWN_GROUP_TYPES, PATTERNS, etc.)
│   │       │   ├── parameter_utils.py # 🆕 simplify_param_name, extract_group_from_column
│   │       │   ├── stdf_parser.py
│   │       │   └── wafermap.py
│   │       ├── gui/           # (Placeholder für Tab-Module Phase 5)
│   │       ├── services/      # Externe Dienste
│   │       └── web/           # Streamlit Web-App
│   ├── tests/                 # Unit Tests (pytest)
│   ├── pyproject.toml         # Projekt-Konfiguration
│   ├── requirements.txt       # Dependencies
│   ├── Dockerfile             # Docker-Support
│   └── docker-compose.yml
│
├── AM Data/                   # STDF/CSV Testdaten
├── Binning/                   # Binning-Excel Dateien
├── Data/                      # Weitere Testdaten
├── Jobs/                      # Job-Dateien
├── saved_jobs/                # Gespeicherte Job-Konfigurationen
├── Report/                    # PowerPoint-Reports (Output)
├── Tooltest/                  # Test-Daten für Entwicklung
├── README.md                  # Projekt-Beschreibung
├── DEPLOYMENT.md              # Deployment-Infos
└── .llms/                     # Devmate Rules
```

### 4.1 Hinweis zur Struktur
- **`code/` Ordner** enthält ALLE Python-Dateien und Konfiguration (ab 26.02.2026 aufgeräumt)
- **`main.py`** ist die Hauptdatei (umbenannt von `main_v3.py` in v4.0.0)
- **`src/stdf_analyzer/core/`** enthält extrahierte Module (ab v3.2.21-v3.2.24 refaktoriert)
- **Daten-Ordner bleiben im Root** für einfachen Zugriff

### 4.2 Refactoring-Status (v4.0.0+)

| Modul | Status | Beschreibung |
|-------|--------|--------------|
| `core/binning.py` | ✅ | BinningLookup, get_bin_colormap (~260 Zeilen) |
| `core/config.py` | ✅ | KNOWN_GROUP_TYPES, PATTERNS (~100 Zeilen) |
| `core/parameter_utils.py` | ✅ | simplify_param_name, extract_group_from_column (~230 Zeilen) |
| `core/app_state.py` | ✅ | AppState-Klasse (Infrastruktur für globale Variablen) |
| `core/data_loader.py` | ✅ | CSV/STDF Loader Funktionen (~180 Zeilen) |
| `core/statistics_utils.py` | ✅ | Statistische Berechnungen (Cpk, Yield, GRR) (~300 Zeilen) |
| `core/wafermap_utils.py` | ✅ | Wafer-Koordinaten, Die-Positionierung (~330 Zeilen) |
| `gui/diffmap_tab.py` | ✅ | DiffmapTab Klasse (~600 Zeilen) |
| `gui/wafer_tab.py` | ✅ | WaferTab Klasse (~550 Zeilen) |
| `gui/grr_tab.py` | ✅ | GRRTab Klasse (~470 Zeilen) |
| `gui/multi_wafer_tab.py` | ✅ | MultiWaferTab Klasse (~450 Zeilen) |
| `gui/statistics_tab.py` | ✅ | StatisticsTab Klasse (~450 Zeilen) |
| `gui/charac_curve_tab.py` | ✅ | CharacCurveTab Klasse (~480 Zeilen) |
| `gui/pixel_analysis_tab.py` | ✅ | PixelAnalysisTab Klasse (~500 Zeilen) |
| `gui/report_tab.py` | ✅ | ReportTab Klasse (~500 Zeilen) |
| `gui/datalog_tab.py` | ✅ | DatalogTab Klasse (~420 Zeilen) - NEU v5.0.1 |
| `core/datalog_parser.py` | ✅ | TXT Datalog Parser (~380 Zeilen) - NEU v5.0.1 |
| `services/ppt_export.py` | ✅ | PPTExporter Klasse (~520 Zeilen) |
| **GESAMT extrahiert** | ✅ | **~5920 Zeilen in neuen Modulen** |

---

## 5. ABHÄNGIGKEITEN

### Core
- `pandas`, `numpy`, `matplotlib`, `pillow`, `Semi-ATE-STDF`, `scipy`

### Optional
- **Web**: `streamlit`, `plotly`
- **Desktop-Export**: `python-pptx`
- **Google**: `google-api-python-client`, `google-auth-*`, `google-generativeai`
- **Dev**: `pytest`, `black`, `ruff`, `mypy`

---

## 6. GIT & VERSIONIERUNG

| Eigenschaft    | Wert                                              |
|----------------|---------------------------------------------------|
| **Branch**     | main                                              |
| **Remote**     | origin → https://github.com/KRS-SZ/Data-Octopus.git |
| **Formatter**  | black (line-length=100)                           |
| **Linter**     | ruff                                              |
| **Tests**      | pytest (testpaths: tests/)                        |

### 6.1 Versionierung (Semantic Versioning)

| Regel | Beschreibung |
|-------|-------------|
| **Format** | `MAJOR.MINOR.PATCH` (z.B. `3.1.0`) |
| **APP_VERSION** | Konstante in Zeile 5 von `main_v3.py` |
| **Fenster-Titel** | Zeigt `"Measurement Data Visualization  v3.1.0"` |
| **MAJOR** | Große Architektur-Änderungen (z.B. main.py → main_v3.py) |
| **MINOR** | Neue Features (z.B. PLM-GAGE, Wafer Tab Redesign) |
| **PATCH** | Bugfixes, kleine Anpassungen |

### 6.2 Workflow – PFLICHT bei jeder Änderung

⚠️ **VOR jeder Code-Änderung:**
1. Aktuellen Stand **committen** als Backup
2. Commit-Message: `vX.Y.Z: Kurzbeschreibung der Änderung`

⚠️ **NACH jeder Änderung die zum Neukompilat führt:**
1. `APP_VERSION` in `main_v3.py` Zeile 5 hochzählen
2. Commit mit neuer Versionsnummer
3. Learnings-Datei aktualisieren

### 6.2.1 🚨 LOKALE VERSIONIERUNG – PFLICHT FÜR DEVMATE

⚠️ **BEI JEDER CODE-ÄNDERUNG DIE ICH (DEVMATE) MACHE:**
1. **BEVOR** ich die Änderung starte: `APP_VERSION` PATCH hochzählen (z.B. 3.2.0 → 3.2.1)
2. **DANN** die Code-Änderung durchführen
3. **DANN** committen mit neuer Versionsnummer

**WARUM:** Doppelte Sicherheit - jedes Kompilat hat eine eigene Version.

**BEISPIEL:**
```
Aktuell: v3.2.0
Devmate macht Änderung → Version wird 3.2.1 → Commit
Devmate macht weitere Änderung → Version wird 3.2.2 → Commit
```

**AUSNAHMEN:**
- Nur Rules-File Änderungen (kein Code) → keine Versionserhöhung nötig
- Rückgängig machen einer Änderung → keine Versionserhöhung nötig

### 6.3 Versionshistorie

| Version | Datum | Commit Hash | Beschreibung |
|---------|-------|-------------|-------------|
| `3.0.0` | 19.02.2026 | `375d992d` | PLM-GAGE Gruppe: Mean/Median/Position-based PPT Slides |
| `3.1.0` | 20.02.2026 | `6292fdcc` | PLM-GAGE Multi-Type, Wafer Tab Redesign, Agenda Tabelle, Calc Params Slide, Statistics Sub-Tabs, Multi-Wafer CSV |
| `3.1.1` | 20.02.2026 | `c8fdcedc` | Versionierung im Fenster-Titel, Heatmap-Koordinaten revertiert |
| `3.1.2` | 20.02.2026 | `cacf973` | Diffmap: Wafer-Tab-Abhängigkeit entfernt, Gruppen jetzt unabhängig |
| `3.1.3` | 20.02.2026 | `b0f471d` | Diffmap: extract_group_from_column() wie Wafer Tab |
| `3.1.4` | 20.02.2026 | `dc4ea8d` | Diffmap: Debug-Prints entfernt, Cleanup |
| `3.1.5` | 20.02.2026 | `8eac90d` | Diffmap: CSV-Lade-Logik mit Testnummern-Extraktion wie Wafer Tab |
| `3.1.6` | 20.02.2026 | `d1f83f7` | GRR Tab: Wafer Selection UI wie Wafer Tab (Header, Buttons, Listbox Format) |
| `3.1.7` | 23.02.2026 | `1fe887f` | Auto. Jobs: Multi-Folder Load, Do Job, Standard-Ordner, UI auf Englisch, Auto-Enable GRR |
| `3.1.8` | 23.02.2026 | `d465ead` | GRR Analysis Debug-Output, Auto Jobs Fixes |
| `3.1.9` | 23.02.2026 | `9c0489f` | Multi-Parameter Boxplot/Distribution, AM DATA CSV Format Konvertierung |
| `3.2.0` | 23.02.2026 | `1f21703` | Dynamische Parameter-Konvertierung zentral in simplify_param_name() |
| `3.2.5` | 24.02.2026 | `50daa84` | Diffmap Tab: Fix 1D Array ValueError bei DataFrame-Erstellung |
| `3.2.6` | 24.02.2026 | `f49f094` | Wafer Tab: Heatmap Achsenbeschriftung zeigt echte Die-Koordinaten |
| `3.2.7` | 24.02.2026 | `489c913` | Wafer Tab: Koordinatensystem - exakte Daten-Grenzen |
| `3.2.8` | 24.02.2026 | `627caad` | Fix ValueError beim Die-Klick (Series statt Skalar) |
| `3.2.9` | 24.02.2026 | `af90885` | Fix rotes Auswahlrechteck - selected_die_coords global |
| `3.2.10` | 24.02.2026 | `12b3f49` | Restore larger wafermap display with margins like v3.7 |
| `3.2.19` | 25.02.2026 | `c1037c8` | Fix SoftBins in Bin Summary Table - SoftBin-Spalte beim CSV-Laden als 'sbin' preserved |

---

## 7. BEKANNTE FEATURES / LETZTER STAND

- **PLM Image Processing**: Green Group Marker
- **Pixel Analysis Tab**: 25×25 Grid-Analyse
- **PPT Report**: Pixel-Support, Pixel-Annotation auf Slides
- **Multi-Wafer**: Vergleichsansicht mehrerer Wafer
- **Diffmap**: Parametervergleich zwischen Wafern
- **Boxplot Distribution**: Statistische Verteilungen
- **GRR (Gage R&R)**: Messsystem-Analyse
- **Charac.-Curve Tab**: Kennlinien (X/Y Parameterauswahl, Scatter/Line/Scatter+Line, Limits, Color per Wafer)

### 7.1 main_v3.py – AKTUELLER ENTWICKLUNGSSTAND (19.02.2026)

**Neue Datei `main_v3.py`** (~32.600 Zeilen) – enthält alle neuen GRR/PLM Features:

#### PLM Pixel GRR Analysis (Gage R&R Tab)
| Feature | Beschreibung |
|---------|--------------|
| **3 PLM Heatmaps nebeneinander** | 3 Wafer-Positionen werden gleichzeitig angezeigt |
| **Synchronisierte Rechteck-Auswahl** | Ein Rechteck auf einem Canvas → alle 3 synchronisiert |
| **Multi-Region PLM Analysis** | Add Region / Remove Region / Clear All Buttons |
| **Region Listbox** | Farbige R1, R2, R3... Einträge mit Koordinaten und Pixelanzahl |
| **plm_selected_areas** | Liste von `{'x', 'y', 'w', 'h', 'rect_ids'}` Dictionaries |
| **plm_region_colors** | 10 Farben für konsistente Visualisierung |

#### GRR Plots (3 Charts nebeneinander)
| Chart | Beschreibung |
|-------|--------------|
| **%GRR per Region** | Balkendiagramm mit 10%/30% Schwellwert-Linien |
| **ndc per Region** | Balkendiagramm mit ndc=5 Schwellwert-Linie |
| **Repeat. + Reprod. (%)** | Gestapeltes Balkendiagramm (blau + orange) |

#### Report Tab – PLM-GAGE Gruppe
| Parameter | Beschreibung |
|-----------|--------------|
| **Mean** | Eine Zusammenfassungsfolie mit Durchschnittswerten über alle Positionen |
| **Median** | Eine Zusammenfassungsfolie mit Median-Werten über alle Positionen |
| **Position based** | **EINE FOLIE PRO REGION/POSITION** mit Tabelle + Info-Box + 3 Charts |

#### PPT Slide Format (Position based)
```
┌─────────────────────────────────────────────────────────────┐
│ PLM Pixel Analysis: CDMEAN - Position (2,3) ✅ BEST        │
├─────────────────────────────────────────────────────────────┤
│ TABLE: Region | Position | Size | %GRR | ndc | Repeat% |   │
│        Reprod% | Result                                     │
├─────────────────────────────────────────────────────────────┤
│ INFO BOX:              │                                    │
│ 📊 PLM Type: CDMEAN    │                                    │
│ 📍 Position: (2,3)     │                                    │
│ 📏 Pixels: 625         │                                    │
│ 🔄 Runs: 5             │                                    │
│ ✅ BEST position       │                                    │
├─────────────────────────────────────────────────────────────┤
│ [%GRR Chart] │ [ndc Chart] │ [Repeat+Reprod Chart]         │
│ (current=color, others=gray)                                │
└─────────────────────────────────────────────────────────────┘
```

#### Weitere PPT Features
| Feature | Beschreibung |
|---------|--------------|
| **Agenda Slide mit Seitennummern** | Alle Abschnitte mit "Page X" |
| **Calculation Parameters Slide** | Wird nur EINMAL generiert (nicht pro Gruppe) |
| **Best/Worst Indikatoren** | ✅ BEST / ❌ WORST auf Position-Slides |

#### Wichtige Funktionen in main_v3.py
| Funktion | Zeilen ca. | Beschreibung |
|----------|------------|--------------|
| `generate_plm_gage_slides()` | ~21590-22050 | PPT-Slides für PLM-GAGE (Mean/Median/Position) |
| `generate_plm_image_analysis_slides()` | ~21368-21588 | PPT-Slides für Image Analysis PLM |
| `run_plm_pixel_grr()` | ~21076-21365 | Haupt-GRR-Analyse für PLM Pixel |
| `populate_grr_group_data()` | ~28082-28230 | Baut GRR-Gruppen inkl. PLM-GAGE |
| `_plm_refresh_area_list()` | ~20750-20775 | Aktualisiert Region-Listbox mit Farben |

#### Globale Variablen für PLM-GRR
| Variable | Typ | Beschreibung |
|----------|-----|--------------|
| `plm_pixel_grr_results` | dict | Key: `(die_x, die_y, plm_type)`, Value: GRR-Ergebnisse |
| `plm_selected_areas` | list | Liste von Region-Dictionaries |
| `plm_multi_state` | dict | State für 3 synchronisierte Canvas |
| `plm_region_colors` | list | 10 Farben für Regionen |
| `grr_selected_dies` | set | Ausgewählte Dies in Wafermap |

---

## 8. LESSONS LEARNED / BEKANNTE FALLEN

### 8.1 Python / tkinter
| Problem                       | Lösung                                              |
|-------------------------------|------------------------------------------------------|
| fb-python hat kein _tkinter   | **Python 3.13 lokal** verwenden (IMMER für GUI!)     |
| main.py ist riesig (~31k Zeilen) | Vorsicht bei Edits – gezielt str_replace nutzen   |

### 8.2 STDF-Parsing
| Problem                       | Lösung                                              |
|-------------------------------|------------------------------------------------------|
| Semi_ATE.STDF Import fehlt   | Fallback auf pystdf implementiert                    |
| Verschiedene STDF-Versionen   | Robuster Import mit try/except Kette                |

### 8.4 GUI Sub-Tabs (ttk.Notebook Nesting)
| Problem                       | Lösung                                              |
|-------------------------------|------------------------------------------------------|
| ttk.Notebook SubTab Style zerstört globale Tab-Größe | **KEIN ttk.Notebook** für Sub-Tabs verwenden! Stattdessen `tk.Button` + `pack_forget()`/`pack()` als manueller Tab-Umschalter |
| `style.configure("SubTab.TNotebook.Tab")` | Beeinflusst trotzdem den globalen `TNotebook.Tab` Style → NICHT benutzen |

### 8.5 Projekt-Organisation
| Alles lag im VS_Folder Root   | **Verschoben in `Data Octopus/` Unterordner** (Feb 2026) |
| .git musste mit umziehen      | `.git` + `.gitignore` mit verschoben → funktioniert  |
| PPT-Ordner blockiert          | Lock-Files (`~$*.pptx`) erst löschen, dann verschieben |
| Backup-Dateien (main Kopie*)  | Sind in `.gitignore` → werden nicht getrackt         |
| ⚠️ Uncommitted Änderungen gingen verloren (13.02.2026) | Beim Verschieben VS_Folder→Data Octopus/ wurde Git-Baseline statt Working Copy verwendet. **IMMER erst committen bevor Ordner verschoben werden!** |
| ⚠️ REGEL: Vor Ordner-Moves    | `git stash` oder `git commit` machen, DANN erst verschieben |

### 8.6 Gruppen- und Parameter-Auswahl (WICHTIG!)

#### ZENTRALE FUNKTION: `simplify_param_name()`
Diese Funktion in `main_v3.py` (~Zeile 1284) ist die **EINZIGE Stelle** wo Parameternamen formatiert werden!
Sie wird von ALLEN Tabs verwendet (Heatmap, Charac.-Curve, Statistik, Boxplot, Distribution, etc.)

#### Was macht sie?
1. **CSV `<>` Format**: Verwendet den Teil NACH `<>` (Langname mit echten Werten)
2. **Gruppen-Präfix entfernen**: NUR bekannte Gruppen (OPTIC, DC, ANLG, FUNC, etc.)
3. **Kodierte Werte konvertieren**:
   - `FV0P1` → `0.1V` (Force Voltage)
   - `FC0P2`, `FCn0P2` → `0.2mA`, `-0.2mA` (Force Current)
   - `AVEEn1p8` → `-1.80V`
   - `DACI3p0`, `DACIn0p6` → `3.00uA`, `-0.60uA`
   - `DC4p59` → `4.59%` (Duty Cycle)
4. **Cleanup**: Testnummern, `_X_X_X`, `_NV_`, `_PEQA_`, `FREERUN_X_` entfernen

#### WICHTIG: Bekannte Gruppen-Typen
```python
known_group_types = ['OPTIC', 'DC', 'ANLG', 'ANALOG', 'FUNC', 'FUNCTIONAL',
                     'EFUSE', 'INIT', 'INITIALIZE', 'DIGITAL', 'POWER', 'SOT']
```
⚠️ Nur diese Präfixe werden entfernt! `ALLON_NORM1PCT_` wird **NICHT** entfernt (ist kein Gruppenname).

#### Werte-Konvertierung (DYNAMISCH!)
Die Konvertierung ist **dynamisch** - wenn sich Werte ändern, werden sie automatisch konvertiert:
- `FV1P5` → `1.5V` (nicht nur `FV0P1` → `0.1V`)
- `AVEEn2p5` → `-2.50V` (nicht nur `AVEEn1p8`)
- Neue Patterns werden automatisch erkannt

#### FALLS NEUE GRUPPEN HINZUKOMMEN:
`known_group_types` Liste in `simplify_param_name()` erweitern!

#### FALLS NEUE KODIERUNGEN HINZUKOMMEN:
Neue Konvertierungs-Regex in `simplify_param_name()` hinzufügen:
```python
# Beispiel für neues Pattern XYZ:
def convert_xyz(match):
    value = match.group(1)
    return f"{value}Einheit"
name = re.sub(r'XYZ(\d+)', convert_xyz, name, flags=re.IGNORECASE)
```

---

## 9. KOMMUNIKATIONS-STIL

- Krzysztof kommuniziert auf **Deutsch**
- Er erwartet **direkte, technische Antworten** – kein Smalltalk
- Er will **sehen was passiert** (GUI starten, Output zeigen)
- **"Mach einfach"** = implementieren, nicht diskutieren
- Bei Fehlern: **sofort fixen**, nicht lang erklären warum
- **⚠️ WICHTIG: Wenn etwas unklar ist → NACHFRAGEN wie es umzusetzen ist, BEVOR Code geschrieben wird!**
- **🚨 KEINE RÜCKFRAGEN WIE "Willst du Option A oder B?"** - Einfach die beste Option umsetzen!
- **🚨 KEINE "Zusammenfassung" oder "Akzeptieren" verlangen** - Einfach machen und fertig!
- **🚨 EXISTIERENDEN CODE 1:1 ÜBERNEHMEN** - Wenn main.py funktioniert, den Code KOPIEREN, nicht "verbessern"!

---

## 9.1 🚨 REFACTORING-PLAN (Stand 24.02.2026)

### ANALYSE-ERGEBNIS: main_v3.py = 34.754 Zeilen monolithischer Code

#### 🔴 KRITISCHE FINDINGS

| Problem | Details |
|---------|---------|
| **Duplikation** | `BinningLookup` + `get_bin_colormap()` existieren ZWEIMAL (in core/binning.py UND main_v3.py) |
| **Ungenutzte Module** | `src/stdf_analyzer/core/stdf_parser.py` existiert aber wird NICHT verwendet |
| **~70+ Globale Variablen** | `current_stdf_data`, `grouped_parameters`, `test_limits`, etc. |
| **Klare Funktions-Cluster** | Können als separate Module extrahiert werden |

#### FUNKTIONS-CLUSTER (identifiziert)

| Cluster | Zeilen ca. | Extrahierbar als |
|---------|------------|------------------|
| Wafer Tab | 3000-4500 | `gui/wafer_tab.py` |
| Diffmap Tab | 5500-6500 | `gui/diffmap_tab.py` |
| Statistics | 5000-6500 | `gui/statistics_tab.py` |
| GRR Tab | 20000-22000 | `gui/grr_tab.py` |
| PPT Export | 21000-23000 | `services/ppt_export.py` |
| Multi-Wafer | 15000-17000 | `gui/multi_wafer_tab.py` |

### REFACTORING-PHASEN

#### Phase 1: Quick Wins (30 min) ⭐ START HIER
```python
# In main_v3.py ändern:
from src.stdf_analyzer.core.binning import BinningLookup, get_bin_colormap
# → Lokale Kopien in main_v3.py LÖSCHEN (~140 Zeilen weniger)
```

#### Phase 2: config.py erstellen (1h)
```python
# src/stdf_analyzer/core/config.py
KNOWN_GROUP_TYPES = ['OPTIC', 'DC', 'ANLG', 'ANALOG', 'FUNC', 'FUNCTIONAL',
                     'EFUSE', 'INIT', 'INITIALIZE', 'DIGITAL', 'POWER', 'SOT']
VALUE_PATTERNS = {...}
CLEANUP_PATTERNS = ['FREERUN', 'INTFRAME', '_NV_', '_PEQA_', '_X_X_X']
```

#### Phase 3: parameter_utils.py extrahieren (2h)
```
src/stdf_analyzer/core/parameter_utils.py
├── simplify_param_name()       # Aus main_v3.py Zeile 1284
├── extract_group_from_column() # Aus main_v3.py Zeile 1395
└── convert_coded_value()       # Neue Helper-Funktion
```

#### Phase 4: AppState-Klasse (3h)
```python
# src/stdf_analyzer/core/app_state.py
class AppState:
    def __init__(self):
        self.current_stdf_data = None
        self.grouped_parameters = {}
        self.test_parameters = {}
        self.multiple_stdf_data = []
        # ... ersetzt 70+ globale Variablen
```

#### Phase 5: Tab-Module (1 Woche)
```
src/stdf_analyzer/gui/
├── wafer_tab.py      (~1500 Zeilen)
├── diffmap_tab.py    (~1000 Zeilen)
├── statistics_tab.py (~1500 Zeilen)
├── grr_tab.py        (~2000 Zeilen)
└── ppt_export.py     (~2000 Zeilen)
```

### WORKFLOW FÜR REFACTORING
1. ⚠️ **VOR jeder Änderung:** `git commit` als Backup
2. ⚠️ **Nach jeder Phase:** App testen
3. ⚠️ **Alte Funktionen erst löschen wenn Import funktioniert**

---

## 9.2 🔧 BINNING-FEATURE (Stand 24.02.2026)

### ✅ ERLEDIGT (v3.2.11 - v3.2.14)

| Version | Feature |
|---------|---------|
| **3.2.11** | Show Bins Popup erweitert: 2 Tabs (Bin Definitions + Test Definitions mit 120 Tests) |
| **3.2.12** | "Binning" Gruppe im Group-Dropdown hinzugefügt |
| **3.2.13** | Fix ValueError bei Binning Gruppe (bin/softbin/hardbin sind keine test_keys) |
| **3.2.14** | Binning Gruppe an 2. Stelle + korrekte SoftBin/HardBin Erkennung |

### AKTUELLER STAND
- **"Binning" Gruppe** erscheint jetzt an **2. Stelle** im Group-Dropdown (direkt nach "All Groups")
- **HardBin und SoftBin** werden korrekt erkannt (2 parameters)
- **Show Bins Button** zeigt:
  - Tab 1: 15 Bin-Definitionen mit Farben
  - Tab 2: 120 Test-Definitionen mit Suchfunktion (HBin, SBin, Start/Max Test#, Comment)

### 🔄 TODO FÜR MORGEN
1. **Testen** ob Binning-Gruppe korrekt funktioniert (Wafermap nach HardBin/SoftBin färben)
2. **Prüfen** ob andere Tabs (Multi-Wafer, Diffmap, GRR) auch Binning-Gruppe haben sollten
3. **Optional**: Binning-Excel automatisch laden wenn Projekt-Ordner gewählt wird

### EXCEL-DATEI
`Data\AM Data\Binning\Copy of HN2_Binning&TestNumber_V0.36.xlsx`
- Sheet: "BinTable"
- 15 Bin-Definitionen (hbin 1-15)
- 120 Test-Definitionen

---

## 10. VERWANDTE PROJEKTE

| Projekt         | Ordner                                                    | Beschreibung                        |
|-----------------|-----------------------------------------------------------|-------------------------------------|
| Auto Sequencer  | `c:\Users\szenklarz\Desktop\VS_Folder\Auto Sequencer\`   | Separates Projekt (Test-Sequenzierung) |
| Data Octopus    | `c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\`     | **Dieses Projekt** (STDF-Analyse)   |

### 10.1 Datenquellen

| Quelle | Pfad / URL | Beschreibung |
|--------|-----------|--------------|
| **Manifold (Odin)** | `odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tuskar/uled/incoming/tool_data/{TESTER}` | Produktions-Testdaten pro Anlage (z.B. `9ATE3`) |
| **Lokal** | `Data Octopus\AM Data\` | Lokale Kopien der Testdaten für Offline-Arbeit |

⚠️ Manifold ist ein **Meta-interner Webserver** – nur aus dem Firmen-Netzwerk erreichbar (nicht von zu Hause/VPN).
Jede Anlage (Tester) hat einen eigenen Pfad (z.B. `9ATE3`). Dort liegen STDF, CSV, PLM-Dateien etc.
PLM-Types auf Manifold: **Bridged, Bridged-Pixels, Stitched, UniformitySyn** und ggf. weitere je nach Testprogramm.

---

## 11. WICHTIGE DATEIPFADE

```
Projekt:     c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\
Code:        c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\code\
Python 3.13: C:\Users\szenklarz\AppData\Local\Programs\Python\Python313\python.exe
Main GUI:    Data Octopus\code\main.py  ← AKTUELLE VERSION (v4.0+)
Core Module: Data Octopus\code\src\stdf_analyzer\core\
Web App:     Data Octopus\code\src\stdf_analyzer\web\app.py
Tests:       Data Octopus\code\tests\
Testdaten:   Data Octopus\AM Data\
Jobs:        Data Octopus\saved_jobs\
PPT Output:  Data Octopus\Report\
Rules:       Data Octopus\.llms\rules\data_octopus.md  (← DIESE DATEI)
```

---

## 12. BEI JEDER ÄNDERUNG

- **Diese Datei** (`.llms/rules/data_octopus.md`) aktualisieren bei neuen Learnings
- Neue Features in Abschnitt 7 dokumentieren
- Neue Fallen/Fixes in Abschnitt 8 ergänzen
- Bei Struktur-Änderungen Abschnitt 4 aktualisieren

---

## 13. 🚀 TODO NÄCHSTE SESSION (27.02.2026) – VOLLSTÄNDIGE MODULARISIERUNG

### GOAL: main_v5.py soll ALLE Features von main.py haben

**AKTUELLER STAND:**
- ✅ main.py (v4.0.0) = ~34.500 Zeilen, MONOLITHISCH aber FUNKTIONIERT
- ✅ main_v5.py (v5.0.0) = ~470 Zeilen Controller, MODULAR aber VEREINFACHTE TABS
- ⚠️ GUI-Tab Module = ~500 Zeilen pro Tab (VORLAGEN, nicht vollständiger Code)

**ZIEL:**
- 🔒 main.py BLEIBT UNVERÄNDERT (Desktop-Version)
- main_v5.py wird voll funktionsfähig mit ALLEN Features
- GUI-Tab Module bekommen den KOMPLETTEN Code aus main.py

### REFACTORING-LISTE (nach Priorität)

| # | Tab | Zeilen in main.py | Zeilen aktuell | TODO |
|---|-----|-------------------|----------------|------|
| 1 | **Wafer Tab** | ~3.000 | ~550 | Code aus main.py extrahieren |
| 2 | **Multi-Wafer Tab** | ~2.500 | ~450 | Code aus main.py extrahieren |
| 3 | **Diffmap Tab** | ~1.500 | ~640 | Code aus main.py extrahieren |
| 4 | **Statistics Tab** | ~2.000 | ~450 | Code aus main.py extrahieren |
| 5 | **Charac-Curve Tab** | ~1.500 | ~480 | Code aus main.py extrahieren |
| 6 | **GRR Tab** | ~5.000 | ~470 | Code aus main.py extrahieren |
| 7 | **Pixel Analysis Tab** | ~2.000 | ~500 | Code aus main.py extrahieren |
| 8 | **Report/PPT Tab** | ~6.000 | ~500 | Code aus main.py extrahieren |
| **GESAMT** | | **~25.000** | **~4.500** | **~20.000 Zeilen zu extrahieren** |

### WORKFLOW PRO TAB

1. Code-Block in main_dev.py identifizieren (Zeilen X bis Y)
2. Globale Variablen → als Klassen-Attribute umwandeln
3. Funktionen → als Klassen-Methoden umwandeln
4. In gui/{tab}_tab.py einfügen
5. In main_v5.py testen
6. Commit nach jedem Tab

### GESCHÄTZTER AUFWAND

| Phase | Dauer |
|-------|-------|
| Wafer Tab | 2-3h |
| Multi-Wafer Tab | 2-3h |
| Diffmap Tab | 1-2h |
| Statistics Tab | 2h |
| Charac-Curve Tab | 1-2h |
| GRR Tab | 4-5h (komplex!) |
| Pixel Analysis | 2h |
| Report/PPT | 4-5h (komplex!) |
| **GESAMT** | **~20-25h (3-4 Sessions)** |

### WICHTIG

⚠️ **main.py (v4.0.0) NIEMALS ANFASSEN** – das ist die funktionierende Desktop-Version!
⚠️ **Nur main_v5.py und die GUI-Module bearbeiten**
⚠️ **Nach jedem Tab: Testen ob main_v5.py noch startet**
