"""
STDF Parser Module

Provides functions to parse STDF (Standard Test Data Format) files
and CSV files containing wafermap data.

Supports both Semi-ATE STDF library and pystdf library.
"""

import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# STDF library import handling
STDF_MODULE = None
STDF_TYPE = None

try:
    import Semi_ATE.STDF
    STDF_MODULE = Semi_ATE.STDF
    STDF_TYPE = "Semi_ATE"
except ImportError:
    try:
        import pystdf
        STDF_MODULE = pystdf
        STDF_TYPE = "pystdf"
    except ImportError:
        pass


@dataclass
class WaferConfig:
    """Configuration data from WCR (Wafer Configuration Record)"""
    notch_orientation: Optional[str] = None
    wafer_size: Optional[float] = None
    die_width: Optional[float] = None
    die_height: Optional[float] = None
    pos_x: Optional[str] = None
    pos_y: Optional[str] = None


@dataclass
class TestLimits:
    """Test limits information"""
    lo_limit: Optional[float] = None
    hi_limit: Optional[float] = None
    units: str = ""


@dataclass
class STDFData:
    """Container for parsed STDF data"""
    dataframe: pd.DataFrame
    wafer_id: Optional[str]
    test_parameters: Dict[str, str]
    grouped_parameters: Dict[str, List[Tuple[int, str, str]]]
    test_limits: Dict[int, TestLimits]
    wafer_config: WaferConfig

    @property
    def is_empty(self) -> bool:
        return self.dataframe.empty

    @property
    def die_count(self) -> int:
        return len(self.dataframe)

    @property
    def parameter_count(self) -> int:
        return len(self.test_parameters)

    def get_parameter_values(self, param_key: str) -> pd.Series:
        """Get values for a specific parameter"""
        if param_key in self.dataframe.columns:
            return self.dataframe[param_key]
        return pd.Series()


