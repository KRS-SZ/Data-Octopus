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
# Desktop-GUI (Standard)
& "C:\Users\szenklarz\AppData\Local\Programs\Python\Python313\python.exe" "c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\main.py"

# Web-App (Streamlit)
streamlit run "c:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\src\stdf_analyzer\web\app.py"
```

⚠️ **IMMER Python 3.13 lokal verwenden** (nicht fb-python) – wegen tkinter!

---

## 4. ARCHITEKTUR & PROJEKT-STRUKTUR

```
Data Octopus/
├── main.py                    # Haupt-Desktop-Anwendung (~31k Zeilen, monolithisch)
├── src/
│   └── stdf_analyzer/
│       ├── core/              # Business-Logik (UI-unabhängig)
│       │   ├── binning.py     # Bin-Definitionen und Lookup
│       │   ├── stdf_parser.py # STDF/CSV Parsing
│       │   └── wafermap.py    # Wafermap-Generierung
│       ├── gui/               # (Placeholder – GUI ist in main.py)
│       ├── services/          # Externe Dienste
│       └── web/               # Streamlit Web-App
│           ├── app.py
│           └── app_nicegui.py
├── tests/                     # Unit Tests (pytest)
├── saved_jobs/                # Gespeicherte Job-Konfigurationen
├── Jobs/                      # Job-Dateien
├── AM Data/                   # STDF/CSV Testdaten
├── PPT/                       # PowerPoint-Reports (Output)
├── Tooltest/                  # Test-Daten für Entwicklung
├── pyproject.toml             # Projekt-Konfiguration
├── requirements.txt           # Dependencies
├── Dockerfile                 # Docker-Support
├── docker-compose.yml
└── .gitignore
```

### 4.1 Hinweis zur Struktur
- `main.py` ist **monolithisch** (~31.000 Zeilen) – enthält die komplette Desktop-GUI
- `src/stdf_analyzer/core/` enthält extrahierte Module (Binning, Parser, Wafermap)
- Viele `main - Kopie*.py` und `main *.py` Dateien = **Backups** verschiedener Versionen (in .gitignore)

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

---

## 9.1 🚨 MONTAG 24.02.2026 – ERSTER SCHRITT

**FRAGE SOFORT:**
> "Wie sollen wir den Auto. Jobs Feature fertig machen? Folgende Punkte sind offen:
> 1. **Load Wafers Button** - soll der einen Folder-Dialog öffnen oder Files einzeln?
> 2. **Do Job für Report** - wie genau soll die PPT erstellt werden?
> 3. **Report Gruppen/Parameter** - welche genau sollen gespeichert werden?"

**Aktueller Stand v3.1.7 (WIP):**
- ✅ Tab umbenannt: "Settings" → "🔄 Auto. Jobs"
- ✅ Apply & Run Job UI hinzugefügt
- ⚠️ Load Wafers Button noch nicht getestet
- ⚠️ Do Job Funktion noch nicht fertig

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
Python 3.13: C:\Users\szenklarz\AppData\Local\Programs\Python\Python313\python.exe
Main GUI:    Data Octopus\main.py
Core Module: Data Octopus\src\stdf_analyzer\core\
Web App:     Data Octopus\src\stdf_analyzer\web\app.py
Tests:       Data Octopus\tests\
Testdaten:   Data Octopus\AM Data\
Jobs:        Data Octopus\saved_jobs\
PPT Output:  Data Octopus\PPT\
Rules:       Data Octopus\.llms\rules\data_octopus.md  (← DIESE DATEI)
```

---

## 12. BEI JEDER ÄNDERUNG

- **Diese Datei** (`.llms/rules/data_octopus.md`) aktualisieren bei neuen Learnings
- Neue Features in Abschnitt 7 dokumentieren
- Neue Fallen/Fixes in Abschnitt 8 ergänzen
- Bei Struktur-Änderungen Abschnitt 4 aktualisieren
