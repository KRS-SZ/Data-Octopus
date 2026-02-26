"""
Wafermap Utilities Module for Data Octopus

Contains utility functions for wafer coordinate calculations,
die positioning, and wafermap visualization helpers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class WaferConfig:
    """Configuration for wafer geometry and display."""
    notch_orientation: str = "down"  # "down", "up", "left", "right"
    wafer_size: float = 300.0  # mm (300mm or 200mm wafers)
    die_width: Optional[float] = None  # mm
    die_height: Optional[float] = None  # mm
    pos_x: str = "right"  # X increases to "left" or "right"
    pos_y: str = "up"  # Y increases "up" or "down"
    edge_exclusion: float = 3.0  # mm from wafer edge


def calculate_wafer_center(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculate the center of the wafer based on die coordinates.

    Args:
        df: DataFrame with 'x' and 'y' columns

    Returns:
        Tuple (center_x, center_y)
    """
    if 'x' not in df.columns or 'y' not in df.columns:
        return (0.0, 0.0)

    center_x = (df['x'].max() + df['x'].min()) / 2
    center_y = (df['y'].max() + df['y'].min()) / 2

    return (center_x, center_y)


def calculate_die_dimensions(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Estimate die dimensions from coordinate spacing.

    Args:
        df: DataFrame with 'x' and 'y' columns

    Returns:
        Tuple (die_width, die_height) - estimated spacing between dies
    """
    if 'x' not in df.columns or 'y' not in df.columns:
        return (1.0, 1.0)

    # Get unique sorted coordinates
    x_unique = np.sort(df['x'].unique())
    y_unique = np.sort(df['y'].unique())

    # Calculate minimum spacing (die size)
    die_width = 1.0
    die_height = 1.0

    if len(x_unique) > 1:
        x_diffs = np.diff(x_unique)
        die_width = np.min(x_diffs[x_diffs > 0]) if len(x_diffs[x_diffs > 0]) > 0 else 1.0

    if len(y_unique) > 1:
        y_diffs = np.diff(y_unique)
        die_height = np.min(y_diffs[y_diffs > 0]) if len(y_diffs[y_diffs > 0]) > 0 else 1.0

    return (die_width, die_height)


def get_wafer_bounds(df: pd.DataFrame, margin: float = 0.5) -> Dict[str, float]:
    """
    Calculate wafer bounds with optional margin.

    Args:
        df: DataFrame with 'x' and 'y' columns
        margin: Fraction of die size to add as margin (0.5 = half die)

    Returns:
        Dict with 'x_min', 'x_max', 'y_min', 'y_max'
    """
    if 'x' not in df.columns or 'y' not in df.columns:
        return {'x_min': -1, 'x_max': 1, 'y_min': -1, 'y_max': 1}

    die_w, die_h = calculate_die_dimensions(df)

    return {
        'x_min': df['x'].min() - margin * die_w,
        'x_max': df['x'].max() + margin * die_w,
        'y_min': df['y'].min() - margin * die_h,
        'y_max': df['y'].max() + margin * die_h,
    }


def transform_coordinates(df: pd.DataFrame,
                          config: WaferConfig) -> pd.DataFrame:
    """
    Transform die coordinates based on wafer configuration.
    Handles notch orientation and axis direction.

    Args:
        df: DataFrame with 'x' and 'y' columns
        config: WaferConfig with orientation settings

    Returns:
        DataFrame with transformed 'x_plot' and 'y_plot' columns
    """
    result = df.copy()

    x = df['x'].values.copy()
    y = df['y'].values.copy()

    # Handle X direction
    if config.pos_x == "left":
        x = -x

    # Handle Y direction
    if config.pos_y == "down":
        y = -y

    # Handle notch orientation (rotate coordinates)
    if config.notch_orientation == "up":
        # Rotate 180 degrees
        x, y = -x, -y
    elif config.notch_orientation == "left":
        # Rotate 90 degrees CCW
        x, y = y, -x
    elif config.notch_orientation == "right":
        # Rotate 90 degrees CW
        x, y = -y, x
    # "down" is default, no rotation needed

    result['x_plot'] = x
    result['y_plot'] = y

    return result


def find_die_at_position(df: pd.DataFrame,
                         click_x: float,
                         click_y: float) -> Optional[int]:
    """
    Find the die index at the clicked position.

    Args:
        df: DataFrame with 'x' and 'y' columns
        click_x: Clicked X coordinate
        click_y: Clicked Y coordinate

    Returns:
        Index of closest die, or None if no die found
    """
    if 'x' not in df.columns or 'y' not in df.columns:
        return None

    if len(df) == 0:
        return None

    # Calculate distance to all dies
    distances = np.sqrt((df['x'] - click_x)**2 + (df['y'] - click_y)**2)

    # Get die dimensions to determine maximum click distance
    die_w, die_h = calculate_die_dimensions(df)
    max_distance = max(die_w, die_h) * 0.75  # Allow some tolerance

    min_idx = distances.idxmin()
    min_dist = distances[min_idx]

    if min_dist <= max_distance:
        return min_idx

    return None


def get_die_neighbors(df: pd.DataFrame,
                      die_idx: int,
                      radius: int = 1) -> List[int]:
    """
    Get neighboring die indices within specified radius.

    Args:
        df: DataFrame with 'x' and 'y' columns
        die_idx: Index of center die
        radius: Number of dies in each direction (default 1 = 3x3 grid)

    Returns:
        List of neighboring die indices
    """
    if die_idx not in df.index:
        return []

    center_x = df.loc[die_idx, 'x']
    center_y = df.loc[die_idx, 'y']

    die_w, die_h = calculate_die_dimensions(df)

    # Find dies within radius
    x_range = (center_x - radius * die_w * 1.5, center_x + radius * die_w * 1.5)
    y_range = (center_y - radius * die_h * 1.5, center_y + radius * die_h * 1.5)

    mask = (
        (df['x'] >= x_range[0]) & (df['x'] <= x_range[1]) &
        (df['y'] >= y_range[0]) & (df['y'] <= y_range[1])
    )

    return df[mask].index.tolist()


def calculate_radial_position(df: pd.DataFrame) -> pd.Series:
    """
    Calculate radial position (distance from center) for each die.

    Args:
        df: DataFrame with 'x' and 'y' columns

    Returns:
        Series with radial distance for each die
    """
    center_x, center_y = calculate_wafer_center(df)

    return np.sqrt((df['x'] - center_x)**2 + (df['y'] - center_y)**2)


def get_edge_dies(df: pd.DataFrame,
                  threshold_percentile: float = 90) -> List[int]:
    """
    Identify edge dies (dies near the wafer edge).

    Args:
        df: DataFrame with 'x' and 'y' columns
        threshold_percentile: Percentile of radial distance to consider "edge"

    Returns:
        List of edge die indices
    """
    radial = calculate_radial_position(df)
    threshold = np.percentile(radial, threshold_percentile)

    return df[radial >= threshold].index.tolist()


def get_center_dies(df: pd.DataFrame,
                    threshold_percentile: float = 25) -> List[int]:
    """
    Identify center dies (dies near the wafer center).

    Args:
        df: DataFrame with 'x' and 'y' columns
        threshold_percentile: Percentile of radial distance to consider "center"

    Returns:
        List of center die indices
    """
    radial = calculate_radial_position(df)
    threshold = np.percentile(radial, threshold_percentile)

    return df[radial <= threshold].index.tolist()


def create_heatmap_grid(df: pd.DataFrame,
                        value_column: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a 2D grid for heatmap plotting from scattered die data.

    Args:
        df: DataFrame with 'x', 'y', and value_column
        value_column: Name of column containing values to plot

    Returns:
        Tuple (X_grid, Y_grid, Z_values) for use with pcolormesh or imshow
    """
    if value_column not in df.columns:
        raise ValueError(f"Column {value_column} not found in DataFrame")

    # Get unique coordinates
    x_unique = np.sort(df['x'].unique())
    y_unique = np.sort(df['y'].unique())

    # Create grid
    X_grid, Y_grid = np.meshgrid(x_unique, y_unique)
    Z_values = np.full(X_grid.shape, np.nan)

    # Fill in values
    for _, row in df.iterrows():
        x_idx = np.where(x_unique == row['x'])[0]
        y_idx = np.where(y_unique == row['y'])[0]
        if len(x_idx) > 0 and len(y_idx) > 0:
            Z_values[y_idx[0], x_idx[0]] = row[value_column]

    return X_grid, Y_grid, Z_values


def get_quadrant(df: pd.DataFrame, die_idx: int) -> str:
    """
    Determine which quadrant a die is in (NE, NW, SE, SW).

    Args:
        df: DataFrame with 'x' and 'y' columns
        die_idx: Index of die

    Returns:
        Quadrant string: "NE", "NW", "SE", or "SW"
    """
    if die_idx not in df.index:
        return "Unknown"

    center_x, center_y = calculate_wafer_center(df)
    die_x = df.loc[die_idx, 'x']
    die_y = df.loc[die_idx, 'y']

    if die_x >= center_x:
        if die_y >= center_y:
            return "NE"
        else:
            return "SE"
    else:
        if die_y >= center_y:
            return "NW"
        else:
            return "SW"
