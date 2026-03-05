"""
Datalog Parser Module for Data Octopus

Contains functions for parsing TXT Datalog files from IGXL/93K testers.
Extracts test results, header info, and converts to DataFrame.

Datalog Format:
- Header lines with Prog Name, Job Name, Lot, Operator, etc.
- Test sections: Initialization, DC Tests, Optical Tests, etc.
- Test result lines: Number, Site, Test Name, Pin, Channel, Low, Measured, High, Force, Loc
"""

import re
import os
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DatalogHeader:
    """Parsed header information from a datalog file."""
    prog_name: str = ""
    job_name: str = ""
    lot_id: str = ""
    operator: str = ""
    test_mode: str = ""
    node_name: str = ""
    part_type: str = ""
    channel_map: str = ""
    timestamp: Optional[datetime] = None
    wafer_color: str = ""
    device_count: int = 0
    site_number: int = 0


@dataclass
class TestResult:
    """Single test result from datalog."""
    test_number: int
    site: int
    test_name: str
    pin: str = ""
    channel: str = ""
    low_limit: Optional[float] = None
    measured: Optional[float] = None
    high_limit: Optional[float] = None
    force: Optional[float] = None
    location: int = 0
    unit: str = ""
    pass_fail: str = "P"  # P=Pass, F=Fail
    section: str = ""  # DC Tests, Optical Tests, etc.


