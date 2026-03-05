"""
Application State Management for NiceGUI Web App.

Zentrale State-Verwaltung wie in der Desktop-App.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class WaferData:
    """Container für geladene Wafer-Daten."""
    filename: str
    wafer_id: str
    dataframe: pd.DataFrame
    test_parameters: Dict[str, str] = field(default_factory=dict)
    test_limits: Dict[Any, Any] = field(default_factory=dict)
    grouped_parameters: Dict[str, List[str]] = field(default_factory=dict)


class AppState:
    """
    Globaler Application State.

    Entspricht den globalen Variablen in main.py:
    - current_stdf_data
    - multiple_stdf_data
    - grouped_parameters
    - test_limits
    - binning_lookup
    """

    def __init__(self):
        # Geladene Dateien
        self.loaded_files: Dict[str, WaferData] = {}
        self.current_file: Optional[str] = None

        # Binning
        self.binning_lookup = None
        self.binning_loaded = False

        # UI State
        self.current_main_tab: str = "wafer"
        self.current_sub_tab: str = "heatmap"

        # Wafer Selection
        self.selected_wafers: List[str] = []

        # Parameter Selection
        self.current_group: str = "All Groups"
        self.current_param: str = ""

        # View Settings
        self.view_mode: str = "Data"  # Data, Bin
        self.plot_type: str = "Heatmap"  # Heatmap, Scatter
        self.show_grid: bool = False

        # Ordner-Pfade (wie Desktop: die_image_directory, plm_file_directory)
        self.project_folder: Optional[str] = None
        self.image_directory: Optional[str] = None
        self.plm_directory: Optional[str] = None

        # Aktuell ausgewählte Die
        self.selected_die: Optional[tuple] = None

    @property
    def current_data(self) -> Optional[WaferData]:
        """Aktuell ausgewählte Wafer-Daten."""
        if self.current_file and self.current_file in self.loaded_files:
            return self.loaded_files[self.current_file]
        return None

    @property
    def wafer_count(self) -> int:
        """Anzahl geladener Wafer."""
        return len(self.loaded_files)

    def add_wafer(self, wafer: WaferData) -> None:
        """Wafer hinzufügen."""
        self.loaded_files[wafer.filename] = wafer
        if self.current_file is None:
            self.current_file = wafer.filename

    def remove_wafer(self, filename: str) -> None:
        """Wafer entfernen."""
        if filename in self.loaded_files:
            del self.loaded_files[filename]
            if self.current_file == filename:
                self.current_file = next(iter(self.loaded_files), None)

    def clear_all(self) -> None:
        """Alle Wafer entfernen."""
        self.loaded_files.clear()
        self.current_file = None
        self.selected_wafers.clear()

    def get_all_parameters(self) -> List[str]:
        """Alle Parameter aus allen geladenen Wafern."""
        params = set()
        for wafer in self.loaded_files.values():
            params.update(wafer.test_parameters.keys())
        return sorted(params)

    def get_common_parameters(self) -> List[str]:
        """Parameter die in ALLEN Wafern vorhanden sind."""
        if not self.loaded_files:
            return []
        param_sets = [set(w.test_parameters.keys()) for w in self.loaded_files.values()]
        common = param_sets[0].intersection(*param_sets[1:]) if len(param_sets) > 1 else param_sets[0]
        return sorted(common)


# Globale State-Instanz
app_state = AppState()
