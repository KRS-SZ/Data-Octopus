"""
CSV Loader für NiceGUI Web App.

VERWENDET DIE CORE-FUNKTIONEN aus parameter_utils.py!
- simplify_param_name() → Parameter-Namen formatieren
- extract_group_from_column() → Gruppen erkennen
"""

import os
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# CORE IMPORTS - NICHT DUPLIZIEREN!
from src.stdf_analyzer.core.parameter_utils import (
    simplify_param_name,
    extract_group_from_column,
    convert_am_data_column_name,
)


@dataclass
class LoadedWaferData:
    """Container für geladene Wafer-Daten - wie in main_v5.py"""
    dataframe: pd.DataFrame
    wafer_id: str
    test_parameters: Dict[str, str]  # test_key -> display_name
    grouped_parameters: Dict[str, List]  # group -> [(test_num, display_name, display_name)]
    test_limits: Dict[int, Dict] = field(default_factory=dict)
    notch_orientation: str = 'D'


def load_csv_file_full(csv_path: str) -> Optional[LoadedWaferData]:
    """
    CSV-Datei laden - EXAKT wie load_csv_wafermap_file() aus main_v5.py!

    Args:
        csv_path: Pfad zur CSV-Datei

    Returns:
        LoadedWaferData oder None bei Fehler
    """
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return None

    try:
        print(f"Loading CSV file: {csv_path}")

        # Read CSV file
        df = pd.read_csv(csv_path)

        # ================================================================
        # KOORDINATEN-SPALTEN FINDEN (wie main_v5.py Zeile 1860-1887)
        # ================================================================
        x_col_candidates = ['x', 'X', 'x_coord', 'X_COORD', 'X_Coordinate', 'x_coordinate',
                           'DIE_X', 'die_x', 'col', 'COL', 'Column']
        y_col_candidates = ['y', 'Y', 'y_coord', 'Y_COORD', 'Y_Coordinate', 'y_coordinate',
                           'DIE_Y', 'die_y', 'row', 'ROW', 'Row']

        x_col = None
        y_col = None

        for candidate in x_col_candidates:
            if candidate in df.columns:
                x_col = candidate
                break

        for candidate in y_col_candidates:
            if candidate in df.columns:
                y_col = candidate
                break

        if x_col is None or y_col is None:
            # Fallback: Erste zwei numerische Spalten verwenden
            print(f"Warning: Could not find standard x/y columns. Available columns: {df.columns.tolist()}")
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                print(f"Using '{x_col}' as X coordinate and '{y_col}' as Y coordinate")
            else:
                print("ERROR: Could not identify coordinate columns in CSV")
                return None

        # Spalten umbenennen zu x, y
        df = df.rename(columns={x_col: 'x', y_col: 'y'})
        print(f"  Renamed '{x_col}' -> 'x', '{y_col}' -> 'y'")

        # ================================================================
        # BIN-SPALTE FINDEN (wie main_v5.py Zeile 1892-1904)
        # ================================================================
        bin_col_candidates = ['HardBin', 'SoftBin', 'hardbin', 'softbin', 'bin', 'BIN', 'Bin',
                             'HARD_BIN', 'hard_bin', 'SOFT_BIN', 'soft_bin', 'HB', 'SB']
        bin_col = None
        for candidate in bin_col_candidates:
            if candidate in df.columns:
                bin_col = candidate
                df = df.rename(columns={bin_col: 'bin'})
                print(f"  Found bin column '{candidate}' -> renamed to 'bin'")
                break

        if 'bin' not in df.columns:
            df['bin'] = 1
            print("  No bin column found, created default bin column (all bins = 1)")

        # ================================================================
        # SOFTBIN SEPARAT BEHANDELN (wie main_v5.py Zeile 1906-1915)
        # ================================================================
        sbin_candidates = ['SoftBin', 'softbin', 'sbin', 'SOFT_BIN', 'soft_bin', 'SB']
        for candidate in sbin_candidates:
            if candidate in df.columns and candidate != bin_col:
                if candidate != 'sbin':
                    df = df.rename(columns={candidate: 'sbin'})
                    print(f"  Renamed SoftBin column '{candidate}' -> 'sbin'")
                break

        # ================================================================
        # WAFER ID AUS DATEINAME (wie main_v5.py Zeile 1917-1918)
        # ================================================================
        wafer_id = os.path.basename(csv_path).replace('.csv', '').replace('.CSV', '')

        # ================================================================
        # TEST-PARAMETER EXTRAHIEREN (wie main_v5.py Zeile 1920-1977)
        # ================================================================
        test_params = {}
        grouped_params = {}
        test_limits_dict = {}

        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        exclude_cols = ['x', 'y', 'bin', 'sbin']
        test_columns = [col for col in numeric_columns if col not in exclude_cols]

        for idx, col in enumerate(test_columns):
            # AM DATA Format konvertieren
            display_name = convert_am_data_column_name(col)

            # Group-Source für Gruppierung
            if ' <> ' in col:
                group_source = col.split(' <> ')[0].strip()
            else:
                group_source = col

            # Whitespace cleanup
            group_source = re.sub(r'\s+', '_', group_source)

            # Test-Nummer aus Spaltennamen extrahieren
            match = re.search(r'_(\d{5,})$', str(display_name)) or re.search(r'_(\d{5,})$', str(col))
            if match:
                test_num = int(match.group(1))
            else:
                test_num = idx + 1

            test_key = f"test_{test_num}"

            # Gruppe erkennen
            group_name = extract_group_from_column(group_source)

            # Spalte umbenennen zu test_num
            df = df.rename(columns={col: test_num})

            test_params[test_key] = display_name

            # In Gruppe einfügen
            if group_name not in grouped_params:
                grouped_params[group_name] = []
            grouped_params[group_name].append((test_num, display_name, display_name))

            # Limits aus Daten berechnen
            col_data = df[test_num].dropna()
            if len(col_data) > 0:
                test_limits_dict[test_num] = {
                    'lo_limit': col_data.min(),
                    'hi_limit': col_data.max(),
                    'units': ''
                }

        # Print detected groups
        print(f"Detected groups from CSV: {list(grouped_params.keys())}")
        for grp, params in grouped_params.items():
            print(f"  {grp}: {len(params)} parameters")

        # ================================================================
        # NOTCH ORIENTATION ERKENNEN (wie main_v5.py Zeile 2019-2081)
        # ================================================================
        notch_orientation = detect_notch_orientation(df, csv_path)

        print(f"Successfully loaded CSV: {wafer_id}")
        print(f"  Dies: {len(df)}, Parameters: {len(test_params)}, Groups: {len(grouped_params)}")

        return LoadedWaferData(
            dataframe=df,
            wafer_id=wafer_id,
            test_parameters=test_params,
            grouped_parameters=grouped_params,
            test_limits=test_limits_dict,
            notch_orientation=notch_orientation,
        )

    except Exception as e:
        print(f"Error loading CSV: {e}")
        import traceback
        traceback.print_exc()
        return None


