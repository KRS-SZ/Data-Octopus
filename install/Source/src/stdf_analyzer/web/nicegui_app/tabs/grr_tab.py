"""
GRR Tab - Web Version.

Gage R&R (Repeatability & Reproducibility) Analysis.
"""

from nicegui import ui
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class GRRTab:
    """
    GRR (Gage R&R) Tab für Messsystem-Analyse.

    Features:
    - Repeatability Analysis
    - Reproducibility Analysis
    - %GRR Calculation
    - ndc (Number of Distinct Categories)
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state
        self.container = None

        # GRR Results
        self.grr_results: Dict[str, Any] = {}

    def build(self, parent: Any = None) -> None:
        """Tab UI aufbauen."""
        with ui.column().classes('w-full h-full p-2') as self.container:
            # Info Header
            with ui.card().classes('w-full bg-blue-50'):
                ui.label('GRR Analysis (Gage R&R)').classes('font-bold text-lg')
                ui.label('Requires multiple measurements of the same parts').classes('text-sm text-gray-600')

            # Controls
            with ui.row().classes('gap-4 items-center my-2'):
                ui.label('Parameter:')
                self.param_select = ui.select(options=[], label='Parameter').classes('w-64')

                ui.label('Method:')
                self.method_select = ui.select(
                    options=['ANOVA', 'X-bar/R', 'Range'],
                    value='ANOVA',
                    label='Method'
                ).classes('w-32')

                ui.button('Run GRR Analysis', on_click=self._run_grr).classes(
                    'bg-green-600 text-white'
                ).props('dense')

            # Wafer/Part Selection
            with ui.card().classes('w-full'):
                ui.label('Select Wafers (Parts/Runs)').classes('font-bold')
                self.wafer_select = ui.select(
                    options=[],
                    multiple=True,
                    label='Select Wafers for GRR'
                ).classes('w-full')

            # Results Area
            with ui.row().classes('w-full gap-2 mt-2'):
                # GRR Metrics Card
                with ui.card().classes('w-64'):
                    ui.label('GRR Results').classes('font-bold')
                    self.grr_value = ui.label('%GRR: -').classes('text-2xl')
                    self.ndc_value = ui.label('ndc: -').classes('text-xl')
                    self.repeatability = ui.label('Repeatability: -')
                    self.reproducibility = ui.label('Reproducibility: -')

                    # Result Indicator
                    self.result_indicator = ui.label('-').classes('text-lg font-bold mt-2')

                # Charts
                with ui.column().classes('flex-1'):
                    with ui.row().classes('w-full gap-2'):
                        # %GRR Chart
                        with ui.card().classes('flex-1'):
                            ui.label('%GRR').classes('font-bold text-sm')
                            self.grr_chart = ui.plotly({}).classes('w-full h-48')

                        # ndc Chart
                        with ui.card().classes('flex-1'):
                            ui.label('ndc').classes('font-bold text-sm')
                            self.ndc_chart = ui.plotly({}).classes('w-full h-48')

                        # Components Chart
                        with ui.card().classes('flex-1'):
                            ui.label('Repeatability + Reproducibility').classes('font-bold text-sm')
                            self.components_chart = ui.plotly({}).classes('w-full h-48')

            # Data Table
            with ui.card().classes('w-full mt-2'):
                ui.label('Detailed Results').classes('font-bold')
                self.results_table = ui.table(
                    columns=[
                        {'name': 'source', 'label': 'Source', 'field': 'source'},
                        {'name': 'variance', 'label': 'Variance', 'field': 'variance'},
                        {'name': 'std_dev', 'label': 'Std Dev', 'field': 'std_dev'},
                        {'name': 'pct_contribution', 'label': '% Contribution', 'field': 'pct_contribution'},
                    ],
                    rows=[]
                ).classes('w-full')

    def _run_grr(self) -> None:
        """GRR Analyse durchführen."""
        param = self.param_select.value
        wafers = self.wafer_select.value or []

        if not param or len(wafers) < 2:
            ui.notify('Select parameter and at least 2 wafers', type='warning')
            return

        # Collect data from wafers
        all_data = []
        for i, wafer_name in enumerate(wafers):
            if wafer_name not in self.app_state.loaded_files:
                continue
            wafer_data = self.app_state.loaded_files[wafer_name]
            df = wafer_data.dataframe

            if param not in df.columns:
                continue

            values = df[param].dropna().values
            for j, val in enumerate(values):
                all_data.append({
                    'operator': f'Run{i+1}',
                    'part': j,
                    'value': val
                })

        if len(all_data) == 0:
            ui.notify('No data found for analysis', type='warning')
            return

        grr_df = pd.DataFrame(all_data)

        # Simple GRR calculation
        # Repeatability: Variation within runs
        # Reproducibility: Variation between runs

        overall_mean = grr_df['value'].mean()
        overall_std = grr_df['value'].std()

        # Group by operator (run)
        run_means = grr_df.groupby('operator')['value'].mean()
        run_stds = grr_df.groupby('operator')['value'].std()

        repeatability = run_stds.mean()  # Average within-run variation
        reproducibility = run_means.std()  # Between-run variation

        # GRR
        grr_variance = repeatability**2 + reproducibility**2
        grr_std = np.sqrt(grr_variance)

        # %GRR (as percentage of tolerance or total variation)
        pct_grr = (grr_std / overall_std) * 100 if overall_std > 0 else 0

        # ndc (Number of Distinct Categories)
        part_std = grr_df.groupby('part')['value'].std().mean()
        ndc = 1.41 * (part_std / grr_std) if grr_std > 0 else 0

        # Update UI
        self.grr_value.text = f'%GRR: {pct_grr:.1f}%'
        self.ndc_value.text = f'ndc: {ndc:.1f}'
        self.repeatability.text = f'Repeatability: {repeatability:.4f}'
        self.reproducibility.text = f'Reproducibility: {reproducibility:.4f}'

        # Result indicator
        if pct_grr <= 10:
            self.result_indicator.text = '✅ EXCELLENT'
            self.result_indicator.classes(remove='text-yellow-600 text-red-600', add='text-green-600')
        elif pct_grr <= 30:
            self.result_indicator.text = '⚠️ ACCEPTABLE'
            self.result_indicator.classes(remove='text-green-600 text-red-600', add='text-yellow-600')
        else:
            self.result_indicator.text = '❌ NOT ACCEPTABLE'
            self.result_indicator.classes(remove='text-green-600 text-yellow-600', add='text-red-600')

        # Update charts
        self._update_grr_chart(pct_grr)
        self._update_ndc_chart(ndc)
        self._update_components_chart(repeatability, reproducibility)

        # Update table
        total_var = overall_std**2
        self.results_table.rows = [
            {'source': 'Total', 'variance': f'{total_var:.6f}', 'std_dev': f'{overall_std:.6f}', 'pct_contribution': '100%'},
            {'source': 'Repeatability', 'variance': f'{repeatability**2:.6f}', 'std_dev': f'{repeatability:.6f}',
             'pct_contribution': f'{(repeatability**2/total_var)*100:.1f}%' if total_var > 0 else '-'},
            {'source': 'Reproducibility', 'variance': f'{reproducibility**2:.6f}', 'std_dev': f'{reproducibility:.6f}',
             'pct_contribution': f'{(reproducibility**2/total_var)*100:.1f}%' if total_var > 0 else '-'},
            {'source': 'GRR', 'variance': f'{grr_variance:.6f}', 'std_dev': f'{grr_std:.6f}',
             'pct_contribution': f'{pct_grr:.1f}%'},
        ]
        self.results_table.update()

    def _update_grr_chart(self, pct_grr: float) -> None:
        """GRR Bar Chart."""
        fig = go.Figure(go.Bar(
            x=['%GRR'],
            y=[pct_grr],
            marker_color='green' if pct_grr <= 10 else ('yellow' if pct_grr <= 30 else 'red')
        ))
        fig.add_hline(y=10, line_dash="dash", line_color="green", annotation_text="10%")
        fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="30%")
        fig.update_layout(height=200, margin=dict(l=30, r=30, t=30, b=30), yaxis_title="%")
        self.grr_chart.update_figure(fig)

    def _update_ndc_chart(self, ndc: float) -> None:
        """ndc Bar Chart."""
        fig = go.Figure(go.Bar(
            x=['ndc'],
            y=[ndc],
            marker_color='green' if ndc >= 5 else 'red'
        ))
        fig.add_hline(y=5, line_dash="dash", line_color="green", annotation_text="ndc=5")
        fig.update_layout(height=200, margin=dict(l=30, r=30, t=30, b=30), yaxis_title="ndc")
        self.ndc_chart.update_figure(fig)

    def _update_components_chart(self, repeatability: float, reproducibility: float) -> None:
        """Stacked Bar Chart für Repeatability + Reproducibility."""
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Repeatability', x=['Components'], y=[repeatability], marker_color='blue'))
        fig.add_trace(go.Bar(name='Reproducibility', x=['Components'], y=[reproducibility], marker_color='orange'))
        fig.update_layout(barmode='stack', height=200, margin=dict(l=30, r=30, t=30, b=30), yaxis_title="Std Dev")
        self.components_chart.update_figure(fig)

    def update_wafers(self, wafers: List[str]) -> None:
        """Wafer-Liste aktualisieren."""
        self.wafer_select.options = wafers
        self.wafer_select.value = wafers
        self.wafer_select.update()

    def update_params(self, params: List[str]) -> None:
        """Parameter-Liste aktualisieren."""
        self.param_select.options = params
        if params:
            self.param_select.value = params[0]
        self.param_select.update()