class STDFParser:
    """
    Parser for STDF (Standard Test Data Format) files.

    Example usage:
        >>> parser = STDFParser()
        >>> data = parser.parse("wafer_data.stdf")
        >>> print(f"Loaded {data.die_count} dies")
    """

    # Pre-compiled regex patterns for performance
    PATTERN_SECTION = re.compile(r'^>{3,}\s*(.+?)\s*<{3,}$')
    PATTERN_SUBGROUP = re.compile(r'^<([A-Za-z][A-Za-z0-9_]*)>$')
    PATTERN_BRACKET = re.compile(r'^\[([A-Za-z][A-Za-z0-9_]*)\]$')
    EXCLUDED_GROUPS = {"Definitions", "Initialization"}

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def _log(self, message: str):
        if self.verbose:
            print(message)

    def parse(self, file_path: str) -> STDFData:
        """
        Parse an STDF file and return structured data.

        Args:
            file_path: Path to the STDF file

        Returns:
            STDFData object containing all parsed information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"STDF file not found: {file_path}")

        if STDF_MODULE is None:
            raise ImportError(
                "No STDF library found. Install with: pip install Semi-ATE-STDF"
            )

        if STDF_TYPE == "pystdf":
            return self._parse_with_pystdf(file_path)
        else:
            return self._parse_with_semi_ate(file_path)

    def _parse_with_semi_ate(self, file_path: str) -> STDFData:
        """Parse STDF using Semi-ATE library"""
        file_size = os.path.getsize(file_path)
        self._log(f"Loading: {os.path.basename(file_path)} ({file_size / 1024 / 1024:.1f} MB)...")
        load_start = time.time()

        wafermap = []
        wafer_id = None
        test_info = {}
        test_groups = {}
        test_limits_dict = {}
        current_die_tests = {}
        current_group = "Ungrouped"
        wafer_config = WaferConfig()

        with open(file_path, "rb") as f:
            records_gen = STDF_MODULE.records_from_file(f)
            record_count = 0
            last_update = time.time()

            for record in records_gen:
                record_count += 1

                # Progress update every 2 seconds
                if record_count % 100000 == 0:
                    now = time.time()
                    if now - last_update > 2.0:
                        elapsed = now - load_start
                        self._log(f"  {record_count:,} records, {len(wafermap):,} dies ({elapsed:.0f}s)...")
                        last_update = now

                rec_type = type(record).__name__

                # Process different record types
                if rec_type == "WCR":
                    wafer_config = self._parse_wcr_record(record)

                elif rec_type == "WIR":
                    wafer_id = self._get_record_value(record, "WAFER_ID")

                elif rec_type == "PIR":
                    current_die_tests = {}

                elif rec_type == "PTR":
                    self._process_ptr_record(
                        record, test_info, test_groups, test_limits_dict,
                        current_die_tests, current_group
                    )

                elif rec_type == "PRR":
                    die_data = self._process_prr_record(record, current_die_tests)
                    if die_data:
                        wafermap.append(die_data)

                elif rec_type == "DTR":
                    new_group = self._process_dtr_record(record)
                    if new_group:
                        current_group = new_group

        # Build result structures
        test_params = {}
        grouped_params = {}

        for test_num, test_name in test_info.items():
            short_name = self._shorten_test_name(test_name) if test_name else f"Test {test_num}"
            test_params[f"test_{test_num}"] = test_name

            group = self._extract_group_from_name(test_name) if test_name else test_groups.get(test_num, "Ungrouped")

            if group not in grouped_params:
                grouped_params[group] = []
            grouped_params[group].append((test_num, short_name, test_name))

        # Convert test_limits_dict to TestLimits objects
        test_limits = {
            k: TestLimits(**v) for k, v in test_limits_dict.items()
        }

        elapsed = time.time() - load_start
        df = pd.DataFrame(wafermap)
        self._log(f"  Done: {record_count:,} records | {len(wafermap):,} dies | {len(test_params)} params | {elapsed:.1f}s")

        return STDFData(
            dataframe=df,
            wafer_id=wafer_id,
            test_parameters=test_params,
            grouped_parameters=grouped_params,
            test_limits=test_limits,
            wafer_config=wafer_config
        )

    def _parse_with_pystdf(self, file_path: str) -> STDFData:
        """Parse STDF using pystdf library"""
        import pystdf

        wafermap = []
        wafer_id = None
        test_info = {}
        test_limits_dict = {}
        current_die_tests = {}
        wafer_config = WaferConfig()

        with open(file_path, "rb") as f:
            parser = pystdf.Parser(inp=f)

            for record in parser:
                if record.id == "WIR":
                    wafer_id = record.WAFER_ID

                elif record.id == "WCR":
                    wafer_config = WaferConfig(
                        notch_orientation=getattr(record, 'WF_FLAT', None),
                        wafer_size=getattr(record, 'WAFR_SIZ', None),
                        die_width=getattr(record, 'DIE_WID', None),
                        die_height=getattr(record, 'DIE_HT', None),
                        pos_x=getattr(record, 'POS_X', None),
                        pos_y=getattr(record, 'POS_Y', None)
                    )

                elif record.id == "PIR":
                    current_die_tests = {}

                elif record.id == "PTR":
                    try:
                        test_num = record.TEST_NUM
                        test_name = record.TEST_TXT
                        result = record.RESULT

                        if test_num is not None and test_name:
                            test_info[test_num] = test_name

                        if test_num is not None and test_num not in test_limits_dict:
                            test_limits_dict[test_num] = {
                                'lo_limit': getattr(record, 'LO_LIMIT', None),
                                'hi_limit': getattr(record, 'HI_LIMIT', None),
                                'units': getattr(record, 'UNITS', "") or ""
                            }

                        if test_num is not None and result is not None:
                            current_die_tests[test_num] = result
                    except (ValueError, KeyError, AttributeError):
                        pass

                elif record.id == "PRR":
                    try:
                        if record.X_COORD is not None and record.Y_COORD is not None:
                            die_data = {
                                "x": record.X_COORD,
                                "y": record.Y_COORD,
                                "bin": record.HARD_BIN if record.HARD_BIN is not None else record.SOFT_BIN,
                            }
                            for test_num in current_die_tests:
                                die_data[f"test_{test_num}"] = current_die_tests[test_num]
                            wafermap.append(die_data)
                    except (ValueError, KeyError, AttributeError):
                        pass

        # Build result structures
        test_params = {f"test_{num}": self._shorten_test_name(name) for num, name in test_info.items()}
        grouped_params = {"Ungrouped": [(num, self._shorten_test_name(name), name) for num, name in test_info.items()]}
        test_limits = {k: TestLimits(**v) for k, v in test_limits_dict.items()}

        return STDFData(
            dataframe=pd.DataFrame(wafermap),
            wafer_id=wafer_id,
            test_parameters=test_params,
            grouped_parameters=grouped_params,
            test_limits=test_limits,
            wafer_config=wafer_config
        )

    def _get_record_value(self, record, field_name: str) -> Any:
        """Get a value from a record using various access methods"""
        if hasattr(record, "get_value"):
            return record.get_value(field_name)
        elif hasattr(record, "fields"):
            return record.fields.get(field_name)
        elif hasattr(record, field_name):
            return getattr(record, field_name)
        return None

    def _parse_wcr_record(self, record) -> WaferConfig:
        """Parse WCR (Wafer Configuration Record)"""
        return WaferConfig(
            notch_orientation=self._get_record_value(record, "WF_FLAT"),
            wafer_size=self._get_record_value(record, "WAFR_SIZ"),
            die_width=self._get_record_value(record, "DIE_WID"),
            die_height=self._get_record_value(record, "DIE_HT"),
            pos_x=self._get_record_value(record, "POS_X"),
            pos_y=self._get_record_value(record, "POS_Y")
        )

    def _process_ptr_record(self, record, test_info, test_groups, test_limits_dict,
                           current_die_tests, current_group):
        """Process PTR (Parametric Test Record)"""
        try:
            test_num = self._get_record_value(record, "TEST_NUM")
            if test_num is None:
                return

            result = self._get_record_value(record, "RESULT")

            if test_num not in test_info:
                test_name = self._get_record_value(record, "TEST_TXT")
                if test_name:
                    test_info[test_num] = test_name
                    test_groups[test_num] = current_group

            if test_num not in test_limits_dict:
                test_limits_dict[test_num] = {
                    'lo_limit': self._get_record_value(record, "LO_LIMIT"),
                    'hi_limit': self._get_record_value(record, "HI_LIMIT"),
                    'units': self._get_record_value(record, "UNITS") or ""
                }

            if result is not None:
                current_die_tests[test_num] = result
        except Exception:
            pass

    def _process_prr_record(self, record, current_die_tests) -> Optional[Dict[str, Any]]:
        """Process PRR (Part Result Record)"""
        try:
            x_coord = self._get_record_value(record, "X_COORD")
            y_coord = self._get_record_value(record, "Y_COORD")

            if x_coord is None or y_coord is None:
                return None

            hard_bin = self._get_record_value(record, "HARD_BIN")
            soft_bin = self._get_record_value(record, "SOFT_BIN")

            die_data = {
                "x": x_coord,
                "y": y_coord,
                "bin": hard_bin if hard_bin is not None else soft_bin,
            }
            die_data.update(current_die_tests)
            return die_data
        except Exception:
            return None

    def _process_dtr_record(self, record) -> Optional[str]:
        """Process DTR (Datalog Text Record) for group information"""
        try:
            text_data = self._get_record_value(record, "TEXT_DAT")
            if not text_data:
                return None

            text_stripped = text_data.strip()

            match = self.PATTERN_SECTION.match(text_stripped)
            if match:
                group_name = match.group(1).strip()
                if group_name and group_name not in self.EXCLUDED_GROUPS:
                    return group_name

            match = self.PATTERN_SUBGROUP.match(text_stripped)
            if match:
                return match.group(1)

            match = self.PATTERN_BRACKET.match(text_stripped)
            if match:
                return match.group(1)

        except Exception:
            pass
        return None

    @staticmethod
    def _shorten_test_name(test_name: str) -> str:
        """Shorten test name by truncating at _X_X_X pattern"""
        if not test_name:
            return test_name

        match = re.search(r'_X_X_X', test_name)
        if match:
            return test_name[:match.start()]

        if len(test_name) > 40:
            return test_name[:37] + "..."
        return test_name

    @staticmethod
    def _extract_group_from_name(test_name: str) -> str:
        """Extract group name from test name"""
        if not test_name:
            return "Ungrouped"

        # Common patterns: DC_LKG_xxx, DC_CONT_xxx, etc.
        parts = test_name.split('_')
        if len(parts) >= 2:
            prefix = f"{parts[0]}_{parts[1]}"
            if prefix in ["DC_LKG", "DC_CONT", "DC_VTH", "AC_FREQ", "AC_DELAY"]:
                return prefix

        if parts:
            return parts[0]

        return "Ungrouped"


def parse_stdf_file(file_path: str, verbose: bool = True) -> STDFData:
    """
    Convenience function to parse an STDF file.

    Args:
        file_path: Path to the STDF file
        verbose: Whether to print progress messages

    Returns:
        STDFData object containing all parsed information
    """
    parser = STDFParser(verbose=verbose)
    return parser.parse(file_path)


def parse_csv_file(file_path: str) -> STDFData:
    """
    Parse a CSV file containing wafermap data.

    Expected CSV format:
        - Columns: x, y, bin, test_XXX, ...
        - Or: X, Y, Bin, Parameter1, Parameter2, ...

    Args:
        file_path: Path to the CSV file

    Returns:
        STDFData object containing the parsed data
    """
    df = pd.read_csv(file_path)

    # Normalize column names
    column_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ['x', 'x_coord', 'xcoord']:
            column_map[col] = 'x'
        elif col_lower in ['y', 'y_coord', 'ycoord']:
            column_map[col] = 'y'
        elif col_lower in ['bin', 'hbin', 'hard_bin', 'sbin', 'soft_bin']:
            column_map[col] = 'bin'

    if column_map:
        df = df.rename(columns=column_map)

    # Extract wafer ID from filename
    wafer_id = os.path.splitext(os.path.basename(file_path))[0]

    # Build test parameters
    test_params = {}
    for col in df.columns:
        if col not in ['x', 'y', 'bin']:
            test_params[col] = col

    return STDFData(
        dataframe=df,
        wafer_id=wafer_id,
        test_parameters=test_params,
        grouped_parameters={"All Parameters": [(i, name, name) for i, name in enumerate(test_params.keys())]},
        test_limits={},
        wafer_config=WaferConfig()
    )