def parse_datalog_file(file_path: str) -> Tuple[DatalogHeader, pd.DataFrame]:
    """
    Parse a TXT Datalog file and return header info and test results.

    Args:
        file_path: Path to the .txt datalog file

    Returns:
        Tuple of (DatalogHeader, DataFrame with test results)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Datalog file not found: {file_path}")

    header = DatalogHeader()
    results: List[TestResult] = []
    current_section = "Unknown"

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Parse header information
        if line.startswith("Prog Name:"):
            header.prog_name = line.split(":", 1)[1].strip()
        elif line.startswith("Job Name:"):
            header.job_name = line.split(":", 1)[1].strip()
        elif line.startswith("Lot:"):
            header.lot_id = line.split(":", 1)[1].strip()
        elif line.startswith("Operator:"):
            header.operator = line.split(":", 1)[1].strip()
        elif line.startswith("Test Mode:"):
            header.test_mode = line.split(":", 1)[1].strip()
        elif line.startswith("Node Name:"):
            header.node_name = line.split(":", 1)[1].strip()
        elif line.startswith("Part Type:"):
            header.part_type = line.split(":", 1)[1].strip()
        elif line.startswith("Channel map:"):
            header.channel_map = line.split(":", 1)[1].strip()
        elif line.startswith("Device#:"):
            try:
                header.device_count = int(line.split(":")[1].strip())
            except:
                pass
        elif "Wafer Color" in line:
            match = re.search(r'Wafer Color.*?:\s*(\w+)', line)
            if match:
                header.wafer_color = match.group(1)

        # Parse section headers
        if line.startswith(">>>>>>") and "<<<<<<" in line:
            section_match = re.search(r'>>>>>>(.+?)<<<<<<', line)
            if section_match:
                current_section = section_match.group(1).strip()

        # Parse test section markers
        if line.startswith("<") and line.endswith(">") and not line.startswith("<<"):
            current_section = line[1:-1]

        # Parse test result lines
        # Format: Number Site TestName Pin Channel Low Measured High Force Loc
        result = _parse_test_line(line, current_section)
        if result:
            results.append(result)

        i += 1

    # Convert to DataFrame
    df = _results_to_dataframe(results)

    return header, df


def _parse_test_line(line: str, section: str) -> Optional[TestResult]:
    """
    Parse a single test result line.

    Format varies but typically:
    Number Site TestName Pin Channel Low Measured High Force Loc
    """
    # Skip header lines and empty lines
    if not line or line.startswith("Number") or line.startswith(">>>") or line.startswith("<"):
        return None

    # Skip non-numeric starting lines
    parts = line.split()
    if len(parts) < 3:
        return None

    # First column should be test number (numeric)
    try:
        test_number = int(parts[0])
    except ValueError:
        return None

    # Second column is site number
    try:
        site = int(parts[1])
    except ValueError:
        site = 0

    # Third column is test name (can be very long)
    # Find where the test name ends by looking for numeric values
    test_name = parts[2]

    result = TestResult(
        test_number=test_number,
        site=site,
        test_name=test_name,
        section=section
    )

    # Parse remaining columns - they vary based on test type
    # Look for patterns like: Pin, Channel, Low, Measured, High, Force, Loc
    remaining = ' '.join(parts[3:])

    # Extract measured value - look for patterns like "35.1906 nA", "2.8213 mA", etc.
    measured_match = re.search(r'(-?\d+\.?\d*)\s*(nA|uA|mA|A|mV|V|mW|W|ms|us|ns|%)?', remaining)
    if measured_match:
        try:
            result.measured = float(measured_match.group(1))
            result.unit = measured_match.group(2) or ""
        except:
            pass

    # Extract limits
    # Low limit typically before measured, high limit after
    limit_pattern = r'(-?\d+\.?\d*)\s*(nA|uA|mA|A|mV|V|mW|W)?'
    limits = re.findall(limit_pattern, remaining)

    if len(limits) >= 3:
        try:
            result.low_limit = float(limits[0][0])
            result.measured = float(limits[1][0])
            result.high_limit = float(limits[2][0])
        except:
            pass

    # Determine pass/fail
    if result.measured is not None:
        if result.low_limit is not None and result.measured < result.low_limit:
            result.pass_fail = "F"
        elif result.high_limit is not None and result.measured > result.high_limit:
            result.pass_fail = "F"
        else:
            result.pass_fail = "P"

    # Extract pin name (usually after test name)
    pin_match = re.search(r'\s+([A-Z_][A-Z0-9_]*)\s+\d+\.', remaining)
    if pin_match:
        result.pin = pin_match.group(1)

    return result


def _results_to_dataframe(results: List[TestResult]) -> pd.DataFrame:
    """Convert list of TestResult objects to DataFrame."""
    if not results:
        return pd.DataFrame()

    data = {
        'test_number': [r.test_number for r in results],
        'site': [r.site for r in results],
        'test_name': [r.test_name for r in results],
        'pin': [r.pin for r in results],
        'channel': [r.channel for r in results],
        'low_limit': [r.low_limit for r in results],
        'measured': [r.measured for r in results],
        'high_limit': [r.high_limit for r in results],
        'force': [r.force for r in results],
        'unit': [r.unit for r in results],
        'pass_fail': [r.pass_fail for r in results],
        'section': [r.section for r in results],
    }

    return pd.DataFrame(data)


def parse_datalog_advanced(file_path: str) -> Tuple[DatalogHeader, pd.DataFrame]:
    """
    Advanced parser that handles the specific IGXL format better.

    Handles columns:
    Number   Site  Test Name   Pin   Channel  Low   Measured   High   Force   Loc
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Datalog file not found: {file_path}")

    header = DatalogHeader()
    results = []
    current_section = "Unknown"

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    lines = content.split('\n')

    # Parse header
    for line in lines[:50]:  # Header is usually in first 50 lines
        line = line.strip()
        if "Prog Name:" in line:
            header.prog_name = line.split(":", 1)[1].strip()
        elif "Job Name:" in line:
            header.job_name = line.split(":", 1)[1].strip()
        elif "Lot:" in line:
            header.lot_id = line.split(":", 1)[1].strip()
        elif "Operator:" in line:
            header.operator = line.split(":", 1)[1].strip()
        elif "Test Mode:" in line:
            header.test_mode = line.split(":", 1)[1].strip()
        elif "Node Name:" in line:
            header.node_name = line.split(":", 1)[1].strip()
        elif "Part Type:" in line:
            header.part_type = line.split(":", 1)[1].strip()
        elif "Wafer Color" in line:
            match = re.search(r'Wafer Color.*?:\s*(\w+)', line)
            if match:
                header.wafer_color = match.group(1)

    # Parse test results using regex for the specific format
    # Pattern: test_number site test_name pin channel low measured high force loc
    test_pattern = re.compile(
        r'^\s*(\d+)\s+'           # test_number
        r'(\d+)\s+'               # site
        r'(\S+)\s+'               # test_name
        r'(\S+)?\s*'              # pin (optional)
        r'(\S+)?\s*'              # channel (optional)
        r'(-?[\d.]+\s*\w*)?\s*'   # low_limit with unit (optional)
        r'(-?[\d.]+\s*\w*)?\s*'   # measured with unit (optional)
        r'(-?[\d.]+\s*\w*)?\s*'   # high_limit with unit (optional)
        r'(-?[\d.]+\s*\w*)?\s*'   # force with unit (optional)
        r'(\d+)?'                 # location (optional)
    )

    for line in lines:
        line_stripped = line.strip()

        # Track sections
        if line_stripped.startswith("<") and line_stripped.endswith(">"):
            current_section = line_stripped[1:-1]
            continue

        if line_stripped.startswith(">>>>>>"):
            match = re.search(r'>>>>>>(.+?)<<<<<<', line_stripped)
            if match:
                current_section = match.group(1).strip()
            continue

        # Skip header lines
        if line_stripped.startswith("Number") or not line_stripped:
            continue

        # Try to parse as test line
        parts = line_stripped.split()
        if len(parts) >= 3:
            try:
                test_num = int(parts[0])
                site = int(parts[1])
                test_name = parts[2]

                # Create result
                result = {
                    'test_number': test_num,
                    'site': site,
                    'test_name': test_name,
                    'section': current_section,
                    'pin': '',
                    'channel': '',
                    'low_limit': None,
                    'measured': None,
                    'high_limit': None,
                    'force': None,
                    'unit': '',
                    'pass_fail': 'P',
                    'raw_line': line_stripped
                }

                # Parse values from remaining parts
                remaining = ' '.join(parts[3:])

                # Find numeric values with units
                value_pattern = r'(-?\d+\.?\d*)\s*(nA|uA|mA|A|mV|V|mW|W|ms|us|ns|%|m)?'
                values = re.findall(value_pattern, remaining)

                # Assign values based on position (typically: pin, channel, low, measured, high, force)
                numeric_values = []
                for val, unit in values:
                    try:
                        numeric_values.append((float(val), unit))
                    except:
                        pass

                if len(numeric_values) >= 3:
                    result['low_limit'] = numeric_values[0][0]
                    result['measured'] = numeric_values[1][0]
                    result['high_limit'] = numeric_values[2][0]
                    result['unit'] = numeric_values[1][1]
                elif len(numeric_values) == 1:
                    result['measured'] = numeric_values[0][0]
                    result['unit'] = numeric_values[0][1]

                # Check pass/fail
                if result['measured'] is not None:
                    if result['low_limit'] is not None and result['measured'] < result['low_limit']:
                        result['pass_fail'] = 'F'
                    elif result['high_limit'] is not None and result['measured'] > result['high_limit']:
                        result['pass_fail'] = 'F'

                results.append(result)

            except (ValueError, IndexError):
                continue

    # Convert to DataFrame
    if results:
        df = pd.DataFrame(results)
    else:
        df = pd.DataFrame()

    return header, df


