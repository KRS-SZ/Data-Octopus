"""
Tests for the wafermap_utils module.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from stdf_analyzer.core.wafermap_utils import (
    WaferConfig,
    calculate_wafer_center,
    calculate_die_dimensions,
    get_wafer_bounds,
    find_die_at_position,
    transform_coordinates,
    get_edge_dies,
    get_center_dies,
    calculate_radial_position,
)


def create_test_df(x_coords, y_coords):
    """Helper to create test DataFrame from coordinate arrays."""
    return pd.DataFrame({'x': x_coords, 'y': y_coords})


class TestWaferConfig:
    """Tests for WaferConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WaferConfig()

        assert config.wafer_size == 300.0
        assert config.notch_orientation in ["down", "up", "left", "right"]

    def test_custom_config(self):
        """Test custom configuration."""
        config = WaferConfig(
            wafer_size=200.0,
            die_width=5.0,
            die_height=5.0,
            notch_orientation="up"
        )

        assert config.wafer_size == 200.0
        assert config.die_width == 5.0
        assert config.die_height == 5.0
        assert config.notch_orientation == "up"


class TestCalculateWaferCenter:
    """Tests for calculate_wafer_center function."""

    def test_center_symmetric(self):
        """Test center calculation for symmetric coordinates."""
        df = create_test_df(
            x_coords=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
            y_coords=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        )

        center_x, center_y = calculate_wafer_center(df)

        assert abs(center_x - 0.0) < 0.1
        assert abs(center_y - 0.0) < 0.1

    def test_center_offset(self):
        """Test center calculation for offset coordinates."""
        df = create_test_df(
            x_coords=[10, 11, 12, 13, 14],
            y_coords=[20, 21, 22, 23, 24]
        )

        center_x, center_y = calculate_wafer_center(df)

        assert abs(center_x - 12.0) < 0.1
        assert abs(center_y - 22.0) < 0.1

    def test_center_empty(self):
        """Test center calculation with empty DataFrame."""
        df = pd.DataFrame({'x': [], 'y': []})

        center_x, center_y = calculate_wafer_center(df)

        # Should return 0, 0 or handle gracefully
        assert center_x == 0.0 or np.isnan(center_x)
        assert center_y == 0.0 or np.isnan(center_y)


