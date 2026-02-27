"""
Plotly Wafermap Renderer - EXAKT wie main_v5.py!

Verwendet go.Heatmap mit Grid-Berechnung wie update_multi_stdf_heatmap().
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Any, Dict, Optional

# Bin-Farben aus main_v5.py
BIN_COLORS = {
    1: '#4CAF50',   # Grün - GOOD BIN
    2: '#F44336',   # Rot
    3: '#FF9800',   # Orange
    4: '#9C27B0',   # Lila
    5: '#2196F3',   # Blau
    6: '#FFEB3B',   # Gelb
    7: '#795548',   # Braun
    8: '#607D8B',   # Blau-Grau
    9: '#E91E63',   # Pink
    10: '#00BCD4',  # Cyan
    11: '#8BC34A',  # Hell-Grün
    12: '#FF5722',  # Tief-Orange
    13: '#673AB7',  # Tief-Lila
    14: '#03A9F4',  # Hell-Blau
    15: '#CDDC39',  # Lime
    16: '#9E9E9E',  # Grau
}


def create_wafermap_figure(
    df: pd.DataFrame,
    param,
    wafer_id: str = "",
    height: int = 600,
    show_grid: bool = False,
) -> go.Figure:
    """
    Erstellt Wafermap Figure - EXAKT wie update_multi_stdf_heatmap() in main_v5.py!

    Args:
        show_grid: Wenn True, werden Grid-Linien zwischen den Zellen angezeigt
    """
    # Prüfe Daten
    if df is None or len(df) == 0:
        return _empty_figure("No data", height)

    if 'x' not in df.columns or 'y' not in df.columns:
        return _empty_figure("No x/y coordinates", height)

    if param not in df.columns:
        return _empty_figure(f"Parameter '{param}' not found", height)

    # Filter NaN-Werte
    mask = df[param].notna()
    plot_data = df[mask].copy()

    if len(plot_data) == 0:
        return _empty_figure("No valid data", height)

    x = plot_data['x'].values
    y = plot_data['y'].values
    values = plot_data[param].values

    # Grid-Berechnung wie in main_v5.py _compute_grid_fast()
    x_min, x_max = int(np.min(x)), int(np.max(x))
    y_min, y_max = int(np.min(y)), int(np.max(y))

    grid_width = x_max - x_min + 1
    grid_height = y_max - y_min + 1

    # Grid erstellen (NaN = leer)
    grid = np.full((grid_height, grid_width), np.nan)

    # Werte in Grid eintragen
    x_idx = (x - x_min).astype(int)
    y_idx = (y - y_min).astype(int)

    for i in range(len(values)):
        xi, yi = x_idx[i], y_idx[i]
        if 0 <= xi < grid_width and 0 <= yi < grid_height:
            grid[yi, xi] = values[i]

    # Bin oder kontinuierliche Daten?
    param_str = str(param).lower()
    is_bin = param_str in ['bin', 'sbin', 'hbin', 'softbin', 'hardbin']

    if is_bin:
        fig = _create_bin_heatmap(grid, x_min, y_min, x_max, y_max, height)
    else:
        fig = _create_value_heatmap(grid, x_min, y_min, x_max, y_max, param, height)

    # Titel
    title = f"{wafer_id}" if wafer_id else "Wafermap"
    if param:
        title += f" - {param}"

    # Layout wie Desktop: X-Achse OBEN, Grid, grauer Hintergrund, QUADRATISCHE Dies
    fig.update_layout(
        title=dict(text=title, font=dict(size=14), x=0.5),
        xaxis=dict(
            title="X Coordinate",
            side='top',  # X-Achse OBEN wie Desktop!
            tickmode='linear',
            tick0=x_min,
            dtick=5,
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            constrain='domain',
        ),
        yaxis=dict(
            title="Y Coordinate",
            autorange='reversed',  # Y von oben nach unten
            tickmode='linear',
            tick0=y_min,
            dtick=5,
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            scaleanchor='x',  # QUADRATISCHE Dies!
            scaleratio=1,
        ),
        plot_bgcolor='#e8e8e8',  # Grauer Hintergrund wie Desktop!
        height=height,
        margin=dict(l=60, r=80, t=80, b=40),
    )

    # NOTCH Marker hinzufügen (oben in der Mitte)
    x_center = (x_min + x_max) / 2
    fig.add_annotation(
        x=x_center,
        y=y_min - 1,
        text="▼",
        showarrow=False,
        font=dict(size=20, color='red'),
        yref='y',
    )
    fig.add_annotation(
        x=x_center + 2,
        y=y_min - 0.5,
        text="NOTCH",
        showarrow=False,
        font=dict(size=10, color='red'),
        yref='y',
    )

    return fig


def _create_bin_heatmap(grid: np.ndarray, x_min: int, y_min: int,
                        x_max: int, y_max: int, height: int) -> go.Figure:
    """Erstellt Bin-Heatmap mit diskreten Farben."""

    # Unique Bins finden
    unique_bins = np.unique(grid[~np.isnan(grid)]).astype(int)

    # Colorscale für Bins erstellen
    colorscale = []
    for i, bin_val in enumerate(sorted(unique_bins)):
        color = BIN_COLORS.get(int(bin_val), '#808080')
        if len(unique_bins) > 1:
            pos = i / (len(unique_bins) - 1)
        else:
            pos = 0.5
        colorscale.append([pos, color])

    if len(colorscale) == 1:
        colorscale = [[0, colorscale[0][1]], [1, colorscale[0][1]]]

    fig = go.Figure(go.Heatmap(
        z=grid,
        x=np.arange(x_min, x_max + 1),
        y=np.arange(y_min, y_max + 1),
        colorscale=colorscale,
        showscale=True,
        hoverongaps=False,
        hovertemplate="X: %{x}<br>Y: %{y}<br>Bin: %{z}<extra></extra>",
        xgap=1,  # Grid-Linien zwischen Zellen
        ygap=1,
    ))

    return fig


def _create_value_heatmap(grid: np.ndarray, x_min: int, y_min: int,
                          x_max: int, y_max: int, param, height: int) -> go.Figure:
    """Erstellt kontinuierliche Heatmap."""

    # Min/Max für Colorbar
    valid_values = grid[~np.isnan(grid)]
    if len(valid_values) > 0:
        vmin = float(np.min(valid_values))
        vmax = float(np.max(valid_values))
    else:
        vmin, vmax = 0, 1

    fig = go.Figure(go.Heatmap(
        z=grid,
        x=np.arange(x_min, x_max + 1),
        y=np.arange(y_min, y_max + 1),
        colorscale='Viridis',
        zmin=vmin,
        zmax=vmax,
        showscale=True,
        hoverongaps=False,
        hovertemplate=f"X: %{{x}}<br>Y: %{{y}}<br>{param}: %{{z:.4f}}<extra></extra>",
        xgap=1,  # Grid-Linien zwischen Zellen
        ygap=1,
        colorbar=dict(
            title=str(param)[:20],
            tickformat='.2f',
        )
    ))

    return fig


def _empty_figure(message: str, height: int) -> go.Figure:
    """Leere Figure mit Nachricht."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color='gray')
    )
    fig.update_layout(height=height)
    return fig


def get_statistics(df: pd.DataFrame, param) -> Dict[str, Any]:
    """Berechnet Statistiken für einen Parameter."""
    if df is None or param not in df.columns:
        return {'count': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}

    values = pd.to_numeric(df[param], errors='coerce').dropna()

    if len(values) == 0:
        return {'count': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}

    return {
        'count': len(values),
        'mean': float(values.mean()),
        'std': float(values.std()),
        'min': float(values.min()),
        'max': float(values.max()),
        'median': float(values.median()),
    }