def get_datalog_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for a parsed datalog.

    Returns:
        Dict with total_tests, pass_count, fail_count, yield_pct, sections, etc.
    """
    if df.empty:
        return {
            'total_tests': 0,
            'pass_count': 0,
            'fail_count': 0,
            'yield_pct': 0.0,
            'sections': [],
            'unique_pins': []
        }

    total = len(df)
    pass_count = len(df[df['pass_fail'] == 'P'])
    fail_count = total - pass_count
    yield_pct = 100.0 * pass_count / total if total > 0 else 0.0

    sections = df['section'].unique().tolist() if 'section' in df.columns else []
    pins = df['pin'].dropna().unique().tolist() if 'pin' in df.columns else []

    return {
        'total_tests': total,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'yield_pct': yield_pct,
        'sections': sections,
        'unique_pins': pins,
        'test_numbers': df['test_number'].unique().tolist() if 'test_number' in df.columns else []
    }


def get_failed_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Return only failed tests from datalog."""
    if df.empty or 'pass_fail' not in df.columns:
        return pd.DataFrame()

    return df[df['pass_fail'] == 'F'].copy()


def get_tests_by_section(df: pd.DataFrame, section: str) -> pd.DataFrame:
    """Return tests filtered by section."""
    if df.empty or 'section' not in df.columns:
        return pd.DataFrame()

    return df[df['section'] == section].copy()
