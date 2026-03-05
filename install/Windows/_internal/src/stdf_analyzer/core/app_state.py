"""
Application State Module for Data Octopus

Contains the AppState class that manages the application's global state.
This centralizes all data variables that were previously scattered as global variables.

Usage:
    from src.stdf_analyzer.core.app_state import app_state

    # Access data
    app_state.current_stdf_data
    app_state.grouped_parameters

    # Modify data
    app_state.current_stdf_data = new_data
    app_state.reset()  # Clear all data
"""

from typing import Optional, Dict, List, Any, Set
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class WaferConfig:
    """Configuration for a single wafer (from WCR record)."""
    notch_orientation: Optional[str] = None  # 'U', 'D', 'L', 'R' or None
    wafer_size: Optional[float] = None       # Wafer diameter in mm
    die_width: Optional[float] = None
    die_height: Optional[float] = None
    pos_x: Optional[str] = None              # Positive X direction
    pos_y: Optional[str] = None              # Positive Y direction


class AppState:
    """
    Central application state manager.

    Replaces the 70+ global variables that were previously scattered
    throughout main_v3.py. This makes the code more maintainable and testable.

    Categories of state:
    - Current wafer data (single wafer view)
    - Multiple wafer data (multi-wafer view)
    - Test parameters and limits
    - Column detection (HardBin, SoftBin)
    - PLM (Pixel Light Measurement) state
    - GRR (Gage R&R) state
    - Custom tests and groups
    """

    def __init__(self):
        """Initialize all state variables to their default values."""
        self.reset()

    def reset(self):
        """Reset all state to initial values. Call when loading new data."""
        # ============================================================
        # CURRENT WAFER DATA (Single Wafer View)
        # ============================================================
        self.current_stdf_data: Optional[pd.DataFrame] = None
        self.current_wafer_id: Optional[str] = None
        self.current_wafer_config = WaferConfig()

        # ============================================================
        # MULTIPLE WAFER DATA (Multi-Wafer View)
        # ============================================================
        self.multiple_stdf_data: List[pd.DataFrame] = []
        self.multiple_wafer_ids: List[str] = []

        # ============================================================
        # TEST PARAMETERS AND LIMITS
        # ============================================================
        self.test_parameters: Dict[str, str] = {}  # test_key -> test_name
        self.grouped_parameters: Dict[str, List] = {}  # group_name -> list of (test_num, short_name, full_name)
        self.test_limits: Dict[int, Dict] = {}  # test_num -> {'lo_limit': value, 'hi_limit': value, 'units': str}

        # ============================================================
        # COLUMN DETECTION
        # ============================================================
        self.hardbin_column: Optional[str] = None  # Column name for HardBin (detected from CSV)
        self.softbin_column: Optional[str] = None  # Column name for SoftBin (detected from CSV)

        # ============================================================
        # CUSTOM TESTS
        # ============================================================
        self.custom_tests: Dict[str, Any] = {}  # User-defined custom test configurations

        # ============================================================
        # PLM (Pixel Light Measurement) STATE
        # ============================================================
        self.plm_file_directory: Optional[str] = None
        self.plm_pixel_grr_results: Dict = {}  # Key: (die_x, die_y, plm_type), Value: GRR results
        self.plm_selected_areas: List[Dict] = []  # List of {'x', 'y', 'w', 'h', 'rect_ids'}
        self.plm_region_colors: List[str] = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]

        # ============================================================
        # GRR (Gage R&R) STATE
        # ============================================================
        self.grr_selected_dies: Set = set()  # Selected dies in wafermap

        # ============================================================
        # DIE IMAGE DIRECTORY
        # ============================================================
        self.die_image_directory: Optional[str] = None

    def has_data(self) -> bool:
        """Check if any wafer data is loaded."""
        return self.current_stdf_data is not None or len(self.multiple_stdf_data) > 0

    def get_wafer_count(self) -> int:
        """Get the number of loaded wafers."""
        return len(self.multiple_stdf_data) if self.multiple_stdf_data else (1 if self.current_stdf_data is not None else 0)

    def clear_current(self):
        """Clear only the current wafer data (keep multi-wafer data)."""
        self.current_stdf_data = None
        self.current_wafer_id = None
        self.current_wafer_config = WaferConfig()

    def clear_multiple(self):
        """Clear only the multiple wafer data (keep current wafer)."""
        self.multiple_stdf_data = []
        self.multiple_wafer_ids = []

    def set_wafer_config(self, **kwargs):
        """Set wafer configuration values."""
        for key, value in kwargs.items():
            if hasattr(self.current_wafer_config, key):
                setattr(self.current_wafer_config, key, value)

    def get_wafer_config_dict(self) -> Dict:
        """Get wafer configuration as dictionary (for backward compatibility)."""
        return {
            'notch_orientation': self.current_wafer_config.notch_orientation,
            'wafer_size': self.current_wafer_config.wafer_size,
            'die_width': self.current_wafer_config.die_width,
            'die_height': self.current_wafer_config.die_height,
            'pos_x': self.current_wafer_config.pos_x,
            'pos_y': self.current_wafer_config.pos_y,
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================
# This is the single instance that should be used throughout the application.
# Import it as: from src.stdf_analyzer.core.app_state import app_state
app_state = AppState()
