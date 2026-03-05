"""
Data Octopus - NiceGUI Web Application

Modulare Web-Version der Desktop-App mit gleichem Design und Layout.

Architektur:
    main.py (dieser File)
        ├── Components
        │   ├── toolbar.py (Toolbar1, Toolbar2)
        │   └── sidebar.py (WaferSidebar)
        │
        ├── Tabs
        │   ├── wafer_tab.py
        │   ├── multi_wafer_tab.py
        │   ├── diffmap_tab.py
        │   ├── grr_tab.py
        │   ├── report_tab.py
        │   └── config_tab.py
        │
        └── State
            └── state.py (AppState)

Usage:
    python main.py
    → Opens http://localhost:8080
"""

import sys
import os
import tempfile
from pathlib import Path

# Add paths
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from nicegui import ui, app, events
import pandas as pd

# Local imports
from .state import app_state, WaferData
from .components import Toolbar1, Toolbar2, WaferSidebar
from .tabs import WaferTab, MultiWaferTab, DiffmapTab, GRRTab, ReportTab, ConfigTab

# Core imports
try:
    from src.stdf_analyzer.core.stdf_parser import parse_stdf_file, parse_csv_file
    from src.stdf_analyzer.core.binning import BinningLookup
    STDF_AVAILABLE = True
except ImportError:
    STDF_AVAILABLE = False
    print("⚠️ STDF parser not available")

# Default paths for file browser
DEFAULT_DATA_PATHS = [
    r"C:\Users\szenklarz\Desktop\VS_Folder\AM Data",
    r"C:\Users\szenklarz\Desktop\VS_Folder\Tooltest",
    r"C:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\Data",
]


# ============================================================================
# Main Application Class
# ============================================================================

