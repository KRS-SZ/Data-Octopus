"""
Wafermap Generator Module

Provides functions to create wafermap visualizations from test data.
Can be used with both matplotlib (for Tkinter) and Plotly (for web).
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .binning import BIN_COLORS, get_bin_colormap


class WafermapGenerator:
    """
    Generator for wafermap visualizations.

    Supports multiple output formats:
    - Matplotlib figure (for Tkinter desktop app)
    - Plotly figure (for web applications)
    - Raw data for custom rendering

    Example usage:
        >>> generator = WafermapGenerator(df, wafer_id="Wafer001")
        >>> fig = generator.create_matplotlib_figure(parameter="bin")
        >>> # or for web:
        >>> plotly_fig = generator.create_plotly_figure(parameter="bin")
    """

    def __init__(
        self,
        data: pd.DataFrame,
        wafer_id: Optional[str] = None,
        wafer_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the wafermap generator.

        Args:
            data: DataFrame with columns 'x', 'y', 'bin', and optional test parameters
            wafer_id: Wafer identifier for title
            wafer_config: Optional wafer configuration (notch orientation, etc.)
        """
        self.data = data
        self.wafer_id = wafer_id or "Unknown"
        self.wafer_config = wafer_config or {}

    @property
    def available_parameters(self) -> List[str]:
        """Get list of available parameters (columns) in the data"""
        exclude = ['x', 'y']
        return [col for col in self.data.columns if col not in exclude]

    @property
    def x_range(self) -> Tuple[int, int]:
        """Get X coordinate range"""
        return int(self.data['x'].min()), int(self.data['x'].max())

    @property
    def y_range(self) -> Tuple[int, int]:
        """Get Y coordinate range"""
        return int(self.data['y'].min()), int(self.data['y'].max())

    @property
    def die_count(self) -> int:
        """Get total number of dies"""
        return len(self.data)

    def get_statistics(self, parameter: str) -> Dict[str, Any]:
        """
        Get statistics for a parameter.

        Args:
            parameter: Column name to analyze

        Returns:
            Dictionary with statistics (mean, std, min, max, etc.)
        """
        if parameter not in self.data.columns:
            return {}

        values = self.data[parameter].dropna()

        return {
            'count': len(values),
            'mean': float(values.mean()) if len(values) > 0 else None,
            'std': float(values.std()) if len(values) > 0 else None,
            'min': float(values.min()) if len(values) > 0 else None,
            'max': float(values.max()) if len(values) > 0 else None,
            'median': float(values.median()) if len(values) > 0 else None,
            'unique_values': int(values.nunique()),
        }

    def create_matplotlib_figure(
        self,
        parameter: str = "bin",
        figsize: Tuple[int, int] = (10, 10),
        title: Optional[str] = None,
        show_colorbar: bool = True,
        marker_size: int = 80,
        show_grid: bool = True
    ):
        """
        Create a matplotlib figure for the wafermap.

        Args:
            parameter: Column name to use for coloring
            figsize: Figure size in inches
            title: Custom title (auto-generated if None)
            show_colorbar: Whether to show the colorbar
            marker_size: Size of die markers
            show_grid: Whether to show grid lines

        Returns:
            matplotlib Figure object
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        if self.data.empty or parameter not in self.data.columns:
            ax.set_title(f"No data for parameter '{parameter}'")
            return fig

        plot_data = self.data.dropna(subset=[parameter])

        if len(plot_data) == 0:
            ax.set_title(f"No valid data for '{parameter}'")
            return fig

        # Determine colormap
        if parameter == "bin":
            unique_bins = plot_data[parameter].unique()
            cmap, norm = get_bin_colormap(unique_bins)
        else:
            cmap = "viridis"
            norm = None

        # Create scatter plot
        sc = ax.scatter(
            plot_data["x"],
            plot_data["y"],
            c=plot_data[parameter],
            cmap=cmap,
            norm=norm,
            s=marker_size,
            edgecolors="black",
            linewidth=0.5,
        )

        # Labels and title
        ax.set_xlabel("X Coordinate", fontsize=12)
        ax.set_ylabel("Y Coordinate", fontsize=12)

        if title:
            ax.set_title(title, fontsize=14)
        else:
            ax.set_title(f"Wafermap - {self.wafer_id}\n{parameter}", fontsize=14)

        if show_grid:
            ax.grid(True, alpha=0.3)

        ax.set_aspect("equal")

        if show_colorbar:
            cbar = plt.colorbar(sc, ax=ax, label=parameter)
            cbar.ax.tick_params(labelsize=10)

        plt.tight_layout()
        return fig

    def create_plotly_figure(
        self,
        parameter: str = "bin",
        title: Optional[str] = None,
        width: int = 700,
        height: int = 700,
        marker_size: int = 10
    ):
        """
        Create a Plotly figure for the wafermap (for web applications).

        Args:
            parameter: Column name to use for coloring
            title: Custom title (auto-generated if None)
            width: Figure width in pixels
            height: Figure height in pixels
            marker_size: Size of die markers

        Returns:
            Plotly Figure object
        """
        try:
            import plotly.express as px
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError("Plotly is required for web visualizations. Install with: pip install plotly")

        if self.data.empty or parameter not in self.data.columns:
            fig = go.Figure()
            fig.add_annotation(text=f"No data for parameter '{parameter}'",
                             xref="paper", yref="paper", x=0.5, y=0.5)
            return fig

        plot_data = self.data.dropna(subset=[parameter]).copy()

        if len(plot_data) == 0:
            fig = go.Figure()
            fig.add_annotation(text=f"No valid data for '{parameter}'",
                             xref="paper", yref="paper", x=0.5, y=0.5)
            return fig

        # Determine color settings
        if parameter == "bin":
            # Use discrete colors for bins
            unique_bins = sorted(plot_data[parameter].unique())
            colors = [BIN_COLORS.get(int(b), '#808080') for b in unique_bins]

            fig = px.scatter(
                plot_data,
                x="x",
                y="y",
                color=parameter,
                color_discrete_sequence=colors,
                category_orders={parameter: unique_bins},
                hover_data=["x", "y", parameter],
            )
        else:
            # Use continuous colorscale for test parameters
            fig = px.scatter(
                plot_data,
                x="x",
                y="y",
                color=parameter,
                color_continuous_scale="Viridis",
                hover_data=["x", "y", parameter],
            )

        # Update layout
        fig.update_traces(marker=dict(size=marker_size, line=dict(width=0.5, color='black')))

        fig.update_layout(
            title=title or f"Wafermap - {self.wafer_id}<br>{parameter}",
            width=width,
            height=height,
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate",
            yaxis=dict(scaleanchor="x", scaleratio=1),
        )

        return fig

    def get_bin_summary(self) -> pd.DataFrame:
        """
        Get a summary of bin distribution.

        Returns:
            DataFrame with bin counts and percentages
        """
        if 'bin' not in self.data.columns:
            return pd.DataFrame()

        bin_counts = self.data['bin'].value_counts().sort_index()
        total = len(self.data)

        summary = pd.DataFrame({
            'Bin': bin_counts.index,
            'Count': bin_counts.values,
            'Percentage': (bin_counts.values / total * 100).round(2)
        })

        return summary

    def get_yield(self, good_bins: List[int] = None) -> float:
        """
        Calculate yield (percentage of good dies).

        Args:
            good_bins: List of bin numbers considered as good (default: [1])

        Returns:
            Yield percentage (0-100)
        """
        if good_bins is None:
            good_bins = [1]

        if 'bin' not in self.data.columns or self.data.empty:
            return 0.0

        good_count = self.data['bin'].isin(good_bins).sum()
        total = len(self.data)

        return (good_count / total * 100) if total > 0 else 0.0


def create_wafermap_figure(
    data: pd.DataFrame,
    parameter: str = "bin",
    wafer_id: str = "Unknown",
    backend: str = "matplotlib",
    **kwargs
) -> Any:
    """
    Convenience function to create a wafermap figure.

    Args:
        data: DataFrame with wafermap data
        parameter: Parameter to visualize
        wafer_id: Wafer identifier
        backend: "matplotlib" or "plotly"
        **kwargs: Additional arguments passed to the figure creation method

    Returns:
        Figure object (matplotlib or plotly)
    """
    generator = WafermapGenerator(data, wafer_id)

    if backend == "plotly":
        return generator.create_plotly_figure(parameter=parameter, **kwargs)
    else:
        return generator.create_matplotlib_figure(parameter=parameter, **kwargs)


def create_multi_wafer_comparison(
    data_list: List[Tuple[pd.DataFrame, str]],
    parameter: str = "bin",
    backend: str = "plotly",
    cols: int = 3
) -> Any:
    """
    Create a multi-wafer comparison visualization.

    Args:
        data_list: List of (DataFrame, wafer_id) tuples
        parameter: Parameter to visualize
        backend: "matplotlib" or "plotly"
        cols: Number of columns in subplot grid

    Returns:
        Figure object with multiple wafermaps
    """
    if backend == "plotly":
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go

        rows = (len(data_list) + cols - 1) // cols

        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[wafer_id for _, wafer_id in data_list]
        )

        for idx, (df, wafer_id) in enumerate(data_list):
            row = idx // cols + 1
            col = idx % cols + 1

            if df.empty or parameter not in df.columns:
                continue

            plot_data = df.dropna(subset=[parameter])

            if parameter == "bin":
                colors = [BIN_COLORS.get(int(b), '#808080') for b in plot_data[parameter]]
            else:
                colors = plot_data[parameter]

            fig.add_trace(
                go.Scatter(
                    x=plot_data["x"],
                    y=plot_data["y"],
                    mode='markers',
                    marker=dict(
                        color=colors,
                        size=6,
                        line=dict(width=0.3, color='black')
                    ),
                    name=wafer_id,
                    showlegend=False
                ),
                row=row, col=col
            )

        fig.update_layout(
            title=f"Multi-Wafer Comparison - {parameter}",
            height=300 * rows,
            width=300 * cols
        )

        return fig

    else:
        import matplotlib.pyplot as plt

        rows = (len(data_list) + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 5*rows))
        axes = np.array(axes).flatten() if len(data_list) > 1 else [axes]

        for idx, (df, wafer_id) in enumerate(data_list):
            ax = axes[idx]

            if df.empty or parameter not in df.columns:
                ax.set_title(f"{wafer_id}\n(No data)")
                continue

            plot_data = df.dropna(subset=[parameter])

            if parameter == "bin":
                unique_bins = plot_data[parameter].unique()
                cmap, norm = get_bin_colormap(unique_bins)
            else:
                cmap = "viridis"
                norm = None

            ax.scatter(
                plot_data["x"],
                plot_data["y"],
                c=plot_data[parameter],
                cmap=cmap,
                norm=norm,
                s=20,
                edgecolors="black",
                linewidth=0.3
            )
            ax.set_title(wafer_id)
            ax.set_aspect("equal")

        # Hide unused axes
        for idx in range(len(data_list), len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()
        return fig
