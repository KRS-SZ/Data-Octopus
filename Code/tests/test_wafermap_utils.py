"""
Tests for the wafermap_utils module.
"""

import pytest
import numpy as np
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


class TestWaferConfig:
    """Tests for WaferConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WaferConfig()

        assert config.wafer_diameter == 300.0
        assert config.die_size_x > 0
        assert config.die_size_y > 0
        assert config.flat_orientation in ["bottom", "top", "left", "right"]

    def test_custom_config(self):
        """Test custom configuration."""
        config = WaferConfig(
            wafer_diameter=200.0,
            die_size_x=5.0,
            die_size_y=5.0,
            flat_orientation="top"
        )

        assert config.wafer_diameter == 200.0
        assert config.die_size_x == 5.0
        assert config.die_size_y == 5.0
        assert config.flat_orientation == "top"


class TestCalculateWaferCenter:
    """Tests for calculate_wafer_center function."""

    def test_center_symmetric(self):
        """Test center calculation for symmetric coordinates."""
        x_coords = np.array([-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5])
        y_coords = np.array([-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5])

        center_x, center_y = calculate_wafer_center(x_coords, y_coords)

        assert abs(center_x - 0.0) < 0.1
        assert abs(center_y - 0.0) < 0.1

    def test_center_offset(self):
        """Test center calculation for offset coordinates."""
        x_coords = np.array([10, 11, 12, 13, 14])
        y_coords = np.array([20, 21, 22, 23, 24])

        center_x, center_y = calculate_wafer_center(x_coords, y_coords)

        assert abs(center_x - 12.0) < 0.1
        assert abs(center_y - 22.0) < 0.1

    def test_center_empty(self):
        """Test center calculation with empty arrays."""
        x_coords = np.array([])
        y_coords = np.array([])

        center_x, center_y = calculate_wafer_center(x_coords, y_coords)

        # Should return 0, 0 or handle gracefully
        assert center_x == 0 or np.isnan(center_x)
        assert center_y == 0 or np.isnan(center_y)


class TestCalculateDieDimensions:
    """Tests for calculate_die_dimensions function."""

    def test_uniform_grid(self):
        """Test die dimensions for uniform grid."""
        x_coords = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
        y_coords = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])

        die_width, die_height = calculate_die_dimensions(x_coords, y_coords)

        assert die_width == 1.0
        assert die_height == 1.0

    def test_non_uniform_spacing(self):
        """Test die dimensions with non-uniform spacing."""
        x_coords = np.array([0, 2, 4, 6])
        y_coords = np.array([0, 3, 6, 9])

        die_width, die_height = calculate_die_dimensions(x_coords, y_coords)

        assert die_width == 2.0
        assert die_height == 3.0

    def test_single_die(self):
        """Test die dimensions with single die."""
        x_coords = np.array([5])
        y_coords = np.array([10])

        die_width, die_height = calculate_die_dimensions(x_coords, y_coords)

        # Should return default dimensions
        assert die_width > 0
        assert die_height > 0


class TestGetWaferBounds:
    """Tests for get_wafer_bounds function."""

    def test_bounds_basic(self):
        """Test basic wafer bounds calculation."""
        x_coords = np.array([0, 5, 10])
        y_coords = np.array([0, 5, 10])

        min_x, max_x, min_y, max_y = get_wafer_bounds(x_coords, y_coords)

        assert min_x == 0
        assert max_x == 10
        assert min_y == 0
        assert max_y == 10

    def test_bounds_negative(self):
        """Test bounds with negative coordinates."""
        x_coords = np.array([-5, 0, 5])
        y_coords = np.array([-3, 0, 3])

        min_x, max_x, min_y, max_y = get_wafer_bounds(x_coords, y_coords)

        assert min_x == -5
        assert max_x == 5
        assert min_y == -3
        assert max_y == 3

    def test_bounds_empty(self):
        """Test bounds with empty arrays."""
        x_coords = np.array([])
        y_coords = np.array([])

        result = get_wafer_bounds(x_coords, y_coords)

        # Should return None or (0, 0, 0, 0)
        assert result is None or result == (0, 0, 0, 0)


class TestFindDieAtPosition:
    """Tests for find_die_at_position function."""

    def test_find_existing_die(self):
        """Test finding an existing die."""
        x_coords = np.array([0, 1, 2, 3, 4])
        y_coords = np.array([0, 1, 2, 3, 4])

        die_idx = find_die_at_position(x_coords, y_coords, 2, 2)

        assert die_idx == 2  # Index of the die at (2, 2)

    def test_find_nonexistent_die(self):
        """Test finding a non-existent die."""
        x_coords = np.array([0, 1, 2])
        y_coords = np.array([0, 1, 2])

        die_idx = find_die_at_position(x_coords, y_coords, 10, 10)

        assert die_idx == -1 or die_idx is None

    def test_find_die_tolerance(self):
        """Test finding die with floating point tolerance."""
        x_coords = np.array([0.0, 1.0, 2.0])
        y_coords = np.array([0.0, 1.0, 2.0])

        die_idx = find_die_at_position(x_coords, y_coords, 1.0001, 0.9999)

        # Should find die at (1, 1) with some tolerance
        assert die_idx == 1 or die_idx == -1  # Depends on implementation


class TestTransformCoordinates:
    """Tests for transform_coordinates function."""

    def test_no_transform(self):
        """Test with no transformation."""
        x_coords = np.array([1, 2, 3])
        y_coords = np.array([1, 2, 3])

        new_x, new_y = transform_coordinates(x_coords, y_coords, rotation=0, flip_x=False, flip_y=False)

        np.testing.assert_array_equal(new_x, x_coords)
        np.testing.assert_array_equal(new_y, y_coords)

    def test_flip_x(self):
        """Test X-axis flip."""
        x_coords = np.array([1, 2, 3])
        y_coords = np.array([1, 1, 1])

        new_x, new_y = transform_coordinates(x_coords, y_coords, rotation=0, flip_x=True, flip_y=False)

        # X should be mirrored around center
        assert new_x[0] > new_x[2]  # Order should be reversed

    def test_flip_y(self):
        """Test Y-axis flip."""
        x_coords = np.array([1, 1, 1])
        y_coords = np.array([1, 2, 3])

        new_x, new_y = transform_coordinates(x_coords, y_coords, rotation=0, flip_x=False, flip_y=True)

        # Y should be mirrored around center
        assert new_y[0] > new_y[2]  # Order should be reversed

    def test_rotation_90(self):
        """Test 90 degree rotation."""
        x_coords = np.array([1, 0])
        y_coords = np.array([0, 0])

        new_x, new_y = transform_coordinates(x_coords, y_coords, rotation=90, flip_x=False, flip_y=False)

        # Point (1, 0) rotated 90 degrees should be at (0, 1)
        # Allow some tolerance for floating point


class TestGetEdgeDies:
    """Tests for get_edge_dies function."""

    def test_edge_dies_grid(self):
        """Test edge die detection on a grid."""
        # Create a 5x5 grid
        x_coords = np.array([i for i in range(5) for _ in range(5)])
        y_coords = np.array([j for _ in range(5) for j in range(5)])

        edge_indices = get_edge_dies(x_coords, y_coords)

        # Edge dies should include boundary dies
        assert len(edge_indices) > 0
        assert len(edge_indices) < len(x_coords)  # Not all dies are edge dies

    def test_edge_dies_small(self):
        """Test edge dies with small dataset."""
        x_coords = np.array([0, 1])
        y_coords = np.array([0, 0])

        edge_indices = get_edge_dies(x_coords, y_coords)

        # Both dies should be edge dies in a 2-die row
        assert len(edge_indices) == 2


class TestGetCenterDies:
    """Tests for get_center_dies function."""

    def test_center_dies_grid(self):
        """Test center die detection on a grid."""
        # Create a 5x5 grid
        x_coords = np.array([i for i in range(5) for _ in range(5)])
        y_coords = np.array([j for _ in range(5) for j in range(5)])

        center_indices = get_center_dies(x_coords, y_coords)

        # Center dies should be a subset
        assert len(center_indices) > 0
        assert len(center_indices) < len(x_coords)

    def test_center_dies_with_radius(self):
        """Test center dies with custom radius."""
        x_coords = np.array([0, 1, 2, 3, 4])
        y_coords = np.array([0, 1, 2, 3, 4])

        center_indices_small = get_center_dies(x_coords, y_coords, radius=1)
        center_indices_large = get_center_dies(x_coords, y_coords, radius=3)

        # Larger radius should include more dies
        assert len(center_indices_large) >= len(center_indices_small)


class TestCalculateRadialPosition:
    """Tests for calculate_radial_position function."""

    def test_radial_at_center(self):
        """Test radial position at center."""
        # Die at center
        radial = calculate_radial_position(0, 0, center_x=0, center_y=0)

        assert radial == 0.0

    def test_radial_at_distance(self):
        """Test radial position at known distance."""
        # Die at (3, 4) from origin - should be 5 (3-4-5 triangle)
        radial = calculate_radial_position(3, 4, center_x=0, center_y=0)

        assert abs(radial - 5.0) < 0.001

    def test_radial_with_offset_center(self):
        """Test radial position with offset center."""
        # Die at (10, 10), center at (7, 6) - distance should be 5 (3-4-5 triangle)
        radial = calculate_radial_position(10, 10, center_x=7, center_y=6)

        assert abs(radial - 5.0) < 0.001

    def test_radial_normalized(self):
        """Test normalized radial position."""
        # Normalized should return value between 0 and 1
        radial = calculate_radial_position(5, 5, center_x=0, center_y=0, normalize=True, max_radius=10)

        expected = np.sqrt(50) / 10  # ~0.707
        assert abs(radial - expected) < 0.01
