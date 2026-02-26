"""
Parameter Utilities Module for Data Octopus

Contains functions for processing, simplifying, and grouping parameter names
from STDF and CSV test data files.
"""

import re
from typing import Optional, List, Tuple, Any

from src.stdf_analyzer.core.config import (
    KNOWN_GROUP_TYPES,
    MAIN_GROUPS,
    GROUP_NORMALIZATION,
    DETAILED_GROUP_PATTERNS,
    GROUP_PREFIXES,
)


def simplify_param_name(param_name: str) -> str:
    """
    Simplify parameter name by removing group/subgroup prefix and test number suffix.
    Also strips CSV '<>' duplicate name and converts coded values to readable format.

    Conversions (dynamic, not hardcoded):
    - FV0P1 → 0.1V (Force Voltage)
    - FC0P2, FCn0P2 → 0.2mA, -0.2mA (Force Current)
    - AVEEn1p8 → -1.80V
    - DACI3p0 → 3.00uA
    - DC4p59 → 4.59%

    Args:
        param_name: Original parameter name from STDF/CSV

    Returns:
        Simplified, human-readable parameter name
    """
    if not param_name or param_name == "Bin":
        return param_name

    name = str(param_name)

    # Remove test_XXXXX: prefix if present
    if ":" in name:
        name = name.split(":", 1)[-1].strip()

    # ============================================================
    # HANDLE CSV "<>" FORMAT - Use the long name after "<>"
    # ============================================================
    if '<>' in name:
        parts = name.split('<>')
        if len(parts) == 2:
            name = parts[1].strip()  # Use the long name (after <>)

    # Whitespace cleanup - REMOVE SPACES
    name = re.sub(r'\s+', '', name)

    # ============================================================
    # REMOVE GROUP PREFIX DYNAMICALLY
    # Only remove known group types at the beginning (OPTIC_, DC_, ANLG_, FUNC_, etc.)
    # NOT arbitrary XXXX_YYYY_ patterns - those could be test names!
    # ============================================================
    # Pattern: GROUP_SUBGROUP- or GROUP_SUBGROUP_ at the beginning
    # e.g. OPTIC_ANSI-, DC_SHORT_, ANLG_DISPLAYI-
    prefix_match = re.match(r'^([A-Z]+)_([A-Z0-9]+[-_])', name, re.IGNORECASE)
    if prefix_match:
        group_type = prefix_match.group(1).upper()
        if group_type in KNOWN_GROUP_TYPES:
            # Only remove if it's a known group
            name = name[len(prefix_match.group(0)):]

    # ============================================================
    # CONVERT CODED VALUES DYNAMICALLY
    # ============================================================
    name = convert_coded_values(name)

    # ============================================================
    # CLEANUP
    # ============================================================
    name = cleanup_param_name(name)

    return name if name else param_name


def convert_coded_values(name: str) -> str:
    """
    Convert coded values in parameter names to readable format.

    Conversions:
    - FV0P1 → 0.1V (Force Voltage)
    - FC0P2, FCn0P2 → 0.2mA, -0.2mA (Force Current)
    - AVEEn1p8 → -1.80V
    - DACI3p0 → 3.00uA
    - DC4p59 → 4.59%

    Args:
        name: Parameter name possibly containing coded values

    Returns:
        Parameter name with coded values converted
    """
    # FV (Force Voltage): FV0P1 → 0.1V, FV1P8 → 1.8V
    def convert_fv(match):
        integer = match.group(1)
        decimal = match.group(2)
        return f"{integer}.{decimal}V"
    name = re.sub(r'FV(\d+)P(\d+)', convert_fv, name, flags=re.IGNORECASE)

    # FC (Force Current): FC0P2 → 0.2mA, FCn0P2 → -0.2mA
    def convert_fc(match):
        sign = '-' if match.group(1).lower() == 'n' else ''
        integer = match.group(2)
        decimal = match.group(3)
        return f"{sign}{integer}.{decimal}mA"
    name = re.sub(r'FC([np]?)(\d+)P(\d+)', convert_fc, name, flags=re.IGNORECASE)

    # AVEE (Voltage): AVEEn1p8 → -1.80V, AVEE1p8 → 1.80V
    def convert_avee(match):
        sign = '-' if match.group(1).lower() == 'n' else ''
        integer = match.group(2)
        decimal = match.group(3).ljust(2, '0')
        return f"{sign}{integer}.{decimal}V"
    name = re.sub(r'AVEE([np]?)(\d+)p(\d+)', convert_avee, name, flags=re.IGNORECASE)

    # DACI (Current): DACI3p0 → 3.00uA, DACIn0p6 → -0.60uA
    def convert_daci(match):
        sign = '-' if match.group(1).lower() == 'n' else ''
        integer = match.group(2)
        decimal = match.group(3).ljust(2, '0')
        return f"{sign}{integer}.{decimal}uA"
    name = re.sub(r'DACI([np]?)(\d+)p(\d+)', convert_daci, name, flags=re.IGNORECASE)

    # DC (Duty Cycle): DC4p59 → 4.59%
    def convert_dc(match):
        integer = match.group(1)
        decimal = match.group(2)
        return f"{integer}.{decimal}%"
    name = re.sub(r'(?<![A-Z])DC(\d+)p(\d+)', convert_dc, name, flags=re.IGNORECASE)

    return name