class TestCalculateDieDimensions:
    """Tests for calculate_die_dimensions function."""

    def test_uniform_grid(self):
        """Test die dimensions for uniform grid."""
        df = create_test_df(
            x_coords=[0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
            y_coords=[0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        )

        die_width, die_height = calculate_die_dimensions(df)

        assert die_width == 1.0
        assert die_height == 1.0

    def test_non_uniform_spacing(self):
        """Test die dimensions with non-uniform spacing."""
        df = create_test_df(
            x_coords=[0, 2, 4, 6],
            y_coords=[0, 3, 6, 9]
        )

        die_width, die_height = calculate_die_dimensions(df)

        assert die_width == 2.0
        assert die_height == 3.0

    def test_single_die(self):
        """Test die dimensions with single die."""
        df = create_test_df(x_coords=[5], y_coords=[10])

        die_width, die_height = calculate_die_dimensions(df)

        # Should return default dimensions
        assert die_width > 0
        assert die_height > 0


class TestGetWaferBounds:
    """Tests for get_wafer_bounds function."""

    def test_bounds_basic(self):
        """Test basic wafer bounds calculation."""
        df = create_test_df(x_coords=[0, 5, 10], y_coords=[0, 5, 10])

        bounds = get_wafer_bounds(df)

        assert bounds['x_min'] <= 0
        assert bounds['x_max'] >= 10
        assert bounds['y_min'] <= 0
        assert bounds['y_max'] >= 10

    def test_bounds_negative(self):
        """Test bounds with negative coordinates."""
        df = create_test_df(x_coords=[-5, 0, 5], y_coords=[-3, 0, 3])

        bounds = get_wafer_bounds(df)

        assert bounds['x_min'] <= -5
        assert bounds['x_max'] >= 5
        assert bounds['y_min'] <= -3
        assert bounds['y_max'] >= 3


class TestFindDieAtPosition:
    """Tests for find_die_at_position function."""

    def test_find_existing_die(self):
        """Test finding an existing die."""
        df = create_test_df(
            x_coords=[0, 1, 2, 3, 4],
            y_coords=[0, 1, 2, 3, 4]
        )

        die_idx = find_die_at_position(df, 2, 2)

        assert die_idx == 2  # Index of the die at (2, 2)

    def test_find_nonexistent_die(self):
        """Test finding a non-existent die."""
        df = create_test_df(x_coords=[0, 1, 2], y_coords=[0, 1, 2])

        die_idx = find_die_at_position(df, 100, 100)

        assert die_idx is None

    def test_find_die_tolerance(self):
        """Test finding die with floating point tolerance."""
        df = create_test_df(
            x_coords=[0.0, 1.0, 2.0],
            y_coords=[0.0, 1.0, 2.0]
        )

        die_idx = find_die_at_position(df, 1.1, 0.9)

        # Should find die at (1, 1) with some tolerance
        assert die_idx == 1 or die_idx is None


class TestTransformCoordinates:
    """Tests for transform_coordinates function."""

    def test_no_transform(self):
        """Test with default configuration (no rotation)."""
        df = create_test_df(x_coords=[1, 2, 3], y_coords=[1, 2, 3])
        config = WaferConfig()

        result = transform_coordinates(df, config)

        assert 'x_plot' in result.columns
        assert 'y_plot' in result.columns

    def test_transform_returns_dataframe(self):
        """Test that transform returns a DataFrame."""
        df = create_test_df(x_coords=[1, 2, 3], y_coords=[1, 1, 1])
        config = WaferConfig(notch_orientation="up")

        result = transform_coordinates(df, config)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3


class TestGetEdgeDies:
    """Tests for get_edge_dies function."""

    def test_edge_dies_grid(self):
        """Test edge die detection on a grid."""
        # Create a 5x5 grid
        x_coords = [i for i in range(5) for _ in range(5)]
        y_coords = [j for _ in range(5) for j in range(5)]
        df = create_test_df(x_coords=x_coords, y_coords=y_coords)

        edge_indices = get_edge_dies(df)

        # Edge dies should include boundary dies
        assert len(edge_indices) > 0
        assert len(edge_indices) < len(df)  # Not all dies are edge dies

    def test_edge_dies_small(self):
        """Test edge dies with small dataset."""
        df = create_test_df(x_coords=[0, 1], y_coords=[0, 0])

        edge_indices = get_edge_dies(df)

        # With only 2 dies, at least one should be considered edge
        assert len(edge_indices) > 0


class TestGetCenterDies:
    """Tests for get_center_dies function."""

    def test_center_dies_grid(self):
        """Test center die detection on a grid."""
        # Create a 5x5 grid
        x_coords = [i for i in range(5) for _ in range(5)]
        y_coords = [j for _ in range(5) for j in range(5)]
        df = create_test_df(x_coords=x_coords, y_coords=y_coords)

        center_indices = get_center_dies(df)

        # Center dies should be a subset
        assert len(center_indices) > 0
        assert len(center_indices) < len(df)


class TestCalculateRadialPosition:
    """Tests for calculate_radial_position function."""

    def test_radial_returns_series(self):
        """Test that radial position returns a Series."""
        df = create_test_df(x_coords=[0, 1, 2], y_coords=[0, 1, 2])

        radial = calculate_radial_position(df)

        assert isinstance(radial, pd.Series)
        assert len(radial) == 3

    def test_radial_center_is_zero(self):
        """Test radial position at center is minimum."""
        # Create symmetric grid around (0, 0)
        df = create_test_df(
            x_coords=[-1, 0, 1, -1, 0, 1, -1, 0, 1],
            y_coords=[-1, -1, -1, 0, 0, 0, 1, 1, 1]
        )

        radial = calculate_radial_position(df)

        # Die at center (0, 0) should have minimum radial position
        center_idx = 4  # Index of (0, 0)
        assert radial[center_idx] == radial.min()
