"""
Multi-Wafer Tab - Web Version.

Entspricht dem Multi-Wafer Tab in der Desktop-App.
"""

from nicegui import ui
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class MultiWaferTab:
    """
    Multi-Wafer Tab für Wafer-Vergleiche.

    Features:
    - Multi-Wafer Boxplot
    - Multi-Wafer Distribution
    - Wafer vs Wafer Scatter
    - Trend Analysis
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state
        self.container = None

        # Plots
        self.boxplot = None
        self.distribution_plot = None

    def build(self, parent: Any = None) -> None:
        """Tab UI aufbauen."""
        with ui.column().classes('w-full h-full p-2') as self.container:
            # Controls
            with ui.row().classes('gap-2 items-center mb-2'):
                ui.label('Parameter:')
                self.param_select = ui.select(options=[], label='Parameter').classes('w-64')

                ui.label('Plot Type:')
                self.plot_type = ui.select(
                    options=['Boxplot', 'Distribution', 'Trend'],
                    value='Boxplot',
                    on_change=self._on_plot_type_change
                ).classes('w-32')

                ui.button('Update', on_click=self._update_plot).props('dense')

            # Wafer Selection (Multi-Select)
            with ui.row().classes('gap-2 items-center mb-2'):
                ui.label('Wafers:')
                self.wafer_select = ui.select(
                    options=[],
                    multiple=True,
                    label='Select Wafers'
                ).classes('w-96')

            # Plot Area
            with ui.card().classes('w-full flex-1'):
                self.boxplot = ui.plotly({}).classes('w-full h-96')

    def _on_plot_type_change(self, e) -> None:
        """Plot-Typ geändert."""
        self._update_plot()

    def _update_plot(self) -> None:
        """Plot aktualisieren."""
        param = self.param_select.value
        wafers = self.wafer_select.value or []
        plot_type = self.plot_type.value

        if not param or not wafers:
            return

        if plot_type == 'Boxplot':
            self._create_boxplot(param, wafers)
        elif plot_type == 'Distribution':
            self._create_distribution(param, wafers)
        elif plot_type == 'Trend':
            self._create_trend(param, wafers)

    def _create_boxplot(self, param: str, wafers: List[str]) -> None:
        """Boxplot erstellen."""
        fig = go.Figure()

        for wafer_name in wafers:
            if wafer_name not in self.app_state.loaded_files:
                continue
            wafer_data = self.app_state.loaded_files[wafer_name]
            df = wafer_data.dataframe

            if param not in df.columns:
                continue

            values = df[param].dropna()
            if len(values) > 0:
                fig.add_trace(go.Box(
                    y=values,
                    name=wafer_data.wafer_id or wafer_name,
                    boxpoints='outliers'
                ))

        fig.update_layout(
            title=f"Boxplot - {param}",
            yaxis_title=param,
            height=450
        )

        self.boxplot.update_figure(fig)

    def _create_distribution(self, param: str, wafers: List[str]) -> None:
        """Distribution/Histogram erstellen."""
        fig = go.Figure()

        for wafer_name in wafers:
            if wafer_name not in self.app_state.loaded_files:
                continue
            wafer_data = self.app_state.loaded_files[wafer_name]
            df = wafer_data.dataframe

            if param not in df.columns:
                continue

            values = df[param].dropna()
            if len(values) > 0:
                fig.add_trace(go.Histogram(
                    x=values,
                    name=wafer_data.wafer_id or wafer_name,
                    opacity=0.7
                ))

        fig.update_layout(
            title=f"Distribution - {param}",
            xaxis_title=param,
            yaxis_title="Count",
            barmode='overlay',
            height=450
        )

        self.boxplot.update_figure(fig)

    def _create_trend(self, param: str, wafers: List[str]) -> None:
        """Trend über Wafer erstellen."""
        fig = go.Figure()

        means = []
        labels = []

        for wafer_name in wafers:
            if wafer_name not in self.app_state.loaded_files:
                continue
            wafer_data = self.app_state.loaded_files[wafer_name]
            df = wafer_data.dataframe

            if param not in df.columns:
                continue

            values = df[param].dropna()
            if len(values) > 0:
                means.append(values.mean())
                labels.append(wafer_data.wafer_id or wafer_name)

        fig.add_trace(go.Scatter(
            x=labels,
            y=means,
            mode='lines+markers',
            name='Mean'
        ))

        fig.update_layout(
            title=f"Trend - {param}",
            xaxis_title="Wafer",
            yaxis_title=f"Mean {param}",
            height=450
        )

        self.boxplot.update_figure(fig)

    def update_params(self, params: List[str]) -> None:
        """Parameter-Liste aktualisieren."""
        self.param_select.options = params
        if params:
            self.param_select.value = params[0]
        self.param_select.update()

    def update_wafers(self, wafers: List[str]) -> None:
        """Wafer-Liste aktualisieren."""
        self.wafer_select.options = wafers
        self.wafer_select.value = wafers  # Alle vorausgewählt
        self.wafer_select.update()
