"""
Wafer Tab - Web Version.

IMPORTIERT alle Logik aus den Core-Modulen:
- core/data_loader.py      → load_csv_file(), detect_test_parameters(), group_parameters()
- core/wafermap_utils.py   → calculate_die_dimensions(), get_wafer_bounds()
- core/statistics_utils.py → calculate_basic_stats(), calculate_yield()
- core/binning.py          → BIN_COLORS
- core/parameter_utils.py  → simplify_param_name(), extract_group_from_column()

VERWENDET PlotlyWafermapRenderer für die Plotly-Visualisierung.
Diese Komponente kann von anderen Tabs wiederverwendet werden!
"""

from nicegui import ui
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ============================================================================
# CORE IMPORTS
# ============================================================================

from src.stdf_analyzer.core.data_loader import (
    detect_test_parameters,
    group_parameters,
)
from src.stdf_analyzer.core.statistics_utils import (
    calculate_basic_stats,
    format_stat_value,
)

# Wafermap Renderer Funktionen
from ..components.wafermap_renderer import create_wafermap_figure, get_statistics


class WaferTab:
    """
    Wafer Tab mit Sub-Tabs (Heatmap, Charac.-Curve, Statistics).
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state

        # UI Elements
        self.container = None
        self.sub_tab_buttons: Dict[str, ui.button] = {}
        self.sub_tab_contents: Dict[str, Any] = {}
        self.current_sub_tab = "heatmap"

        # Plot elements
        self.wafermap_plot = None
        self.stats_table = None
        self.charac_plot = None

        # Parameter Selection (MODULAR - kann von anderen Tabs verwendet werden!)
        self.group_select = None
        self.param_select = None

        # Test Limits
        self.lo_limit_input = None
        self.hi_limit_input = None

        # Statistik Labels
        self.stat_min = None
        self.stat_max = None
        self.stat_mean = None
        self.stat_median = None
        self.stat_dies = None
        self.stat_yield = None

        # Current data cache
        self._current_df: Optional[pd.DataFrame] = None
        self._current_param: Optional[str] = None
        self._current_wafer_id: Optional[str] = None
        self._grouped_params: Dict[str, List] = {}
        self._test_params: Dict[str, str] = {}
        self._param_mapping: Dict[str, str] = {}  # display_name -> column_name

    def build(self, parent: Any = None) -> None:
        """Tab UI aufbauen."""
        with ui.column().classes('w-full h-full') as self.container:
            # Sub-Tab Buttons
            self._build_sub_tabs()

            # Main Content Area - Horizontal Layout
            with ui.row().classes('w-full flex-1 gap-2 p-2'):
                # LINKS: Images/PLM + Test Limits
                self._build_left_panel()

                # RECHTS: Wafermap
                self._build_wafermap_panel()

            # Sub-Tab Contents (hidden by default)
            self._build_charac_curve_content()
            self._build_statistics_content()

            # Initial: nur Heatmap sichtbar
            self._switch_sub_tab("heatmap")

    def _build_sub_tabs(self) -> None:
        """Sub-Tab Buttons erstellen."""
        with ui.row().classes('gap-0 bg-gray-200 border-b w-full'):
            for tab_id, label in [("heatmap", "Heatmap"),
                                   ("charac_curve", "Charac.-Curve"),
                                   ("statistics", "Statistics")]:
                btn = ui.button(label, on_click=lambda t=tab_id: self._switch_sub_tab(t))
                btn.classes('rounded-none px-4 py-2')
                if tab_id == "heatmap":
                    btn.classes(add='bg-white font-bold border-t-2 border-blue-500')
                else:
                    btn.classes(add='bg-gray-100 hover:bg-gray-200')
                btn.props('flat dense')
                self.sub_tab_buttons[tab_id] = btn

    def _build_left_panel(self) -> None:
        """Linkes Panel: Images/PLM + Test Limits."""
        with ui.column().classes('w-80 gap-2'):
            # Die Images & PLM Card
            with ui.card().classes('w-full'):
                ui.label('Die Images & PLM').classes('font-bold text-sm border-b pb-1')

                with ui.row().classes('w-full items-center gap-2 mt-2'):
                    ui.icon('image', size='16px').classes('text-gray-500')
                    ui.label('Images').classes('text-sm flex-1')
                    self.image_type_select = ui.select(options=['All'], value='All').classes('w-20').props('dense outlined')

                # Image Anzahl + Liste (wird bei Die-Klick befüllt)
                self.image_count_label = ui.label('').classes('text-xs text-gray-500')
                self.image_container = ui.column().classes('h-32 overflow-auto bg-gray-50 border rounded p-1')
                with self.image_container:
                    ui.label('Klicke auf eine Die...').classes('text-xs text-gray-400')

                with ui.row().classes('w-full items-center gap-2 mt-2'):
                    ui.icon('insert_chart', size='16px').classes('text-gray-500')
                    ui.label('PLM Files').classes('text-sm flex-1')
                    self.plm_type_select = ui.select(options=['All'], value='All').classes('w-20').props('dense outlined')

                # PLM Anzahl + Container für Heatmaps (wird bei Die-Klick befüllt)
                self.plm_count_label = ui.label('').classes('text-xs text-gray-500')
                self.plm_container = ui.column().classes('max-h-96 overflow-auto bg-gray-50 border rounded p-1')
                with self.plm_container:
                    ui.label('Klicke auf eine Die...').classes('text-xs text-gray-400')

            # Test Limits Card (wie Desktop!)
            with ui.card().classes('w-full'):
                ui.label('Test Limits').classes('font-bold text-sm border-b pb-1')

                with ui.column().classes('gap-2 mt-2'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label('Lo:').classes('w-8 text-sm')
                        self.lo_limit_input = ui.input(placeholder='').classes('flex-1').props('dense outlined')

                    with ui.row().classes('items-center gap-2'):
                        ui.label('Hi:').classes('w-8 text-sm')
                        self.hi_limit_input = ui.input(placeholder='').classes('flex-1').props('dense outlined')

                    ui.button('Apply', on_click=self._apply_limits).classes(
                        'bg-blue-500 text-white w-full'
                    ).props('dense')

            # Yield Card (NEU - wie Desktop!)
            with ui.card().classes('w-full'):
                ui.label('Yield').classes('font-bold text-sm border-b pb-1')
                self.stat_yield = ui.label('Pass: - | Fail: -').classes('text-sm mt-1')

    def _build_wafermap_panel(self) -> None:
        """Rechtes Panel: Wafermap + Statistik-Box."""
        with ui.column().classes('flex-1 relative') as content:
            self.sub_tab_contents["heatmap"] = content

            # Statistik-Box ÜBER der Wafermap (wie Desktop!)
            with ui.card().classes('absolute z-10 ml-2 mt-2 bg-white/95 shadow-lg'):
                with ui.column().classes('gap-0 p-2'):
                    self.stat_min = ui.label('Min: -').classes('text-xs')
                    self.stat_max = ui.label('Max: -').classes('text-xs')
                    self.stat_mean = ui.label('Mean: -').classes('text-xs')
                    self.stat_median = ui.label('Median: -').classes('text-xs')
                    self.stat_dies = ui.label('Dies: -').classes('text-xs font-bold')

            # Wafermap Plot (GROSS - wie Desktop!)
            self.wafermap_plot = ui.plotly({}).classes('w-full').style('height: 600px')

            # Die-Klick Event Handler
            self.wafermap_plot.on('plotly_click', self._on_die_click)

            # Titel unter Wafermap
            self.wafermap_title = ui.label('').classes('text-sm text-gray-600 text-center w-full')

            # Die-Info Panel (wird bei Klick befüllt)
            with ui.card().classes('w-full mt-2') as self.die_info_card:
                ui.label('Selected Die').classes('font-bold text-sm border-b pb-1')
                self.die_info_content = ui.column().classes('gap-1 p-2')
                with self.die_info_content:
                    self.die_coord_label = ui.label('Coordinates: -').classes('text-sm')
                    self.die_bin_label = ui.label('Bin: -').classes('text-sm')
                    self.die_value_label = ui.label('Value: -').classes('text-sm font-bold')

            # Initial versteckt
            self.die_info_card.classes(add='hidden')

    def _on_die_click(self, e):
        """Handler für Die-Klick - zeigt Messwerte, Images und PLMs an."""
        import os
        import re
        try:
            if not e.args or 'points' not in e.args:
                return

            points = e.args['points']
            if not points:
                return

            # Erste geklickte Die
            point = points[0]
            x = int(point.get('x', 0))
            y = int(point.get('y', 0))
            z = point.get('z')

            if z is None or np.isnan(z):
                return

            # Die-Info anzeigen
            self.die_info_card.classes(remove='hidden')
            self.die_coord_label.text = f'Coordinates: X={x}, Y={y}'

            # Bin-Wert?
            if self._current_param == 'bin' or str(self._current_param).lower() in ['bin', 'sbin', 'hbin']:
                self.die_bin_label.text = f'Bin: {int(z)}'
                self.die_value_label.text = ''
            else:
                # Parameter-Wert
                display_name = str(self._current_param)
                if isinstance(self._current_param, int) and f"test_{self._current_param}" in self._test_params:
                    display_name = self._test_params[f"test_{self._current_param}"]
                self.die_value_label.text = f'{display_name}: {z:.6g}'

                # Auch Bin anzeigen wenn vorhanden
                if self._current_df is not None and 'bin' in self._current_df.columns:
                    die_row = self._current_df[(self._current_df['x'] == x) & (self._current_df['y'] == y)]
                    if len(die_row) > 0:
                        bin_val = die_row['bin'].values[0]
                        self.die_bin_label.text = f'Bin: {int(bin_val)}'

            # Speichere ausgewählte Die
            self._selected_die = (x, y)

            # ================================================================
            # Images für diese Die laden (wie Desktop: display_die_images)
            # ================================================================
            self.image_list.clear()
            image_dir = self.app_state.image_directory
            if image_dir and os.path.exists(image_dir):
                image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff')
                found_images = []

                for filename in os.listdir(image_dir):
                    if filename.lower().endswith(image_extensions):
                        # Pattern: X19_Y46, X19-Y46, _X19_Y46_
                        match = re.search(r'[_\-]?X(\d+)[_\-]Y(\d+)', filename, re.IGNORECASE)
                        if match:
                            img_x = int(match.group(1))
                            img_y = int(match.group(2))
                            if img_x == x and img_y == y:
                                found_images.append(filename)

                with self.image_list:
                    if found_images:
                        for img in found_images[:5]:  # Max 5 anzeigen
                            ui.label(img).classes('text-xs truncate cursor-pointer hover:text-blue-600')
                    else:
                        ui.label(f'Keine Images für X{x}_Y{y}').classes('text-xs text-gray-400')
            else:
                with self.image_list:
                    ui.label('Kein Image-Ordner').classes('text-xs text-gray-400')

            # ================================================================
            # PLM Files für diese Die laden (wie Desktop: display_plm_files)
            # ================================================================
            self.plm_list.clear()
            plm_dir = self.app_state.plm_directory
            if plm_dir and os.path.exists(plm_dir):
                plm_extensions = ('.plm', '.txt', '.csv', '.dat')
                found_plms = []

                for filename in os.listdir(plm_dir):
                    if filename.lower().endswith(plm_extensions):
                        # Pattern: X19_Y46, X19-Y46, _X19_Y46_
                        match = re.search(r'[_\-]?X(\d+)[_\-]Y(\d+)', filename, re.IGNORECASE)
                        if match:
                            plm_x = int(match.group(1))
                            plm_y = int(match.group(2))
                            if plm_x == x and plm_y == y:
                                found_plms.append(filename)

                with self.plm_list:
                    if found_plms:
                        for plm in found_plms[:5]:  # Max 5 anzeigen
                            ui.label(plm).classes('text-xs truncate cursor-pointer hover:text-blue-600')
                    else:
                        ui.label(f'Keine PLM für X{x}_Y{y}').classes('text-xs text-gray-400')
            else:
                with self.plm_list:
                    ui.label('Kein PLM-Ordner').classes('text-xs text-gray-400')

            print(f"Die clicked: X={x}, Y={y}, Value={z}")

        except Exception as ex:
            print(f"Error in die click handler: {ex}")
            import traceback
            traceback.print_exc()

    def _build_charac_curve_content(self) -> None:
        """Charac.-Curve Sub-Tab Content."""
        with ui.column().classes('w-full hidden p-2') as content:
            self.sub_tab_contents["charac_curve"] = content

            with ui.row().classes('gap-4 items-center mb-2'):
                ui.label('X:').classes('font-bold')
                self.charac_x_select = ui.select(options=[], label='X Parameter').classes('w-64').props('dense outlined')
                ui.label('Y:').classes('font-bold')
                self.charac_y_select = ui.select(options=[], label='Y Parameter').classes('w-64').props('dense outlined')
                ui.button('Plot', on_click=self._plot_charac_curve).classes('bg-blue-500 text-white')

            self.charac_plot = ui.plotly({}).classes('w-full').style('height: 550px')

    def _build_statistics_content(self) -> None:
        """Statistics Sub-Tab Content."""
        with ui.column().classes('w-full hidden p-2') as content:
            self.sub_tab_contents["statistics"] = content

            self.stats_table = ui.table(
                columns=[
                    {'name': 'param', 'label': 'Parameter', 'field': 'param', 'align': 'left'},
                    {'name': 'count', 'label': 'Count', 'field': 'count', 'align': 'right'},
                    {'name': 'mean', 'label': 'Mean', 'field': 'mean', 'align': 'right'},
                    {'name': 'std', 'label': 'Std', 'field': 'std', 'align': 'right'},
                    {'name': 'min', 'label': 'Min', 'field': 'min', 'align': 'right'},
                    {'name': 'max', 'label': 'Max', 'field': 'max', 'align': 'right'},
                    {'name': 'yield_pct', 'label': 'Yield %', 'field': 'yield_pct', 'align': 'right'},
                ],
                rows=[],
                row_key='param'
            ).classes('w-full').props('dense')

    def _switch_sub_tab(self, tab_id: str) -> None:
        """Sub-Tab wechseln."""
        self.current_sub_tab = tab_id

        for tid, btn in self.sub_tab_buttons.items():
            if tid == tab_id:
                btn.classes(remove='bg-gray-100 hover:bg-gray-200',
                           add='bg-white font-bold border-t-2 border-blue-500')
            else:
                btn.classes(remove='bg-white font-bold border-t-2 border-blue-500',
                           add='bg-gray-100 hover:bg-gray-200')

        for tid, content in self.sub_tab_contents.items():
            if tid == tab_id:
                content.classes(remove='hidden')
            else:
                content.classes(add='hidden')

    def _apply_limits(self) -> None:
        """Test Limits anwenden und Wafermap neu zeichnen."""
        if self._current_df is not None and self._current_param:
            self.update_wafermap(self._current_df, self._current_param, self._current_wafer_id)

    def _plot_charac_curve(self) -> None:
        """Characteristic Curve plotten. VERWENDET PlotlyWafermapRenderer!"""
        if self._current_df is None:
            return

        x_param = self.charac_x_select.value
        y_param = self.charac_y_select.value

        if not x_param or not y_param:
            return

        # Hole echten Spaltennamen aus Mapping
        x_col = self._param_mapping.get(x_param, x_param)
        y_col = self._param_mapping.get(y_param, y_param)

        if x_col not in self._current_df.columns or y_col not in self._current_df.columns:
            return

        # VERWENDET PlotlyWafermapRenderer!
        fig = self.renderer.create_scatter(self._current_df, x_col, y_col, height=550)
        self.charac_plot.update_figure(fig)

    # ========================================================================
    # PUBLIC METHODS - Werden von main.py aufgerufen
    # ========================================================================

    def load_data(self, df: pd.DataFrame, wafer_id: str = "",
                  test_params: Optional[Dict] = None,
                  grouped_params: Optional[Dict] = None,
                  test_limits: Optional[Dict] = None) -> None:
        """
        Daten in den Tab laden.
        """
        self._current_df = df
        self._current_wafer_id = wafer_id

        # Test-Parameter
        if test_params is None:
            self._test_params = detect_test_parameters(df)
        else:
            self._test_params = test_params

        # Gruppierte Parameter
        if grouped_params is None:
            self._grouped_params = group_parameters(self._test_params)
        else:
            self._grouped_params = grouped_params

        # Mapping erstellen: test_key -> column_name (Integer!)
        # test_params Format: {"test_1": "Display Name", "test_2": "..."}
        # grouped_params Format: {"Group": [(1, "name", "name"), (2, "name", "name")]}
        # Die Spalten im DataFrame sind INTEGER (1, 2, 3, ...)
        self._test_key_to_col = {}
        for test_key in self._test_params.keys():
            # test_key ist "test_1" -> extrahiere 1 als Integer
            try:
                col_num = int(test_key.replace("test_", ""))
                if col_num in df.columns:
                    self._test_key_to_col[test_key] = col_num
            except ValueError:
                pass

        # Parameter für Charac-Curve (zeige test_keys)
        test_keys = list(self._test_params.keys())
        self.charac_x_select.options = test_keys
        self.charac_y_select.options = test_keys
        if test_keys:
            self.charac_x_select.value = test_keys[0]
            self.charac_y_select.value = test_keys[1] if len(test_keys) > 1 else test_keys[0]

        # Ersten Parameter anzeigen - verwende "bin" als Default
        if 'bin' in df.columns:
            self._current_param = 'bin'
            self.update_wafermap(df, 'bin', wafer_id)
        elif self._test_key_to_col:
            first_key = list(self._test_key_to_col.keys())[0]
            first_col = self._test_key_to_col[first_key]
            self._current_param = first_col
            self.update_wafermap(df, first_col, wafer_id)

    def update_wafermap(self, df: pd.DataFrame, param, wafer_id: str = "", show_grid: bool = False) -> None:
        """
        Wafermap aktualisieren.
        param kann String ('bin') oder Integer (Spaltennummer) sein!
        show_grid: Grid-Linien anzeigen
        """
        if df is None:
            return

        # Wenn param ein test_key ist (z.B. "test_1"), konvertiere zu Integer
        if isinstance(param, str) and param.startswith("test_"):
            try:
                param = int(param.replace("test_", ""))
            except ValueError:
                pass

        if param not in df.columns:
            print(f"⚠️ Parameter '{param}' nicht in Spalten: {list(df.columns)[:10]}...")
            return

        # Cache aktualisieren
        self._current_df = df
        self._current_param = param
        self._current_wafer_id = wafer_id

        # Statistiken berechnen - importiere direkt aus wafermap_renderer
        from ..components.wafermap_renderer import get_statistics, create_wafermap_figure

        stats = get_statistics(df, param)
        if stats['count'] > 0:
            self.stat_min.text = f"Min: {stats['min']:.4g}"
            self.stat_max.text = f"Max: {stats['max']:.4g}"
            self.stat_mean.text = f"Mean: {stats['mean']:.4g}"
            self.stat_median.text = f"Median: {stats['median']:.4g}"
            self.stat_dies.text = f"Dies: {stats['count']}"
        else:
            self.stat_min.text = "Min: -"
            self.stat_max.text = "Max: -"
            self.stat_mean.text = "Mean: -"
            self.stat_median.text = "Median: -"
            self.stat_dies.text = "Dies: -"

        # Plotly Figure erstellen - DIREKT wie main_v5.py!
        fig = create_wafermap_figure(
            df=df,
            param=param,
            wafer_id=wafer_id,
            height=600,
        )

        self.wafermap_plot.update_figure(fig)

        # Titel aktualisieren
        display_name = str(param)
        if isinstance(param, int) and f"test_{param}" in self._test_params:
            display_name = self._test_params[f"test_{param}"]
        self.wafermap_title.text = f"Heatmap: {display_name} | Wafer: {wafer_id or 'N/A'}"

    def update_statistics_table(self) -> None:
        """Statistik-Tabelle aktualisieren."""
        if self._current_df is None:
            return

        rows = []
        for col, display_name in self._test_params.items():
            if col not in self._current_df.columns:
                continue

            # VERWENDET Core-Funktion!
            values = pd.to_numeric(self._current_df[col], errors='coerce').dropna().values
            if len(values) == 0:
                continue

            stats = calculate_basic_stats(values)

            rows.append({
                'param': display_name,
                'count': stats['count'],
                'mean': format_stat_value(stats['mean'], 4),
                'std': format_stat_value(stats['std'], 4),
                'min': format_stat_value(stats['min'], 4),
                'max': format_stat_value(stats['max'], 4),
                'yield_pct': '-',  # Braucht Limits
            })

        self.stats_table.rows = rows
        self.stats_table.update()

    def get_current_param(self) -> Optional[str]:
        """Gibt aktuellen Parameter zurück."""
        return self._current_param

    def get_current_df(self) -> Optional[pd.DataFrame]:
        """Gibt aktuellen DataFrame zurück."""
        return self._current_df

    def get_grouped_params(self) -> Dict[str, List]:
        """Gibt gruppierte Parameter zurück (für andere Tabs!)."""
        return self._grouped_params

    def get_test_params(self) -> Dict[str, str]:
        """Gibt Test-Parameter zurück (für andere Tabs!)."""
        return self._test_params
