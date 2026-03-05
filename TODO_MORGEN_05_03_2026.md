# TODO für morgen (05.03.2026)

## AKTUELLE DATEI: `main_v5.1.py` (35.012 Zeilen)

---

## ✅ ERLEDIGT HEUTE

### 1. Load Wafer Button + Manifold Integration (in main_v5.1.py)
- **Position:** Zeile ~3920 (unter "Wafer Selection" im linken Panel)
- **Button:** `📂 Load Wafer`
- **Dialog:** 520x480 Pixel mit 3 Optionen:
  - 💻 **Load lokal** - STDF/CSV/MC-300 vom lokalen Dateisystem
  - ⚡ **Manifold (fast)** - Download ZIP + nur CSV extrahieren (keine PLM Bilder)
  - 📦 **Manifold (complete)** - Download komplette ZIP (CSV + PLM Bilder)

### 2. Manifold Browser
- **Fenster:** 750x600 Pixel
- **Sites:** Tuscar, Taiwan, Regensburg
- **Tools:**
  - Tuscar: 9ATE1, 9ATE2, 9ATE3, 9ATE4
  - Taiwan: TPW-CP2
  - Regensburg: RGS-ATE
- **Manifold Pfade:**
  ```
  Tuscar:     odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tuskar/uled/incoming/tool_data/{TOOL}
  Taiwan:     odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tpw/PEQUIN/CP2
  Regensburg: odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/arranmore/testing
  ```

### 3. Funktionen hinzugefügt
- `show_load_wafer_dialog()` - Zeigt Auswahl-Dialog
- `load_local_wafer()` - Lädt lokale Datei (STDF/CSV/MC-300)
- `load_manifold_fast()` / `load_manifold_complete()` - Startet Manifold Browser
- `show_manifold_browser(mode)` - Zeigt Manifold-Dateiliste
- `load_from_manifold_fast()` - Download + nur CSV extrahieren
- `load_from_manifold_complete()` - Download + alles extrahieren (PLM verfügbar)
- `load_csv_wafermap_from_path()` - Lädt CSV von beliebigem Pfad

---

## ⏳ OFFEN FÜR MORGEN

### 1. 🔴 DASHBOARD TAB (FEHLT KOMPLETT!)

Der Dashboard Tab muss als **erster Tab** (vor Wafer Tab) hinzugefügt werden.

**Features:**
- Tool-Cards für jede Anlage:
  - **Tuscar ATE:** 9ATE1, 9ATE2, 9ATE3, 9ATE4 (blau)
  - **Tuscar Prober:** 9PRB3, 9PRF3 (lila) - optional mit Checkbox
  - **Taiwan:** TPW-CP2 (orange)
  - **Regensburg:** RGS-ATE (cyan) - "Coming soon"

- **Browse Buttons** für jedes Tool → öffnet Manifold im Web-Browser

- **5 Charts (Pie/Bar):**
  1. Wafers per Tool (Balkendiagramm)
  2. Site Distribution (Tortendiagramm: Tuscar/Taiwan/Regensburg)
  3. Color/Product Distribution (Tortendiagramm mit "NA" Kategorie)
  4. Timeline (Wafers pro Tag)
  5. Lots per Tool (Balkendiagramm)

- **Checkboxes:**
  - Taiwan (default ON)
  - Prober (default OFF)

**Code-Vorlage (aus heutiger Session):**
```python
# Tab 1: DASHBOARD (vor allen anderen!)
tab_dashboard = tk.Frame(tab_parent)
tab_parent.insert(0, tab_dashboard, text="📊 DASH")

# Manifold Pfade
MANIFOLD_BASE_TSK = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tuskar/uled/incoming/tool_data"
MANIFOLD_BASE_TPW = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tpw/PEQUIN/CP2"
MANIFOLD_BASE_RGS = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/arranmore/testing"

TOOLS = {
    "ATE": ["9ATE1", "9ATE2", "9ATE3", "9ATE4"],
    "Prober": ["9PRB3", "9PRF3"],
    "Taiwan": ["TPW-CP2"],
    "Regensburg": ["RGS-ATE"]  # Coming soon
}

COLORS = {
    "ate": "#2196F3",        # Blue for Tuscar ATE
    "prober": "#9C27B0",     # Purple for Prober
    "taiwan": "#FF5722",     # Orange for Taiwan
    "regensburg": "#00BCD4", # Cyan for Regensburg
}
```

### 2. Toolbar-Vereinfachung (Wafer Tab)

**Aktuell (2 Zeilen):**
```
Zeile 1: Format | Load STDF | Project Folder | Group | Param | Refresh | Custom Test | Save Data
Zeile 2: Load Binning | Show Bins | Grid | Zoom+/- | Reset | Clear Sel | View | Type | PLM
```

**Neu (1 Zeile):**
```
Group | Param | Binning | Show Bins | Grid | Zoom+/- | Reset | Clear Sel | View | Type | PLM | Custom Test | Save Data
```

**Zu entfernen:**
- Format-Dropdown
- Load STDF Button
- Project Folder Button

**Grund:** "Load Wafer" Button übernimmt jetzt ALLE Formate (STDF, CSV, MC-300)

### 3. Testen

Nach allen Änderungen:
1. App starten
2. Dashboard Tab prüfen (Charts, Tool-Cards, Browse Buttons)
3. Load Wafer Button prüfen (Dialog, alle 3 Optionen)
4. Manifold Browser prüfen (Refresh, Dateiliste, Load)

---

## MANIFOLD HINWEIS

⚠️ **Kein echtes Streaming auf Windows möglich!**
- Manifold CLI (`manifold --vip get`) lädt IMMER die komplette Datei
- "Fast" = Download + nur CSV aus ZIP lesen + Temp löschen
- "Complete" = Download + alles entpacken + PLM verfügbar

Für Taiwan-Dateien (70-112 GB): Besser lokal kopieren oder nur Dashboard für Übersicht nutzen.

---

## DATEIEN

| Datei | Beschreibung |
|-------|--------------|
| `main_v5.1.py` | Aktuelle Version mit Load Wafer Button (35.012 Zeilen) |
| `main_v5.1_git.py` | Backup der Git-Version v5.1.0 |
| `main_v5.py` | Modulare Version (9 GUI-Module, Controller ~470 Zeilen) |
| `dashboard_tab.py` | (existiert in src/stdf_analyzer/gui/ - kann als Vorlage dienen) |

---

## GIT STATUS

Letzte Version auf Git: `b4f0082` - v5.1.0 (ohne heutige Änderungen)

**WICHTIG:** Nach Fertigstellung committen!
```bash
git add code/main_v5.1.py
git commit -m "v5.2.0: Dashboard Tab + Load Wafer Button + Manifold Integration"
```
