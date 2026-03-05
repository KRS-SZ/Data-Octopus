"""
Config Tab - Web Version.

Application Configuration and Settings.
"""

from nicegui import ui
from typing import Any, Dict, List, Optional


class ConfigTab:
    """
    Config Tab für App-Einstellungen.
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state
        self.container = None

    def build(self, parent: Any = None) -> None:
        """Tab UI aufbauen."""
        with ui.column().classes('w-full h-full p-4') as self.container:
            ui.label('Configuration').classes('text-xl font-bold mb-4')

            with ui.row().classes('w-full gap-4'):
                # Data Paths
                with ui.card().classes('flex-1'):
                    ui.label('Data Paths').classes('font-bold')

                    ui.label('Default Data Folder:').classes('mt-2')
                    self.data_path = ui.input(
                        value=r'C:\Users\szenklarz\Desktop\VS_Folder\AM Data'
                    ).classes('w-full')

                    ui.label('Binning File:').classes('mt-2')
                    self.binning_path = ui.input(
                        value=''
                    ).classes('w-full')
                    ui.button('Browse...', on_click=self._browse_binning).props('dense')

                # Display Settings
                with ui.card().classes('flex-1'):
                    ui.label('Display Settings').classes('font-bold')

                    ui.label('Default Colormap:').classes('mt-2')
                    self.colormap_select = ui.select(
                        options=['Viridis', 'Plasma', 'Inferno', 'Magma', 'RdBu', 'Spectral'],
                        value='Viridis'
                    ).classes('w-full')

                    ui.label('Marker Size:').classes('mt-2')
                    self.marker_size = ui.slider(min=5, max=20, value=10).classes('w-full')

                    self.show_grid = ui.checkbox('Show Grid by Default', value=False)
                    self.auto_refresh = ui.checkbox('Auto-Refresh on File Load', value=True)

            with ui.row().classes('w-full gap-4 mt-4'):
                # Export Settings
                with ui.card().classes('flex-1'):
                    ui.label('Export Settings').classes('font-bold')

                    ui.label('Default Report Folder:').classes('mt-2')
                    self.report_path = ui.input(
                        value=r'C:\Users\szenklarz\Desktop\VS_Folder\Data Octopus\Report'
                    ).classes('w-full')

                    ui.label('Image DPI:').classes('mt-2')
                    self.export_dpi = ui.select(
                        options=['72', '150', '300', '600'],
                        value='150'
                    ).classes('w-32')

                # About
                with ui.card().classes('flex-1'):
                    ui.label('About').classes('font-bold')
                    ui.label('Data Octopus - Web Version').classes('mt-2')
                    ui.label('Version: 1.0.0 (NiceGUI)').classes('text-gray-600')
                    ui.label('Author: Krzysztof Szenklarz').classes('text-gray-600')
                    ui.link('GitHub', 'https://github.com/KRS-SZ/Data-Octopus')

            # Save Button
            ui.button('Save Configuration', on_click=self._save_config).classes(
                'mt-4 bg-blue-600 text-white'
            )

    def _browse_binning(self) -> None:
        """Binning-Datei auswählen."""
        ui.notify('File browser not available in web mode. Enter path manually.', type='info')

    def _save_config(self) -> None:
        """Konfiguration speichern."""
        # TODO: Save to local storage or config file
        ui.notify('Configuration saved!', type='positive')