def detect_notch_orientation(df: pd.DataFrame, csv_path: str) -> str:
    """
    Erkennt Notch-Orientierung aus CSV - wie in main_v5.py Zeile 2019-2081
    """
    notch_orientation = None

    # Check for notch/flat column in CSV
    notch_col_candidates = ['notch', 'Notch', 'NOTCH', 'flat', 'Flat', 'FLAT',
                           'WF_FLAT', 'wf_flat', 'orientation', 'Orientation',
                           'ORIENTATION', 'wafer_flat', 'WAFER_FLAT']

    for candidate in notch_col_candidates:
        if candidate in df.columns:
            notch_values = df[candidate].dropna()
            if len(notch_values) > 0:
                notch_val = str(notch_values.iloc[0]).strip().upper()
                notch_mapping = {
                    'U': 'U', 'UP': 'U', '0': 'U', 'TOP': 'U', 'NORTH': 'U',
                    'D': 'D', 'DOWN': 'D', '180': 'D', 'BOTTOM': 'D', 'SOUTH': 'D',
                    'L': 'L', 'LEFT': 'L', '270': 'L', 'WEST': 'L',
                    'R': 'R', 'RIGHT': 'R', '90': 'R', 'EAST': 'R'
                }
                notch_orientation = notch_mapping.get(notch_val, notch_val[0] if notch_val else None)
                print(f"  Detected notch orientation from column '{candidate}': {notch_orientation}")
            break

    # Check CSV header for notch info
    if notch_orientation is None:
        try:
            with open(csv_path, 'r') as f:
                for i, line in enumerate(f):
                    if i > 20:
                        break
                    line_upper = line.upper()
                    if 'NOTCH' in line_upper or 'FLAT' in line_upper:
                        for orient in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NORTH', 'SOUTH', 'EAST', 'WEST']:
                            if orient in line_upper:
                                notch_mapping = {'UP': 'U', 'DOWN': 'D', 'LEFT': 'L', 'RIGHT': 'R',
                                               'NORTH': 'U', 'SOUTH': 'D', 'WEST': 'L', 'EAST': 'R'}
                                notch_orientation = notch_mapping.get(orient, 'D')
                                print(f"  Detected notch orientation from header: {notch_orientation}")
                                break
                        if notch_orientation:
                            break
        except:
            pass

    # Default to 'D' (down) if not found
    if notch_orientation is None:
        notch_orientation = 'D'
        print(f"  No notch orientation found, using default: {notch_orientation}")

    return notch_orientation
