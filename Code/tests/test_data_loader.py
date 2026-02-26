"""
Tests for the data_loader module.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from stdf_analyzer.core.data_loader import (
    load_csv_file,
)


class TestLoadCSVFile:
    """Tests for load_csv_file function."""

    def test_load_simple_csv(self):
        """Test loading a simple CSV file."""
        # Create temp CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("x,y,value\n")
            f.write("0,0,1.5\n")
            f.write("1,0,2.5\n")
            f.write("0,1,3.5\n")
            temp_path = f.name

        try:
            result = load_csv_file(temp_path)
            df = result[0] if isinstance(result, tuple) else result

            assert df is not None
            assert len(df) == 3
            assert 'x' in df.columns or 'X' in df.columns.str.upper()
        finally:
            os.unlink(temp_path)

    def test_load_csv_with_semicolon_delimiter(self):
        """Test loading CSV with semicolon delimiter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("x;y;value\n")
            f.write("0;0;1.5\n")
            f.write("1;0;2.5\n")
            temp_path = f.name

        try:
            result = load_csv_file(temp_path)
            df = result[0] if isinstance(result, tuple) else result

            assert df is not None
            assert len(df) == 2
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_csv_file("nonexistent_file_12345.csv")

    def test_load_csv_with_header_only(self):
        """Test loading CSV with header but no data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("x,y,value\n")
            temp_path = f.name

        try:
            result = load_csv_file(temp_path)
            df = result[0] if isinstance(result, tuple) else result

            # Should return empty DataFrame with columns
            assert df is not None
            assert len(df) == 0
            assert len(df.columns) > 0
        finally:
            os.unlink(temp_path)


class TestCSVFormats:
    """Tests for various CSV formats encountered in the project."""

    def test_stdf_export_format(self):
        """Test STDF export CSV format."""
        # Simulate STDF export format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("DIE_X,DIE_Y,SBIN,HBIN,PARAM_001,PARAM_002\n")
            f.write("0,0,1,1,1.234,5.678\n")
            f.write("1,0,1,1,1.345,5.789\n")
            f.write("0,1,2,2,0.123,0.456\n")
            temp_path = f.name

        try:
            result = load_csv_file(temp_path)
            df = result[0] if isinstance(result, tuple) else result

            assert df is not None
            assert len(df) == 3
            # Column names should be standardized
            assert 'x' in df.columns or 'DIE_X' in df.columns
        finally:
            os.unlink(temp_path)

    def test_am_data_format(self):
        """Test AM Data CSV format with angle brackets."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("DIE_X,DIE_Y,100<>OPTIC_PARAM,200<>DC_PARAM\n")
            f.write("0,0,1.5,2.5\n")
            f.write("1,0,1.6,2.6\n")
            temp_path = f.name

        try:
            result = load_csv_file(temp_path)
            df = result[0] if isinstance(result, tuple) else result

            assert df is not None
            assert len(df) == 2
            # Should have the angle bracket columns
            assert any('<>' in col for col in df.columns)
        finally:
            os.unlink(temp_path)

    def test_multi_wafer_csv(self):
        """Test multi-wafer CSV format with WAFER_ID column."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("WAFER_ID,DIE_X,DIE_Y,VALUE\n")
            f.write("W01,0,0,1.0\n")
            f.write("W01,1,0,1.1\n")
            f.write("W02,0,0,2.0\n")
            f.write("W02,1,0,2.1\n")
            temp_path = f.name

        try:
            result = load_csv_file(temp_path)
            df = result[0] if isinstance(result, tuple) else result

            assert df is not None
            assert len(df) == 4
        finally:
            os.unlink(temp_path)
