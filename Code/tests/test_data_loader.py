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
    detect_csv_format,
    extract_wafer_id_from_filename,
    normalize_column_names,
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
            df = load_csv_file(temp_path)
            
            assert df is not None
            assert len(df) == 3
            assert 'x' in df.columns or 'X' in df.columns.str.upper()
            assert 'y' in df.columns or 'Y' in df.columns.str.upper()
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
            df = load_csv_file(temp_path)
            
            assert df is not None
            assert len(df) == 2
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        result = load_csv_file("nonexistent_file_12345.csv")
        
        assert result is None

    def test_load_empty_csv(self):
        """Test loading empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            df = load_csv_file(temp_path)
            
            # Should return None or empty DataFrame
            assert df is None or len(df) == 0
        finally:
            os.unlink(temp_path)

    def test_load_csv_with_header_only(self):
        """Test loading CSV with header but no data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("x,y,value\n")
            temp_path = f.name
        
        try:
            df = load_csv_file(temp_path)
            
            # Should return empty DataFrame with columns
            assert df is not None
            assert len(df) == 0
            assert len(df.columns) > 0
        finally:
            os.unlink(temp_path)


class TestDetectCSVFormat:
    """Tests for detect_csv_format function."""

    def test_detect_comma_delimiter(self):
        """Test detection of comma delimiter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b,c\n1,2,3\n")
            temp_path = f.name
        
        try:
            result = detect_csv_format(temp_path)
            
            assert result['delimiter'] == ','
        finally:
            os.unlink(temp_path)

    def test_detect_semicolon_delimiter(self):
        """Test detection of semicolon delimiter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a;b;c\n1;2;3\n")
            temp_path = f.name
        
        try:
            result = detect_csv_format(temp_path)
            
            assert result['delimiter'] == ';'
        finally:
            os.unlink(temp_path)

    def test_detect_tab_delimiter(self):
        """Test detection of tab delimiter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a\tb\tc\n1\t2\t3\n")
            temp_path = f.name
        
        try:
            result = detect_csv_format(temp_path)
            
            assert result['delimiter'] == '\t'
        finally:
            os.unlink(temp_path)

    def test_detect_angle_bracket_format(self):
        """Test detection of angle bracket format (123<>Name)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("123<>TestParam,456<>OtherParam\n1.5,2.5\n")
            temp_path = f.name
        
        try:
            result = detect_csv_format(temp_path)
            
            assert result.get('has_angle_brackets', False) == True
        finally:
            os.unlink(temp_path)


class TestExtractWaferIdFromFilename:
    """Tests for extract_wafer_id_from_filename function."""

    def test_extract_standard_wafer_id(self):
        """Test extracting wafer ID from standard filename."""
        # Common patterns
        result = extract_wafer_id_from_filename("Wafer_01_data.csv")
        assert "01" in result or "Wafer_01" in result
        
        result = extract_wafer_id_from_filename("W25_test_results.csv")
        assert "25" in result or "W25" in result

    def test_extract_lot_wafer_format(self):
        """Test extracting from LOT_WAFER format."""
        result = extract_wafer_id_from_filename("ABC123_W05_measurements.csv")
        assert "05" in result or "W05" in result or "ABC123" in result

    def test_extract_from_complex_filename(self):
        """Test extracting from complex filename."""
        result = extract_wafer_id_from_filename("9ATE3_LOT123_W12_Run5_STDF.csv")
        # Should extract something meaningful
        assert result is not None
        assert len(result) > 0

    def test_extract_from_simple_filename(self):
        """Test extracting from simple filename without wafer pattern."""
        result = extract_wafer_id_from_filename("data.csv")
        # Should return filename without extension or some default
        assert result is not None

    def test_extract_with_path(self):
        """Test extracting from full path."""
        result = extract_wafer_id_from_filename("/path/to/Wafer_03_data.csv")
        assert "03" in result or "Wafer_03" in result

    def test_extract_empty_string(self):
        """Test with empty string."""
        result = extract_wafer_id_from_filename("")
        assert result == "" or result is None


class TestNormalizeColumnNames:
    """Tests for normalize_column_names function."""

    def test_normalize_basic(self):
        """Test basic column name normalization."""
        df = pd.DataFrame({
            'X_Coord': [1, 2],
            'Y_Coord': [3, 4],
            'Value': [5, 6]
        })
        
        result = normalize_column_names(df)
        
        # Should have normalized x and y columns
        assert 'x' in result.columns or 'X' in result.columns
        assert 'y' in result.columns or 'Y' in result.columns

    def test_normalize_die_x_y(self):
        """Test normalization of DIE_X, DIE_Y columns."""
        df = pd.DataFrame({
            'DIE_X': [1, 2],
            'DIE_Y': [3, 4],
            'RESULT': [5, 6]
        })
        
        result = normalize_column_names(df)
        
        # Should recognize DIE_X/DIE_Y as coordinate columns
        assert 'x' in result.columns.str.lower() or 'die_x' in result.columns.str.lower()

    def test_normalize_preserves_data(self):
        """Test that normalization preserves data."""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        
        result = normalize_column_names(df)
        
        # Data should be preserved
        assert len(result) == 3
        assert len(result.columns) >= 2

    def test_normalize_empty_dataframe(self):
        """Test normalization of empty DataFrame."""
        df = pd.DataFrame()
        
        result = normalize_column_names(df)
        
        assert len(result) == 0

    def test_normalize_angle_bracket_columns(self):
        """Test normalization of angle bracket format columns."""
        df = pd.DataFrame({
            '123<>OPTIC_Test': [1, 2],
            '456<>DC_Param': [3, 4]
        })
        
        result = normalize_column_names(df)
        
        # Columns should still exist
        assert len(result.columns) == 2


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
            df = load_csv_file(temp_path)
            
            assert df is not None
            assert len(df) == 3
            assert 'DIE_X' in df.columns or 'die_x' in df.columns.str.lower()
            assert 'SBIN' in df.columns or 'sbin' in df.columns.str.lower()
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
            df = load_csv_file(temp_path)
            
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
            df = load_csv_file(temp_path)
            
            assert df is not None
            assert len(df) == 4
            assert 'WAFER_ID' in df.columns or 'wafer_id' in df.columns.str.lower()
        finally:
            os.unlink(temp_path)
