"""
Tests for the binning module.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from stdf_analyzer.core.binning import BinningLookup, BIN_COLORS, get_bin_colormap


class TestBinningLookup:
    """Tests for the BinningLookup class"""

    def test_init(self):
        """Test initialization of BinningLookup"""
        lookup = BinningLookup()
        assert lookup.loaded is False
        assert lookup.file_path is None
        assert lookup.bin_ranges == []
        assert lookup.bin_definitions == {}

    def test_get_bin_color_known_bin(self):
        """Test getting color for known bins"""
        lookup = BinningLookup()
        assert lookup.get_bin_color(1) == '#4CAF50'  # Green for bin 1
        assert lookup.get_bin_color(2) == '#F44336'  # Red for bin 2

    def test_get_bin_color_unknown_bin(self):
        """Test getting color for unknown bin"""
        lookup = BinningLookup()
        assert lookup.get_bin_color(999) == '#808080'  # Default gray

    def test_is_good_bin(self):
        """Test good bin identification"""
        lookup = BinningLookup()
        assert lookup.is_good_bin(1) is True
        assert lookup.is_good_bin(2) is False
        assert lookup.is_good_bin(99) is False

    def test_get_bin_name_empty(self):
        """Test get_bin_name when no data loaded"""
        lookup = BinningLookup()
        assert lookup.get_bin_name(1) == ""

    def test_get_bin_description_empty(self):
        """Test get_bin_description when no data loaded"""
        lookup = BinningLookup()
        assert lookup.get_bin_description(1) == ""

    def test_get_all_bins_empty(self):
        """Test get_all_bins when no data loaded"""
        lookup = BinningLookup()
        assert lookup.get_all_bins() == {}


class TestBinColors:
    """Tests for BIN_COLORS constant"""

    def test_bin_1_is_green(self):
        """Bin 1 should always be green (good bin)"""
        assert BIN_COLORS[1] == '#4CAF50'

    def test_bin_colors_are_hex(self):
        """All bin colors should be valid hex colors"""
        for bin_num, color in BIN_COLORS.items():
            assert color.startswith('#')
            assert len(color) == 7


class TestGetBinColormap:
    """Tests for the get_bin_colormap function"""

    def test_empty_bins(self):
        """Test with empty bin list"""
        cmap, norm = get_bin_colormap([])
        assert cmap == 'viridis'
        assert norm is None

    def test_single_bin(self):
        """Test with single bin"""
        cmap, norm = get_bin_colormap([1])
        assert cmap is not None
        assert norm is not None

    def test_multiple_bins(self):
        """Test with multiple bins"""
        cmap, norm = get_bin_colormap([1, 2, 3, 4])
        assert cmap is not None
        assert norm is not None

    def test_handles_nan(self):
        """Test that NaN values are filtered out"""
        cmap, norm = get_bin_colormap([1, 2, np.nan, 3])
        assert cmap is not None
