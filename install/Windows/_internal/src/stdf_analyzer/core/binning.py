"""
Binning Lookup Module

Loads binning information from an Excel file and provides lookup functions
to map test numbers to bin numbers, bin names, and descriptions.
"""

from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.pyplot as plt


# Predefined bin colors: Bin 1 = Green (good bin), others = distinct colors for fail bins
BIN_COLORS = {
    1: '#4CAF50',   # Green - GOOD BIN
    2: '#F44336',   # Red
    3: '#FF9800',   # Orange
    4: '#9C27B0',   # Purple
    5: '#2196F3',   # Blue
    6: '#FFEB3B',   # Yellow
    7: '#795548',   # Brown
    8: '#607D8B',   # Gray-Blue
    9: '#E91E63',   # Pink
    10: '#00BCD4',  # Cyan
    11: '#8BC34A',  # Light Green
    12: '#FF5722',  # Deep Orange
    13: '#673AB7',  # Deep Purple
    14: '#03A9F4',  # Light Blue
    15: '#CDDC39',  # Lime
    16: '#9E9E9E',  # Gray
}


class BinningLookup:
    """
    Loads binning information from an Excel file and provides lookup functions
    to map test numbers to bin numbers, bin names, and descriptions.

    Example usage:
        >>> binning = BinningLookup()
        >>> binning.load_from_excel("binning_table.xlsx")
        >>> bin_num = binning.get_bin_for_test(1234)
        >>> bin_name = binning.get_bin_name(bin_num)
    """

    def __init__(self):
        self.bin_ranges: List[Tuple[int, int, int, str, str]] = []
        self.bin_definitions: Dict[int, Tuple[str, str]] = {}
        self.test_definitions: List[dict] = []  # List of test definitions with all columns
        self.loaded: bool = False
        self.file_path: Optional[str] = None

    def load_from_excel(self, excel_path: str, sheet_name: str = 'BinTable') -> bool:
        """
        Load binning table from Excel file.

        Args:
            excel_path: Path to the Excel file
            sheet_name: Name of the sheet containing binning info (default: 'BinTable')

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            self.bin_ranges = []
            self.bin_definitions = {}
            self.test_definitions = []

            # First pass: Load bin definitions (rows 0-15 with hbin numbers)
            for idx, row in df.iterrows():
                hbin = row.iloc[0] if pd.notna(row.iloc[0]) else None
                hbin_name = row.iloc[1] if pd.notna(row.iloc[1]) else ""
                description = row.iloc[2] if pd.notna(row.iloc[2]) else ""

                # Store bin definition (only for rows with integer hbin in first column)
                if hbin is not None and not pd.isna(hbin):
                    try:
                        hbin_int = int(hbin)
                        if hbin_int >= 1 and hbin_int <= 15:
                            self.bin_definitions[hbin_int] = (str(hbin_name), str(description))
                    except (ValueError, TypeError):
                        pass

            # Second pass: Load test definitions (rows with TestInstance in column B)
            # These start after the header row that contains "TestInstance"
            header_found = False
            for idx, row in df.iterrows():
                # Check if this is the header row
                col1_val = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
                if col1_val == "TestInstance":
                    header_found = True
                    continue

                # Skip rows before header or empty rows
                if not header_found:
                    continue

                # Get test definition data
                test_instance = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                test_name = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                comment = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""

                # Skip empty rows
                if not test_instance and not test_name:
                    continue

                # Get Hbin (column 4)
                hbin = None
                if len(row) > 4 and pd.notna(row.iloc[4]):
                    try:
                        hbin = int(row.iloc[4])
                    except (ValueError, TypeError):
                        pass

                # Get Fail Sbin (column 5)
                fail_sbin = None
                if len(row) > 5 and pd.notna(row.iloc[5]):
                    try:
                        fail_sbin = int(row.iloc[5])
                    except (ValueError, TypeError):
                        pass

                # Get Start Test Number (column 6)
                start_test_num = None
                if len(row) > 6 and pd.notna(row.iloc[6]):
                    try:
                        start_test_num = int(row.iloc[6])
                    except (ValueError, TypeError):
                        pass

                # Get Max Test Number (column 7)
                max_test_num = None
                if len(row) > 7 and pd.notna(row.iloc[7]):
                    try:
                        max_test_num = int(row.iloc[7])
                    except (ValueError, TypeError):
                        pass

                # Store test definition
                self.test_definitions.append({
                    'test_instance': test_instance,
                    'test_name': test_name,
                    'comment': comment,
                    'hbin': hbin,
                    'fail_sbin': fail_sbin,
                    'start_test_num': start_test_num,
                    'max_test_num': max_test_num
                })

                # Also store in bin_ranges for lookup
                if start_test_num is not None and max_test_num is not None and hbin is not None:
                    self.bin_ranges.append((start_test_num, max_test_num, hbin, test_instance, comment))

            self.loaded = True
            self.file_path = excel_path
            print(f"BinningLookup: Loaded {len(self.bin_definitions)} bin definitions and {len(self.test_definitions)} test definitions from {excel_path}")
            return True

        except Exception as e:
            print(f"BinningLookup: Failed to load {excel_path}: {e}")
            import traceback
            traceback.print_exc()
            self.loaded = False
            return False

    def get_bin_for_test(self, test_num: int) -> Optional[int]:
        """
        Get the bin number for a given test number.

        Args:
            test_num: The test number (TEST_NUM from STDF)

        Returns:
            The bin number, or None if not found
        """
        for start, end, hbin, _, _ in self.bin_ranges:
            if start <= test_num <= end:
                return hbin
        return None

    def get_bin_info_for_test(self, test_num: int) -> Optional[Tuple[int, str, str]]:
        """
        Get full bin information for a given test number.

        Args:
            test_num: The test number (TEST_NUM from STDF)

        Returns:
            Tuple of (hbin, hbin_name, description) or None if not found
        """
        for start, end, hbin, hbin_name, description in self.bin_ranges:
            if start <= test_num <= end:
                return (hbin, hbin_name, description)
        return None

    def get_bin_name(self, hbin: int) -> str:
        """
        Get the bin name for a given hardware bin number.

        Args:
            hbin: Hardware bin number

        Returns:
            Bin name string, or empty string if not found
        """
        if hbin in self.bin_definitions:
            return self.bin_definitions[hbin][0]
        return ""

    def get_bin_description(self, hbin: int) -> str:
        """
        Get the bin description for a given hardware bin number.

        Args:
            hbin: Hardware bin number

        Returns:
            Bin description string, or empty string if not found
        """
        if hbin in self.bin_definitions:
            return self.bin_definitions[hbin][1]
        return ""

    def get_all_bins(self) -> Dict[int, Tuple[str, str]]:
        """
        Get all bin definitions.

        Returns:
            Dictionary: hbin -> (hbin_name, description)
        """
        return self.bin_definitions.copy()

    def get_bin_color(self, hbin: int) -> str:
        """
        Get the color for a given bin number.

        Args:
            hbin: Hardware bin number

        Returns:
            Hex color string (e.g., '#4CAF50')
        """
        return BIN_COLORS.get(hbin, '#808080')  # Default to gray

    def is_good_bin(self, hbin: int) -> bool:
        """
        Check if a bin number represents a good (passing) bin.
        By convention, Bin 1 is typically the good bin.

        Args:
            hbin: Hardware bin number

        Returns:
            True if this is a good bin, False otherwise
        """
        return hbin == 1


def get_bin_colormap(unique_bins):
    """
    Create a custom colormap for binning where Bin 1 is always GREEN (good bin).
    Other bins get distinct colors from a predefined palette.

    Args:
        unique_bins: Array or list of unique bin values in the data

    Returns:
        cmap: ListedColormap with Bin 1 as green
        norm: BoundaryNorm for proper bin value mapping
    """
    # Default color for bins > 16
    default_colors = plt.cm.tab20.colors

    sorted_bins = sorted([b for b in unique_bins if not np.isnan(b)])

    if len(sorted_bins) == 0:
        return 'viridis', None

    colors = []
    for bin_val in sorted_bins:
        bin_int = int(bin_val)
        if bin_int in BIN_COLORS:
            colors.append(BIN_COLORS[bin_int])
        else:
            # Use tab20 colors for bins > 16
            color_idx = (bin_int - 1) % len(default_colors)
            colors.append(default_colors[color_idx])

    cmap = ListedColormap(colors)

    # Create boundaries for discrete color mapping
    boundaries = sorted_bins + [sorted_bins[-1] + 1]
    norm = BoundaryNorm(boundaries, cmap.N)

    return cmap, norm