def cleanup_param_name(name: str) -> str:
    """
    Clean up parameter name by removing noise patterns.

    Removes:
    - Trailing test numbers (5+ digits)
    - _X_X_X patterns
    - FREERUN, INTFRAME patterns
    - _NV_, _PEQA_ patterns
    - Multiple underscores

    Args:
        name: Parameter name to clean up

    Returns:
        Cleaned parameter name
    """
    # Remove trailing test number (5+ digits at the end after underscore)
    name = re.sub(r'_\d{5,}$', '', name)

    # Remove trailing _X_X_X patterns and other noise
    name = re.sub(r'(_X)+(_|$)', '_', name)
    name = re.sub(r'_?(FREERUN|INTFRAME)_X_', '_', name, flags=re.IGNORECASE)
    name = re.sub(r'_NV_', '_', name)
    name = re.sub(r'_PEQA_', '_', name)
    name = re.sub(r'_+', '_', name)  # Remove double underscores
    name = name.strip('_')

    return name


def extract_group_from_column(col_name: str) -> str:
    """
    Extract group name from column prefix with detailed subgroups.

    This function is used by both Wafermap and Multi-Wafermap tabs
    to categorize parameters into groups for the dropdown menu.

    Args:
        col_name: Column name from DataFrame

    Returns:
        Group name (e.g., 'DC_SHORT', 'OPTIC_ANSI', 'Func', 'Other')
    """
    col_str = str(col_name).upper()

    # First, check for detailed patterns (longer patterns first = more specific)
    for pattern, group in sorted(DETAILED_GROUP_PATTERNS, key=lambda x: -len(x[0])):
        if pattern in col_str:
            return group

    # Fallback: Check for underscore-separated prefix with second level
    if '_' in col_str:
        parts = col_str.split('_')
        if len(parts) >= 2:
            # Try to create a two-level group name
            first_part = parts[0]
            second_part = parts[1]

            if first_part in MAIN_GROUPS:
                # Normalize main group name
                normalized_main = GROUP_NORMALIZATION.get(first_part, first_part)

                # Create subgroup if second part is meaningful (not just numbers)
                if len(second_part) >= 2 and not second_part.isdigit():
                    # Truncate very long subgroup names
                    subgroup = second_part[:10] if len(second_part) > 10 else second_part
                    return f"{normalized_main}_{subgroup}".title()
                else:
                    return normalized_main.title()

            # If first part is short enough, use it as group
            if len(first_part) >= 2 and len(first_part) <= 10:
                return first_part.title()

    # Fallback: Check for known prefixes at start
    for prefix in GROUP_PREFIXES:
        if col_str.startswith(prefix):
            return prefix.title()

    return "Other"  # Default group


def sort_test_params_numerically(items: Any) -> List:
    """
    CENTRAL SORTING FUNCTION for all parameter lists.

    Sorts parameters by numeric test_num (10011000, 10011001, ...).
    Used by ALL tabs (Wafer, Multi-Wafer, Charac-Curve, Statistics, etc.)

    Args:
        items: Can be:
            - dict.items(): List of (test_key, test_name) tuples
            - list: List of tuples (test_num, name, full_name)

    Returns:
        Sorted list
    """
    def sort_key(item):
        # Handle dict.items() format: (test_key, test_name)
        if isinstance(item, tuple) and len(item) >= 2:
            first = item[0]
            # If first element is a string (e.g., "test_10011000")
            if isinstance(first, str) and first.startswith("test_"):
                try:
                    return int(first.replace("test_", ""))
                except ValueError:
                    pass
            # If first element is directly a number (e.g., 10011000 from grouped_parameters)
            elif isinstance(first, (int, float)):
                return int(first)
        return float('inf')  # Non-numeric to end

    return sorted(items, key=sort_key)


def convert_am_data_column_name(col_name: str) -> str:
    """
    Convert AM DATA column names to readable format - DYNAMIC, not hardcoded!

    Functions:
    1. Dynamically detect and remove group prefix (Pattern: XXXX_YYYY- at start)
    2. Convert ALL coded values automatically:
       - FV0P1 → 0.1V (Force Voltage)
       - FC0P2, FCn0P2 → 0.2mA, -0.2mA (Force Current)
       - AVEEn1p8 → -1.80V
       - DACI3p0, DACIn0p6 → 3.00uA, -0.60uA
       - DC4p59 → 4.59%
       - XpY Pattern → X.Y (generic for all values)

    Args:
        col_name: Original column name from AM DATA CSV

    Returns:
        Human-readable column name
    """
    # If no <> separator, return original
    if ' <> ' not in col_name:
        return col_name

    # Extract part after <>  (contains the actual values)
    parts = col_name.split(' <> ')
    if len(parts) != 2:
        return col_name

    long_name = parts[1].strip()

    # Whitespace cleanup - REMOVE SPACES (not replace with _!)
    long_name = re.sub(r'\s+', '', long_name)

    # ============================================================
    # 1. REMOVE GROUP PREFIX DYNAMICALLY
    # ============================================================
    # Pattern: Everything at the beginning until the first subtest indicator
    # Typical subtest start words: LOW, HIGH, STATIC, SINK, SOURCE, PREWARMUP, POSTWARMUP, etc.
    # Or: GROUP_SUBGROUP- (e.g. OPTIC_ANSI-, ANLG_DISPLAYI-)

    # Pattern 1: XXXX_YYYY- or XXXX_YYYY_ at beginning (e.g. OPTIC_ANSI-, DC_SHORT_)
    prefix_match = re.match(r'^([A-Z]+_[A-Z0-9]+[-_])', long_name, re.IGNORECASE)
    if prefix_match:
        long_name = long_name[len(prefix_match.group(1)):]

    # ============================================================
    # 2. CONVERT CODED VALUES DYNAMICALLY
    # ============================================================
    long_name = convert_coded_values(long_name)

    # ============================================================
    # 3. CLEANUP
    # ============================================================
    long_name = cleanup_param_name(long_name)

    return long_name if long_name else col_name
