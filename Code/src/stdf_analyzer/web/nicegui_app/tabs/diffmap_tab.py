"""
Diffmap Tab - Web Version.

Vergleich von Parametern zwischen Wafern.
"""

from nicegui import ui
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class DiffmapTab:
    """
    Diffmap Tab für Wafer-Differenz-Analyse.

    Features:
    - Reference vs Target Wafer
    - Delta Heatmap
    - Correlation Plot
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state
        self.container = None

    def build(self, parent: Any = None) -> None:
        """Tab UI aufbauen."""
        with ui.column().classes('w-full h-full p-2') as self.container:
            # Wafer Selection
            with ui.row().classes('gap-4 items-center mb-2'):
                ui.label('Reference:')
                self.ref_select = ui.select(options=[], label='Reference Wafer').classes('w-48')

                ui.label('Target:')
                self.target_select = ui.select(options=[], label='Target Wafer').classes('w-48')

                ui.label('Parameter:')
                self.param_select = ui.select(options=[], label='Parameter').classes('w-64')

                ui.button('Calculate Diff', on_click=self._calculate_diff).classes(
                    'bg-blue-500 text-white'
                ).props('dense')

            # Diff Options
            with ui.row().classes('gap-4 items-center mb-2'):
                self.diff_type = ui.select(
                    options=['Absolute', 'Percentage', 'Ratio'],
                    value='Absolute',
                    label='Diff Type'
                ).classes('w-32')

                self.colorscale = ui.select(
                    options=['RdBu', 'Viridis', 'Plasma', 'Inferno'],
                    value='RdBu',
                    label='Colorscale'
                ).classes('w-32')

            # Plot Area
            with ui.row().classes('w-full gap-2'):
                # Reference Wafermap
                with ui.card().classes('flex-1'):
                    ui.label('Reference').classes('font-bold')
                    self.ref_plot = ui.plotly({}).classes('w-full h-80')

                # Target Wafermap
                with ui.card().classes('flex-1'):
                    ui.label('Target').classes('font-bold')
                    self.target_plot = ui.plotly({}).classes('w-full h-80')

                # Diff Wafermap
                with ui.card().classes('flex-1'):
                    ui.label('Difference').classes('font-bold')
                    self.diff_plot = ui.plotly({}).classes('w-full h-80')

            # Statistics
            with ui.card().classes('w-full mt-2'):
                ui.label('Diff Statistics').classes('font-bold')
                self.stats_row = ui.row().classes('gap-8')
                with self.stats_row:
                    self.stat_mean = ui.label('Mean Diff: -')
                    self.stat_std = ui.label('Std Diff: -')
                    self.stat_min = ui.label('Min Diff: -')
                    self.stat_max = ui.label('Max Diff: -')

    def _calculate_diff(self) -> None:
        """Differenz berechnen und anzeigen."""
        ref_name = self.ref_select.value
        target_name = self.target_select.value
        param = self.param_select.value
        diff_type = self.diff_type.value

        if not all([ref_name, target_name, param]):
            ui.notify('Please select Reference, Target and Parameter', type='warning')
            return

        if ref_name not in self.app_state.loaded_files or target_name not in self.app_state.loaded_files:
            return

        ref_data = self.app_state.loaded_files[ref_name]
        target_data = self.app_state.loaded_files[target_name]

        ref_df = ref_data.dataframe
        target_df = target_data.dataframe

        if param not in ref_df.columns or param not in target_df.columns:
            ui.notify(f'Parameter {param} not found in both wafers', type='warning')
            return

        # Merge on coordinates
        ref_df = ref_df[['x', 'y', param]].copy()
        ref_df.columns = ['x', 'y', 'ref_val']
        target_df = target_df[['x', 'y', param]].copy()
        target_df.columns = ['x', 'y', 'target_val']

        merged = pd.merge(ref_df, target_df, on=['x', 'y'], how='inner')

        if len(merged) == 0:
            ui.notify('No matching coordinates found', type='warning')
            return

        # Calculate diff
        if diff_type == 'Absolute':
            merged['diff'] = merged['target_val'] - merged['ref_val']
        elif diff_type == 'Percentage':
            merged['diff'] = (merged['target_val'] - merged['ref_val']) / merged['ref_val'].abs() * 100
        else:  # Ratio
            merged['diff'] = merged['target_val'] / merged['ref_val']

        # Update plots
        self._update_plot(self.ref_plot, merged, 'ref_val', f"Reference - {ref_data.wafer_id}")
        self._update_plot(self.target_plot, merged, 'target_val', f"Target - {target_data.wafer_id}")
        self._update_plot(self.diff_plot, merged, 'diff', "Difference", colorscale=self.colorscale.value)

        # Update statistics
        diff_values = merged['diff'].dropna()
        self.stat_mean.text = f"Mean Diff: {diff_values.mean():.4f}"
        self.stat_std.text = f"Std Diff: {diff_values.std():.4f}"
        self.stat_min.text = f"Min Diff: {diff_values.min():.4f}"
        self.stat_max.text = f"Max Diff: {diff_values.max():.4f}"

    def _update_plot(self, plot_element, df: pd.DataFrame, value_col: str, title: str, colorscale: str = 'Viridis') -> None:
        """Einzelnen Plot aktualisieren."""
        fig = go.Figure(go.Scatter(
            x=df['x'],
            y=df['y'],
            mode='markers',
            marker=dict(
                color=df[value_col],
                colorscale=colorscale,
                size=8,
                colorbar=dict(title=value_col)
            ),
            text=[f"X:{x}, Y:{y}<br>{value_col}: {v:.4f}" for x, y, v in zip(df['x'], df['y'], df[value_col])],
            hoverinfo='text'
        ))

        fig.update_layout(
            title=title,
            xaxis_title="X",
            yaxis_title="Y",
            yaxis=dict(scaleanchor="x"),
            height=350,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        plot_element.update_figure(fig)

    def update_wafers(self, wafers: List[str]) -> None:
        """Wafer-Liste aktualisieren."""
        self.ref_select.options = wafers
        self.target_select.options = wafers
        if len(wafers) >= 2:
            self.ref_select.value = wafers[0]
            self.target_select.value = wafers[1]
        self.ref_select.update()
        self.target_select.update()

    def update_params(self, params: List[str]) -> None:
        """Parameter-Liste aktualisieren."""
        self.param_select.options = params
        if params:
            self.param_select.value = params[0]
        self.param_select.update()
