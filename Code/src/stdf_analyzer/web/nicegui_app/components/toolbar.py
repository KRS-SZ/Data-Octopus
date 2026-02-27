"""
Toolbar Components - Wie in Desktop-App.

Toolbar 1: Format, Load STDF, Project Folder, Group, Param, Refresh, Custom Test, Save Data
Toolbar 2: Load Binning, Show Bins, Grid, Zoom+/-, Reset, Clear Sel, View, Type
"""

from nicegui import ui
from typing import Callable, List, Optional


class Toolbar1:
    """
    Obere Toolbar mit Lade- und Parameter-Controls.

    Layout:
    [Format ▼] [Load STDF] [Project Folder] | [Group ▼] [Param ▼ (breit)] [Refresh] | [Custom Test] [Save Data]
    """

    def __init__(
        self,
        on_load_stdf: Optional[Callable] = None,
        on_project_folder: Optional[Callable] = None,
        on_group_change: Optional[Callable] = None,
        on_param_change: Optional[Callable] = None,
        on_refresh: Optional[Callable] = None,
        on_custom_test: Optional[Callable] = None,
        on_save_data: Optional[Callable] = None,
    ):
        self.on_load_stdf = on_load_stdf
        self.on_project_folder = on_project_folder
        self.on_group_change = on_group_change
        self.on_param_change = on_param_change
        self.on_refresh = on_refresh
        self.on_custom_test = on_custom_test
        self.on_save_data = on_save_data

        # UI Elements (werden in build() erstellt)
        self.format_select = None
        self.group_select = None
        self.param_select = None

    def build(self) -> None:
        """Toolbar UI erstellen."""
        with ui.row().classes('w-full items-center gap-2 px-2 py-1 bg-gray-100 border-b'):
            # Format Dropdown
            self.format_select = ui.select(
                options=['STDF', 'CSV'],
                value='STDF',
                label='Format'
            ).classes('w-24').props('dense outlined')

            # Load STDF Button
            ui.button('Load STDF', on_click=self._handle_load_stdf).classes(
                'bg-blue-500 text-white'
            ).props('dense')

            # Project Folder Button
            ui.button('Project Folder', on_click=self._handle_project_folder).classes(
                'bg-orange-500 text-white'
            ).props('dense')

            # Separator
            ui.separator().props('vertical').classes('h-8')

            # Group Dropdown
            ui.label('Group:').classes('text-sm')
            self.group_select = ui.select(
                options=['All Groups'],
                value='All Groups',
                on_change=self._handle_group_change
            ).classes('w-40').props('dense outlined')

            # Param Dropdown (breit)
            ui.label('Param:').classes('text-sm')
            self.param_select = ui.select(
                options=[],
                on_change=self._handle_param_change
            ).classes('w-96').props('dense outlined')

            # Refresh Button
            ui.button('Refresh', on_click=self._handle_refresh).props('dense outline')

            # Spacer
            ui.space()

            # Custom Test Button (grün)
            ui.button('Custom Test', on_click=self._handle_custom_test).classes(
                'bg-green-600 text-white'
            ).props('dense')

            # Save Data Button (grün)
            ui.button('Save Data', on_click=self._handle_save_data).classes(
                'bg-green-600 text-white'
            ).props('dense')

            # No files loaded Label
            self.status_label = ui.label('No files loaded').classes('text-gray-500 text-sm')

    def update_groups(self, groups: List[str]) -> None:
        """Gruppen-Dropdown aktualisieren."""
        self.group_select.options = ['All Groups'] + groups
        self.group_select.update()

    def update_params(self, params: List[str]) -> None:
        """Parameter-Dropdown aktualisieren."""
        self.param_select.options = params
        if params:
            self.param_select.value = params[0]
        self.param_select.update()

    def update_status(self, text: str) -> None:
        """Status-Label aktualisieren."""
        self.status_label.text = text

    def _handle_load_stdf(self) -> None:
        if self.on_load_stdf:
            self.on_load_stdf()

    def _handle_project_folder(self) -> None:
        if self.on_project_folder:
            self.on_project_folder()

    def _handle_group_change(self, e) -> None:
        if self.on_group_change:
            self.on_group_change(e.value)

    def _handle_param_change(self, e) -> None:
        if self.on_param_change:
            self.on_param_change(e.value)

    def _handle_refresh(self) -> None:
        if self.on_refresh:
            self.on_refresh()

    def _handle_custom_test(self) -> None:
        if self.on_custom_test:
            self.on_custom_test()

    def _handle_save_data(self) -> None:
        if self.on_save_data:
            self.on_save_data()