class DataOctopusApp:
    """
    Haupt-Applikation - entspricht main.py der Desktop-Version.
    """

    def __init__(self):
        self.app_state = app_state

        # UI Components
        self.toolbar1 = None
        self.toolbar2 = None
        self.sidebar = None

        # Main Tabs
        self.main_tab_buttons = {}
        self.main_tab_contents = {}
        self.current_main_tab = "wafer"

        # Tab Instances
        self.tabs = {
            'config': None,
            'wafer': None,
            'multi_wafer': None,
            'diffmap': None,
            'grr': None,
            'report': None,
        }

    def build(self):
        """Hauptseite aufbauen."""
        ui.page_title('Data Octopus - Web')

        # Full height layout
        with ui.column().classes('w-full h-screen'):
            # Header mit Main Tabs
            self._build_main_tabs()

            # Toolbar 1 (Group, Param - VEREINFACHT)
            self.toolbar1 = Toolbar1(
                on_group_change=self._on_group_change,
                on_param_change=self._on_param_change,
                on_refresh=self._refresh,
            )
            self.toolbar1.build()

            # Toolbar 2 (Binning, Zoom, View)
            self.toolbar2 = Toolbar2(
                on_load_binning=self._load_binning,
                on_grid_toggle=self._on_grid_toggle,
                on_zoom_in=self._on_zoom_in,
                on_zoom_out=self._on_zoom_out,
                on_reset=self._on_reset,
                on_view_change=self._on_view_change,
                on_type_change=self._on_type_change,
            )
            self.toolbar2.build()

            # Main Content Area (Sidebar + Tab Content)
            with ui.row().classes('w-full flex-1 gap-0'):
                # Sidebar mit LOAD WAFER Button
                self.sidebar = WaferSidebar(
                    on_load_wafer=self._load_wafer,  # NEU: Einziger Lade-Button
                    on_prev=self._on_wafer_prev,
                    on_next=self._on_wafer_next,
                    on_select_all=self._on_wafer_select_all,
                    on_unload_all=self._on_wafer_unload_all,
                    on_wafer_select=self._on_wafer_select,
                )
                self.sidebar.build()

                # Tab Contents
                with ui.column().classes('flex-1 overflow-auto'):
                    self._build_tab_contents()

            # Footer
            with ui.row().classes('w-full bg-gray-100 px-4 py-1 border-t'):
                ui.label('Data Octopus v1.0.0 (NiceGUI)').classes('text-xs text-gray-500')
                ui.space()
                ui.label('© Krzysztof Szenklarz').classes('text-xs text-gray-500')

        # Initial tab
        self._switch_main_tab('wafer')

    def _build_main_tabs(self):
        """Main Tab Bar erstellen (wie Desktop-App)."""
        with ui.row().classes('w-full bg-white border-b items-center px-2 py-1 gap-1'):
            # App Icon/Title
            ui.icon('analytics', size='28px').classes('text-blue-600')

            # Main Tab Buttons
            tab_config = [
                ('config', '⚙️ Config'),
                ('wafer', '📊 Wafer'),
                ('multi_wafer', '📦 Multi-Wafer'),
                ('diffmap', '🔄 Diffmap'),
                ('grr', '📏 Gage R&R'),
                ('report', '📄 Report'),
            ]

            for tab_id, label in tab_config:
                btn = ui.button(label, on_click=lambda t=tab_id: self._switch_main_tab(t))
                btn.props('flat dense')
                if tab_id == 'wafer':
                    btn.classes('bg-blue-100 font-bold')
                self.main_tab_buttons[tab_id] = btn

            # Spacer
            ui.space()

            # Language Selector (rechts)
            ui.select(options=['English', 'Deutsch'], value='English').classes('w-28').props('dense')

    def _build_tab_contents(self):
        """Tab-Inhalte erstellen."""
        # Config Tab
        with ui.column().classes('w-full h-full hidden') as content:
            self.main_tab_contents['config'] = content
            self.tabs['config'] = ConfigTab(self.app_state)
            self.tabs['config'].build()

        # Wafer Tab
        with ui.column().classes('w-full h-full') as content:
            self.main_tab_contents['wafer'] = content
            self.tabs['wafer'] = WaferTab(self.app_state)
            self.tabs['wafer'].build()

        # Multi-Wafer Tab
        with ui.column().classes('w-full h-full hidden') as content:
            self.main_tab_contents['multi_wafer'] = content
            self.tabs['multi_wafer'] = MultiWaferTab(self.app_state)
            self.tabs['multi_wafer'].build()

        # Diffmap Tab
        with ui.column().classes('w-full h-full hidden') as content:
            self.main_tab_contents['diffmap'] = content
            self.tabs['diffmap'] = DiffmapTab(self.app_state)
            self.tabs['diffmap'].build()

        # GRR Tab
        with ui.column().classes('w-full h-full hidden') as content:
            self.main_tab_contents['grr'] = content
            self.tabs['grr'] = GRRTab(self.app_state)
            self.tabs['grr'].build()

        # Report Tab
        with ui.column().classes('w-full h-full hidden') as content:
            self.main_tab_contents['report'] = content
            self.tabs['report'] = ReportTab(self.app_state)
            self.tabs['report'].build()

    def _switch_main_tab(self, tab_id: str):
        """Main Tab wechseln."""
        self.current_main_tab = tab_id
        self.app_state.current_main_tab = tab_id

        # Button Styles
        for tid, btn in self.main_tab_buttons.items():
            if tid == tab_id:
                btn.classes(remove='', add='bg-blue-100 font-bold')
            else:
                btn.classes(remove='bg-blue-100 font-bold', add='')

        # Content Visibility
        for tid, content in self.main_tab_contents.items():
            if tid == tab_id:
                content.classes(remove='hidden')
            else:
                content.classes(add='hidden')

        # Sidebar für bestimmte Tabs zeigen/verstecken
        if tab_id in ['wafer', 'multi_wafer']:
            self.sidebar.container.classes(remove='hidden')
        else:
            self.sidebar.container.classes(add='hidden')

    # ========================================================================
    # Event Handlers
    # ========================================================================

    def _load_wafer(self):
        """
        LOAD WAFER - Einfacher tkinter File Dialog.
        Öffnet sofort den Windows File Dialog - kein extra Popup.
        """
        import tkinter as tk
        from tkinter import filedialog

        # tkinter root erstellen (versteckt)
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        # File Dialog öffnen
        paths = filedialog.askopenfilenames(
            title='Wafer-Dateien auswählen (CSV oder STDF)',
            filetypes=[
                ('Wafer-Dateien', '*.csv *.stdf'),
                ('CSV', '*.csv'),
                ('STDF', '*.stdf'),
                ('Alle Dateien', '*.*'),
            ],
            initialdir=r'C:\Users\szenklarz\Desktop\VS_Folder\AM Data'
        )
        root.destroy()

        if not paths:
            return

        # Support-Ordner suchen (Images, PLM im Parent/Sibling)
        base_dir = os.path.dirname(paths[0])
        self._find_support_folders(base_dir)

        # Dateien laden
        success = 0
        for fpath in list(paths)[:20]:
            if self._load_single_file(fpath):
                success += 1

        if success > 0:
            self._update_after_load()
            ui.notify(f'✅ {success} Wafer geladen!', type='positive')

    def _find_support_folders(self, base_path: str):
        """Sucht Images, PLM Ordner in Parent und Siblings."""
        image_folders = ['ImageCaptures', 'Images', 'Die_Images']
        plm_folders = ['PLMFiles', 'PLM', 'PLM_Files']

        search_paths = [base_path]
        parent = os.path.dirname(base_path)
        if parent:
            search_paths.append(parent)
            try:
                for sib in os.listdir(parent):
                    sib_path = os.path.join(parent, sib)
                    if os.path.isdir(sib_path):
                        search_paths.append(sib_path)
            except:
                pass

        for sp in search_paths:
            if not self.app_state.image_directory:
                for folder in image_folders:
                    p = os.path.join(sp, folder)
                    if os.path.isdir(p):
                        self.app_state.image_directory = p
                        break
            if not self.app_state.plm_directory:
                for folder in plm_folders:
                    p = os.path.join(sp, folder)
                    if os.path.isdir(p):
                        self.app_state.plm_directory = p
                        break

    def _load_single_file(self, filepath: str) -> bool:
        """Lädt eine einzelne Datei."""
        try:
            filename = os.path.basename(filepath)
            ext = Path(filepath).suffix.lower()

            if ext == '.csv':
                from .csv_loader import load_csv_file_full
                result = load_csv_file_full(filepath)
                if result:
                    wafer_data = WaferData(
                        filename=filename,
                        wafer_id=result.wafer_id,
                        dataframe=result.dataframe,
                        test_parameters=result.test_parameters,
                        grouped_parameters=result.grouped_parameters,
                        test_limits=result.test_limits,
                    )
                    self.app_state.add_wafer(wafer_data)
                    return True
            elif ext == '.stdf' and STDF_AVAILABLE:
                data = parse_stdf_file(filepath, verbose=False)
                if data:
                    wafer_data = WaferData(
                        filename=filename,
                        wafer_id=data.wafer_id or filename,
                        dataframe=data.dataframe,
                        test_parameters=data.test_parameters,
                    )
                    self.app_state.add_wafer(wafer_data)
                    return True
        except Exception as ex:
            print(f'Fehler bei {filepath}: {ex}')
        return False

    def _update_after_load(self):
        """UI nach dem Laden aktualisieren."""
        data = self.app_state.current_data
        if not data:
            return

        # Gruppen laden
        groups = list(data.grouped_parameters.keys())
        self.toolbar1.update_groups(groups)

        # Parameter laden
        param_options = []
        for test_key, display_name in data.test_parameters.items():
            param_options.append(f"{test_key}: {display_name}")
        self.toolbar1.update_params(param_options)

        # Sidebar aktualisieren
        wafers = list(self.app_state.loaded_files.keys())
        self.sidebar.update_wafers(wafers, self.app_state.current_file)

        # Wafer Tab laden
        if self.tabs['wafer']:
            self.tabs['wafer'].load_data(
                df=data.dataframe,
                wafer_id=data.wafer_id,
                test_params=data.test_parameters,
                grouped_params=data.grouped_parameters,
            )

        self._update_ui()

    def _open_project_folder(self):
        """Projekt-Ordner öffnen - LÄDT ALLE DATEIEN AUTOMATISCH wie Desktop-GUI!"""
        with ui.dialog() as dialog, ui.card().classes('w-[500px]'):
            ui.label('📁 Project Folder').classes('text-lg font-bold')
            ui.label('Ordner-Pfad eingeben - ALLE CSV/STDF werden automatisch geladen!').classes('text-sm text-gray-600')

            # Pfad-Eingabe
            path_input = ui.input(
                value=DEFAULT_DATA_PATHS[0] if DEFAULT_DATA_PATHS else '',
                label='Ordner-Pfad'
            ).classes('w-full')

            # Schnellauswahl
            if DEFAULT_DATA_PATHS:
                ui.label('Schnellauswahl:').classes('text-sm text-gray-600 mt-2')
                with ui.row().classes('gap-1 flex-wrap'):
                    for p in DEFAULT_DATA_PATHS:
                        if os.path.exists(p):
                            name = os.path.basename(p)
                            def select_path(path=p):
                                path_input.value = path
                            ui.button(name, on_click=select_path).props('flat dense outline')

            # Status-Anzeige
            status_label = ui.label('').classes('text-sm mt-2')

            async def load_all_files():
                """ALLE Dateien aus dem Ordner laden - wie Desktop-GUI!"""
                path = path_input.value
                if not path or not os.path.exists(path):
                    ui.notify('Pfad nicht gefunden!', type='warning')
                    return

                # Speichere Project Folder
                self.app_state.project_folder = path

                # Image- und PLM-Ordner suchen (wie Desktop-GUI!)
                # Suche AUCH im übergeordneten Ordner und dessen Unterordnern!
                image_folders = ['ImageCaptures', 'Images', 'images', 'Die_Images', 'die_images']
                plm_folders = ['PLMFiles', 'PLM', 'plm', 'PLM_Files', 'plm_files']

                # 1. Im aktuellen Ordner suchen
                for folder in image_folders:
                    img_path = os.path.join(path, folder)
                    if os.path.exists(img_path) and os.path.isdir(img_path):
                        self.app_state.image_directory = img_path
                        print(f"  Found Image directory: {img_path}")
                        break

                for folder in plm_folders:
                    plm_path = os.path.join(path, folder)
                    if os.path.exists(plm_path) and os.path.isdir(plm_path):
                        self.app_state.plm_directory = plm_path
                        print(f"  Found PLM directory: {plm_path}")
                        break

                # 2. Im ÜBERGEORDNETEN Ordner suchen (wie Desktop-GUI!)
                parent_path = os.path.dirname(path)
                if parent_path and not self.app_state.image_directory:
                    for folder in image_folders:
                        img_path = os.path.join(parent_path, folder)
                        if os.path.exists(img_path) and os.path.isdir(img_path):
                            self.app_state.image_directory = img_path
                            print(f"  Found Image directory (parent): {img_path}")
                            break

                if parent_path and not self.app_state.plm_directory:
                    for folder in plm_folders:
                        plm_path = os.path.join(parent_path, folder)
                        if os.path.exists(plm_path) and os.path.isdir(plm_path):
                            self.app_state.plm_directory = plm_path
                            print(f"  Found PLM directory (parent): {plm_path}")
                            break

                # 3. In ALLEN Geschwister-Ordnern des übergeordneten Ordners suchen
                if parent_path:
                    for sibling in os.listdir(parent_path):
                        sibling_path = os.path.join(parent_path, sibling)
                        if os.path.isdir(sibling_path):
                            if not self.app_state.image_directory:
                                for folder in image_folders:
                                    img_path = os.path.join(sibling_path, folder)
                                    if os.path.exists(img_path) and os.path.isdir(img_path):
                                        self.app_state.image_directory = img_path
                                        print(f"  Found Image directory (sibling): {img_path}")
                                        break
                            if not self.app_state.plm_directory:
                                for folder in plm_folders:
                                    plm_path = os.path.join(sibling_path, folder)
                                    if os.path.exists(plm_path) and os.path.isdir(plm_path):
                                        self.app_state.plm_directory = plm_path
                                        print(f"  Found PLM directory (sibling): {plm_path}")
                                        break

                # Alle CSV/STDF Dateien finden - auch in Unterordnern!
                files = []

                # 1. Direkt im Ordner suchen
                for f in os.listdir(path):
                    fpath = os.path.join(path, f)
                    if os.path.isfile(fpath) and f.lower().endswith(('.stdf', '.csv')):
                        files.append(fpath)

                # 2. In Unterordnern suchen (wie Desktop-GUI: STDDatalog, Data, etc.)
                subfolders = ['STDDatalog', 'Data', 'CSV', 'STDF', 'data', 'csv', 'stdf']
                for subfolder in subfolders:
                    subfolder_path = os.path.join(path, subfolder)
                    if os.path.exists(subfolder_path) and os.path.isdir(subfolder_path):
                        for f in os.listdir(subfolder_path):
                            fpath = os.path.join(subfolder_path, f)
                            if os.path.isfile(fpath) and f.lower().endswith(('.stdf', '.csv')):
                                files.append(fpath)

                # 3. Rekursiv alle Unterordner durchsuchen (max 2 Ebenen tief)
                if not files:
                    for root, dirs, filenames in os.walk(path):
                        # Limit depth
                        depth = root.replace(path, '').count(os.sep)
                        if depth > 2:
                            continue
                        for f in filenames:
                            if f.lower().endswith(('.stdf', '.csv')):
                                files.append(os.path.join(root, f))

                if not files:
                    ui.notify(f'Keine CSV/STDF Dateien in {path} gefunden!', type='warning')
                    return

                # LIMIT: Max 20 Dateien um Absturz zu vermeiden
                MAX_FILES = 20
                if len(files) > MAX_FILES:
                    ui.notify(f'⚠️ {len(files)} Dateien gefunden - lade nur die ersten {MAX_FILES}!', type='warning')
                    files = files[:MAX_FILES]

                status_label.text = f'Lade {len(files)} Dateien...'
                ui.notify(f'Lade {len(files)} Dateien...', type='info')

                # ALLE Dateien laden
                loaded_count = 0
                first_wafer = None

                for fpath in files:
                    try:
                        fname = os.path.basename(fpath)
                        ext = Path(fpath).suffix.lower()

                        if ext == '.csv':
                            from .csv_loader import load_csv_file_full
                            result = load_csv_file_full(fpath)

                            if result is not None:
                                wafer_data = WaferData(
                                    filename=fname,
                                    wafer_id=result.wafer_id,
                                    dataframe=result.dataframe,
                                    test_parameters=result.test_parameters,
                                    grouped_parameters=result.grouped_parameters,
                                    test_limits=result.test_limits,
                                )
                                self.app_state.add_wafer(wafer_data)
                                loaded_count += 1

                                # Erste Wafer-Daten merken
                                if first_wafer is None:
                                    first_wafer = result

                        elif ext == '.stdf' and STDF_AVAILABLE:
                            data = parse_stdf_file(fpath, verbose=False)
                            if data:
                                wafer_data = WaferData(
                                    filename=fname,
                                    wafer_id=data.wafer_id or fname,
                                    dataframe=data.dataframe,
                                    test_parameters=data.test_parameters,
                                )
                                self.app_state.add_wafer(wafer_data)
                                loaded_count += 1

                    except Exception as ex:
                        print(f'Fehler bei {fname}: {ex}')

                # UI aktualisieren
                if loaded_count > 0 and first_wafer:
                    # Gruppen in Toolbar laden
                    groups = list(first_wafer.grouped_parameters.keys())
                    self.toolbar1.update_groups(groups)

                    # Parameter in Toolbar laden
                    param_options = []
                    for test_key, display_name in first_wafer.test_parameters.items():
                        param_options.append(f"{test_key}: {display_name}")
                    self.toolbar1.update_params(param_options)

                    # Sidebar aktualisieren
                    wafers = list(self.app_state.loaded_files.keys())
                    self.sidebar.update_wafers(wafers, self.app_state.current_file)

                    # Wafer Tab mit Daten laden
                    if self.tabs['wafer']:
                        self.tabs['wafer'].load_data(
                            df=first_wafer.dataframe,
                            wafer_id=first_wafer.wafer_id,
                            test_params=first_wafer.test_parameters,
                            grouped_params=first_wafer.grouped_parameters,
                        )

                    self._update_ui()
                    ui.notify(f'✅ {loaded_count} Dateien geladen!', type='positive')
                    dialog.close()
                else:
                    ui.notify('Keine Dateien geladen!', type='warning')

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('📥 ALLE LADEN', on_click=load_all_files).classes('bg-green-600 text-white')
                ui.button('Abbrechen', on_click=dialog.close).props('flat')

        dialog.open()

    def _load_binning(self):
        """Binning-Datei laden."""
        ui.notify('Binning file selection...', type='info')

    def _on_group_change(self, group: str):
        """Gruppe geändert - Parameter-Dropdown UND Heatmap aktualisieren."""
        self.app_state.current_group = group
        data = self.app_state.current_data

        if not data:
            return

        # Parameter für diese Gruppe holen
        if group == 'All Groups':
            # Alle Parameter
            param_options = []
            for test_key, display_name in data.test_parameters.items():
                param_options.append(f"{test_key}: {display_name}")
        else:
            # Nur Parameter dieser Gruppe
            param_options = []
            if group in data.grouped_parameters:
                for item in data.grouped_parameters[group]:
                    # item = (test_num, display_name, display_name)
                    test_num = item[0]
                    display_name = item[1] if len(item) > 1 else str(test_num)
                    param_options.append(f"test_{test_num}: {display_name}")

        self.toolbar1.update_params(param_options)

        # Ersten Parameter der Gruppe auswählen und Heatmap aktualisieren
        if param_options:
            self._on_param_change(param_options[0])

    def _on_param_change(self, param: str):
        """Parameter geändert - Heatmap neu zeichnen!"""
        self.app_state.current_param = param
        data = self.app_state.current_data

        if not data or not self.tabs['wafer']:
            return

        # param ist "test_123: Display Name" - extrahiere test_num als Integer
        if ':' in param:
            test_key = param.split(':')[0].strip()  # "test_123"
        else:
            test_key = param

        # Konvertiere test_key zu Integer für DataFrame-Spalte
        if test_key.startswith('test_'):
            try:
                col = int(test_key.replace('test_', ''))
            except ValueError:
                col = test_key
        elif test_key == 'bin':
            col = 'bin'
        else:
            col = test_key

        # Heatmap aktualisieren
        self.tabs['wafer'].update_wafermap(data.dataframe, col, data.wafer_id)

    def _on_view_change(self, view: str):
        """View-Modus geändert (Data/Bin)."""
        self.app_state.view_mode = view
        data = self.app_state.current_data

        if not data or not self.tabs['wafer']:
            return

        # Bei "Bin" → bin-Spalte anzeigen
        if view == 'Bin':
            self.tabs['wafer'].update_wafermap(data.dataframe, 'bin', data.wafer_id)
        else:
            # Bei "Data" → aktuellen Parameter verwenden
            self._on_param_change(self.toolbar1.param_select.value or 'bin')

    def _on_type_change(self, plot_type: str):
        """Plot-Typ geändert (Heatmap/Scatter/Contour)."""
        self.app_state.plot_type = plot_type
        # TODO: Implementieren wenn Scatter/Contour gebraucht wird
        ui.notify(f'Plot-Typ: {plot_type}', type='info')

    def _on_grid_toggle(self, show_grid: bool):
        """Grid ein/aus - Heatmap neu zeichnen!"""
        self.app_state.show_grid = show_grid
        data = self.app_state.current_data

        if data and self.tabs['wafer']:
            # Aktuellen Parameter holen
            param = self.app_state.current_param
            if param:
                # Konvertiere param zu Spaltenname
                if isinstance(param, str) and ':' in param:
                    test_key = param.split(':')[0].strip()
                else:
                    test_key = param

                if isinstance(test_key, str) and test_key.startswith('test_'):
                    try:
                        col = int(test_key.replace('test_', ''))
                    except ValueError:
                        col = test_key
                elif test_key == 'bin':
                    col = 'bin'
                else:
                    col = test_key
            else:
                col = 'bin'

            # Heatmap mit neuem Grid-State neu zeichnen
            self.tabs['wafer'].update_wafermap(data.dataframe, col, data.wafer_id, show_grid=show_grid)

    def _on_zoom_in(self):
        """Zoom In."""
        # TODO: Plotly Zoom implementieren
        ui.notify('Zoom+ (Mausrad im Plot verwenden)', type='info')

    def _on_zoom_out(self):
        """Zoom Out."""
        # TODO: Plotly Zoom implementieren
        ui.notify('Zoom- (Mausrad im Plot verwenden)', type='info')

    def _on_reset(self):
        """Reset View."""
        data = self.app_state.current_data
        if data and self.tabs['wafer']:
            self.tabs['wafer'].update_wafermap(data.dataframe, 'bin', data.wafer_id)
            ui.notify('View zurückgesetzt', type='info')

    def _on_wafer_prev(self, wafer: str):
        """Vorheriger Wafer."""
        self.app_state.current_file = wafer
        self._refresh()

    def _on_wafer_next(self, wafer: str):
        """Nächster Wafer."""
        self.app_state.current_file = wafer
        self._refresh()

    def _on_wafer_select(self, wafer: str):
        """Wafer ausgewählt."""
        self.app_state.current_file = wafer
        self._refresh()

    def _on_wafer_select_all(self, wafers):
        """Alle Wafer auswählen."""
        self.app_state.selected_wafers = wafers

    def _on_wafer_unload_all(self):
        """Alle Wafer entladen."""
        self.app_state.clear_all()
        self._update_ui()

    def _refresh(self):
        """UI aktualisieren."""
        data = self.app_state.current_data
        param = self.app_state.current_param

        if data and param and self.tabs['wafer']:
            self.tabs['wafer'].update_wafermap(data.dataframe, param, data.wafer_id)

    def _update_ui(self):
        """Komplettes UI aktualisieren."""
        # Sidebar
        wafers = list(self.app_state.loaded_files.keys())
        self.sidebar.update_wafers(wafers, self.app_state.current_file)

        # Params
        params = self.app_state.get_all_parameters()
        self.toolbar1.update_params(params)

        # Status
        count = self.app_state.wafer_count
        self.toolbar1.update_status(f'{count} files loaded' if count > 0 else 'No files loaded')

        # Update all tabs
        for tab in self.tabs.values():
            if tab and hasattr(tab, 'update_wafers'):
                tab.update_wafers(wafers)
            if tab and hasattr(tab, 'update_params'):
                tab.update_params(params)


# ============================================================================
# Application Entry Point
# ============================================================================

def main():
    """Anwendung starten."""
    app_instance = DataOctopusApp()

    @ui.page('/')
    def index():
        app_instance.build()

    ui.run(
        title='Data Octopus',
        port=8080,
        reload=True,
        show=True,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
