"""
Data Loader Module for Data Octopus

Contains functions for loading STDF and CSV files and returning DataFrames.
These are standalone loader functions that can be used by any tab module.
"""

import os
import re
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any

# Try to import STDF libraries
try:
    from Semi_ATE.STDF import STDFFile
    STDF_AVAILABLE = True
except ImportError:
    try:
        from pystdf.IO import Parser
        STDF_AVAILABLE = True
    except ImportError:
        STDF_AVAILABLE = False


def load_stdf_file(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[Dict]]:
    """
    Load an STDF file and return a DataFrame with test data.
    
    Args:
        file_path: Path to the STDF file
        
    Returns:
        Tuple of (DataFrame, wafer_id, wafer_config)
        - DataFrame with columns: x, y, bin, and test parameters
        - wafer_id: Wafer identifier from MIR/WIR record
        - wafer_config: Dict with notch_orientation, wafer_size, etc.
    """
    if not STDF_AVAILABLE:
        raise ImportError("No STDF library available (Semi_ATE.STDF or pystdf)")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"STDF file not found: {file_path}")
    
    # This is a simplified loader - the full implementation would parse STDF records
    # For now, return None to indicate the caller should use the main app's loader
    return None, None, None


def load_csv_file(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load a CSV file and return a DataFrame with test data.
    
    Supports multiple CSV formats:
    - Standard CSV with x, y, bin columns
    - AM DATA format with '<>' separator in column names
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (DataFrame, wafer_id)
        - DataFrame with columns: x, y, bin, and test parameters
        - wafer_id: Extracted from filename or first data column
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Try to detect the CSV format
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        first_lines = [f.readline() for _ in range(5)]
    
    # Check if it's a standard CSV or has special format
    header_line = first_lines[0] if first_lines else ""
    
    # Detect delimiter
    if '\t' in header_line:
        delimiter = '\t'
    elif ';' in header_line:
        delimiter = ';'
    else:
        delimiter = ','
    
    # Load the CSV
    try:
        df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8', errors='ignore')
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")
    
    # Standardize column names
    df = _standardize_columns(df)
    
    # Extract wafer ID from filename
    wafer_id = os.path.splitext(os.path.basename(file_path))[0]
    
    # Try to extract wafer ID from column if present
    for col in ['wafer_id', 'WAFER_ID', 'WaferID', 'wafer']:
        if col in df.columns:
            unique_ids = df[col].dropna().unique()
            if len(unique_ids) > 0:
                wafer_id = str(unique_ids[0])
            break
    
    return df, wafer_id


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names in a DataFrame.
    
    Converts common variations to standard names:
    - x, X, die_x, DIE_X, X_COORD -> x
    - y, Y, die_y, DIE_Y, Y_COORD -> y
    - bin, BIN, hbin, HBIN, hard_bin -> bin
    - sbin, SBIN, soft_bin -> sbin
    """
    column_map = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # X coordinate
        if col_lower in ['x', 'die_x', 'x_coord', 'xcoord', 'x_die']:
            column_map[col] = 'x'
        # Y coordinate
        elif col_lower in ['y', 'die_y', 'y_coord', 'ycoord', 'y_die']:
            column_map[col] = 'y'
        # Hard bin
        elif col_lower in ['bin', 'hbin', 'hard_bin', 'hardbin']:
            column_map[col] = 'bin'
        # Soft bin
        elif col_lower in ['sbin', 'soft_bin', 'softbin']:
            column_map[col] = 'sbin'
    
    # Rename columns
    if column_map:
        df = df.rename(columns=column_map)
    
    return df


def detect_test_parameters(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect test parameters in a DataFrame.
    
    Returns a dict mapping column names to simplified display names.
    Excludes coordinate and bin columns.
    """
    from src.stdf_analyzer.core.parameter_utils import simplify_param_name
    
    excluded = {'x', 'y', 'bin', 'sbin', 'wafer_id', 'lot_id', 'site', 'head'}
    test_params = {}
    
    for col in df.columns:
        if col.lower() not in excluded:
            # Check if column has numeric data
            if df[col].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(df[col]):
                short_name = simplify_param_name(col)
                test_params[col] = short_name
    
    return test_params


def group_parameters(test_params: Dict[str, str]) -> Dict[str, list]:
    """
    Group test parameters by their group prefix.
    
    Args:
        test_params: Dict mapping column names to display names
        
    Returns:
        Dict mapping group names to list of (column_name, display_name) tuples
    """
    from src.stdf_analyzer.core.parameter_utils import extract_group_from_column
    
    grouped = {}
    
    for col, display_name in test_params.items():
        group = extract_group_from_column(col)
        if group not in grouped:
            grouped[group] = []
        grouped[group].append((col, display_name))
    
    # Sort parameters within each group
    for group in grouped:
        grouped[group].sort(key=lambda x: x[1])
    
    return grouped