class Toolbar2:
    """
    Untere Toolbar mit Binning und View-Controls.

    Layout:
    [Load Binning] [Show Bins] Binning: Not loaded | □ Grid [Zoom+] [Zoom-] [Reset] [Clear Sel] | View: [▼] Type: [▼]
    """

    def __init__(
        self,
        on_load_binning: Optional[Callable] = None,
        on_show_bins: Optional[Callable] = None,
        on_grid_toggle: Optional[Callable] = None,
        on_zoom_in: Optional[Callable] = None,
        on_zoom_out: Optional[Callable] = None,
        on_reset: Optional[Callable] = None,
        on_clear_selection: Optional[Callable] = None,
        on_view_change: Optional[Callable] = None,
        on_type_change: Optional[Callable] = None,
    ):
        self.on_load_binning = on_load_binning
        self.on_show_bins = on_show_bins
        self.on_grid_toggle = on_grid_toggle
        self.on_zoom_in = on_zoom_in
        self.on_zoom_out = on_zoom_out
        self.on_reset = on_reset
        self.on_clear_selection = on_clear_selection
        self.on_view_change = on_view_change
        self.on_type_change = on_type_change

        # UI Elements
        self.binning_status = None
        self.grid_checkbox = None
        self.view_select = None
        self.type_select = None

    def build(self) -> None:
        """Toolbar UI erstellen."""
        with ui.row().classes('w-full items-center gap-2 px-2 py-1 bg-gray-50 border-b'):
            # Load Binning Button (blau)
            ui.button('Load Binning', on_click=self._handle_load_binning).classes(
                'bg-blue-600 text-white'
            ).props('dense')

            # Show Bins Button (blau)
            ui.button('Show Bins', on_click=self._handle_show_bins).classes(
                'bg-blue-600 text-white'
            ).props('dense')

            # Binning Status
            self.binning_status = ui.label('Binning: Not loaded').classes('text-gray-500 text-sm')

            # Separator
            ui.separator().props('vertical').classes('h-8')

            # Grid Checkbox
            self.grid_checkbox = ui.checkbox('Grid', on_change=self._handle_grid_toggle).props('dense')

            # Zoom Buttons
            ui.button('Zoom+', on_click=self._handle_zoom_in).props('dense outline')
            ui.button('Zoom-', on_click=self._handle_zoom_out).props('dense outline')
            ui.button('Reset', on_click=self._handle_reset).props('dense outline')
            ui.button('Clear Sel', on_click=self._handle_clear_selection).props('dense outline')

            # Separator
            ui.separator().props('vertical').classes('h-8')

            # View Dropdown
            ui.label('View:').classes('text-sm')
            self.view_select = ui.select(
                options=['Data', 'Bin'],
                value='Data',
                on_change=self._handle_view_change
            ).classes('w-24').props('dense outlined')

            # Type Dropdown
            ui.label('Type:').classes('text-sm')
            self.type_select = ui.select(
                options=['Heatmap', 'Scatter', 'Contour'],
                value='Heatmap',
                on_change=self._handle_type_change
            ).classes('w-28').props('dense outlined')

    def set_binning_status(self, loaded: bool, name: str = "") -> None:
        """Binning-Status aktualisieren."""
        if loaded:
            self.binning_status.text = f'Binning: {name}'
            self.binning_status.classes(remove='text-gray-500', add='text-green-600')
        else:
            self.binning_status.text = 'Binning: Not loaded'
            self.binning_status.classes(remove='text-green-600', add='text-gray-500')

    def _handle_load_binning(self) -> None:
        if self.on_load_binning:
            self.on_load_binning()

    def _handle_show_bins(self) -> None:
        if self.on_show_bins:
            self.on_show_bins()

    def _handle_grid_toggle(self, e) -> None:
        if self.on_grid_toggle:
            self.on_grid_toggle(e.value)

    def _handle_zoom_in(self) -> None:
        if self.on_zoom_in:
            self.on_zoom_in()

    def _handle_zoom_out(self) -> None:
        if self.on_zoom_out:
            self.on_zoom_out()

    def _handle_reset(self) -> None:
        if self.on_reset:
            self.on_reset()

    def _handle_clear_selection(self) -> None:
        if self.on_clear_selection:
            self.on_clear_selection()

    def _handle_view_change(self, e) -> None:
        if self.on_view_change:
            self.on_view_change(e.value)

    def _handle_type_change(self, e) -> None:
        if self.on_type_change:
            self.on_type_change(e.value)
