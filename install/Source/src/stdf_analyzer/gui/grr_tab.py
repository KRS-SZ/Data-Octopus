"""
GRR Tab Module for Data Octopus

Contains the GRRTab class that handles Gage R&R (Repeatability and Reproducibility)
analysis for semiconductor test data.

Usage:
    from src.stdf_analyzer.gui.grr_tab import GRRTab
    grr_tab = GRRTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import Optional, Dict, List, Any, Tuple, Callable

from src.stdf_analyzer.core.parameter_utils import (
    simplify_param_name,
    extract_group_from_column,
)
from src.stdf_analyzer.core.statistics_utils import (
    calculate_grr,
    calculate_basic_stats,
    format_stat_value,
)


# GRR Thresholds
GRR_THRESHOLDS = {
    'excellent': 10,  # %GRR < 10% = Excellent
    'acceptable': 30,  # %GRR < 30% = Acceptable
    'ndc_min': 5,  # ndc >= 5 = Good
}


class GRRTab:
    """
    GRR Tab - Gage R&R Analysis.

    Features:
    - Load multiple wafers for repeatability analysis
    - Calculate GRR statistics per parameter
    - Visualize %GRR, ndc, Repeatability, Reproducibility
    - Support for standard GRR and PLM Pixel GRR
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_analysis_complete: Optional[Callable] = None):
        """
        Initialize the GRR Tab.

        Args:
            parent_notebook: Parent ttk.Notebook widget
            tab_frame: The frame for this tab
            on_analysis_complete: Optional callback when analysis is complete
        """
        self.parent = parent_notebook
        self.frame = tab_frame
        self.on_analysis_complete = on_analysis_complete

        # ============================================================
        # STATE VARIABLES
        # ============================================================
        self.wafer_data_list: List[pd.DataFrame] = []
        self.wafer_ids: List[str] = []
        self.grr_results: Dict[str, Dict] = {}  # param -> GRR results
        self.selected_parameter: Optional[str] = None
        self.test_parameters: Dict[str, str] = {}
        self.grouped_parameters: Dict[str, List] = {}

        # UI references
        self.wafer_listbox: Optional[tk.Listbox] = None
        self.group_var: Optional[tk.StringVar] = None
        self.group_combo: Optional[ttk.Combobox] = None
        self.param_var: Optional[tk.StringVar] = None
        self.param_combo: Optional[ttk.Combobox] = None
        self.results_text: Optional[tk.Text] = None
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None

        # Build UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the GRR tab."""
        # ============================================================
        # LEFT PANEL - Wafer Selection & Controls
        # ============================================================
        left_panel = tk.Frame(self.frame, width=300, bg='#f5f5f5')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)

        # Wafer Selection Section
        wafer_frame = tk.LabelFrame(left_panel, text="Loaded Wafers",
                                     font=("Helvetica", 10, "bold"))
        wafer_frame.pack(fill=tk.X, padx=5, pady=5)

        # Wafer Listbox
        listbox_frame = tk.Frame(wafer_frame)
        listbox_frame.pack(fill=tk.X, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.wafer_listbox = tk.Listbox(
            listbox_frame,
            font=("Consolas", 9),
            height=8,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set
        )
        self.wafer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.wafer_listbox.yview)

        # Wafer count label
        self.wafer_count_label = tk.Label(
            wafer_frame,
            text="0 wafers loaded",
            font=("Helvetica", 9),
            fg="gray"
        )
        self.wafer_count_label.pack(pady=2)

        # Buttons
        btn_frame = tk.Frame(wafer_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="Remove Selected",
            command=self._remove_selected_wafers,
            font=("Helvetica", 9)
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame,
            text="Clear All",
            command=self._clear_all_wafers,
            font=("Helvetica", 9)
        ).pack(side=tk.LEFT, padx=2)

        # Group Selection
        group_frame = tk.LabelFrame(left_panel, text="Group Selection",
                                     font=("Helvetica", 10, "bold"))
        group_frame.pack(fill=tk.X, padx=5, pady=5)

        self.group_var = tk.StringVar(value="All Groups")
        self.group_combo = ttk.Combobox(
            group_frame,
            textvariable=self.group_var,
            values=["All Groups"],
            state="readonly",
            width=30
        )
        self.group_combo.pack(fill=tk.X, padx=5, pady=5)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)

        # Parameter Selection
        param_frame = tk.LabelFrame(left_panel, text="Parameter Selection",
                                     font=("Helvetica", 10, "bold"))
        param_frame.pack(fill=tk.X, padx=5, pady=5)

        self.param_var = tk.StringVar()
        self.param_combo = ttk.Combobox(
            param_frame,
            textvariable=self.param_var,
            values=[],
            state="readonly",
            width=30
        )
        self.param_combo.pack(fill=tk.X, padx=5, pady=5)
        self.param_combo.bind("<<ComboboxSelected>>", self._on_param_selected)

        # Run Analysis Button
        tk.Button(
            left_panel,
            text="Run GRR Analysis",
            command=self._run_analysis,
            font=("Helvetica", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2
        ).pack(fill=tk.X, padx=5, pady=10)

        # Results Section
        results_frame = tk.LabelFrame(left_panel, text="GRR Results",
                                       font=("Helvetica", 10, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_frame, width=35, height=15,
                                     font=("Courier", 9), state=tk.DISABLED)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ============================================================
        # RIGHT PANEL - Charts
        # ============================================================
        right_panel = tk.Frame(self.frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Matplotlib Figure with 3 subplots
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.ax1 = self.figure.add_subplot(131)  # %GRR
        self.ax2 = self.figure.add_subplot(132)  # ndc
        self.ax3 = self.figure.add_subplot(133)  # Repeat/Reprod

        self._init_charts()

        self.canvas = FigureCanvasTkAgg(self.figure, right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _init_charts(self):
        """Initialize empty charts."""
        self.ax1.set_title("%GRR")
        self.ax1.set_ylabel("%GRR")
        self.ax1.axhline(y=10, color='g', linestyle='--', label='Excellent (10%)')
        self.ax1.axhline(y=30, color='orange', linestyle='--', label='Acceptable (30%)')

        self.ax2.set_title("ndc (Number of Distinct Categories)")
        self.ax2.set_ylabel("ndc")
        self.ax2.axhline(y=5, color='g', linestyle='--', label='Min (5)')

        self.ax3.set_title("Repeatability & Reproducibility")
        self.ax3.set_ylabel("Percentage (%)")

        self.figure.tight_layout()

    # ============================================================
    # WAFER MANAGEMENT
    # ============================================================

    def add_wafer(self, df: pd.DataFrame, wafer_id: str,
                  test_params: Optional[Dict] = None,
                  grouped_params: Optional[Dict] = None):
        """
        Add a wafer to the GRR analysis.

        Args:
            df: DataFrame with wafer data
            wafer_id: Wafer identifier
            test_params: Optional dict of test parameters
            grouped_params: Optional dict of grouped parameters
        """
        self.wafer_data_list.append(df)
        self.wafer_ids.append(wafer_id)

        # Update test parameters (merge from all wafers)
        if test_params:
            self.test_parameters.update(test_params)
        if grouped_params:
            for group, params in grouped_params.items():
                if group not in self.grouped_parameters:
                    self.grouped_parameters[group] = []
                for p in params:
                    if p not in self.grouped_parameters[group]:
                        self.grouped_parameters[group].append(p)

        # Update UI
        self._update_wafer_listbox()
        self._update_group_combobox()

    def _update_wafer_listbox(self):
        """Update the wafer listbox display."""
        self.wafer_listbox.delete(0, tk.END)
        for i, wafer_id in enumerate(self.wafer_ids):
            self.wafer_listbox.insert(tk.END, f"{i+1}. {wafer_id}")

        self.wafer_count_label.config(text=f"{len(self.wafer_ids)} wafers loaded")

    def _remove_selected_wafers(self):
        """Remove selected wafers from the list."""
        selection = list(self.wafer_listbox.curselection())
        for idx in reversed(selection):
            del self.wafer_data_list[idx]
            del self.wafer_ids[idx]

        self._update_wafer_listbox()
        self.grr_results.clear()

    def _clear_all_wafers(self):
        """Clear all wafers."""
        self.wafer_data_list.clear()
        self.wafer_ids.clear()
        self.grr_results.clear()
        self._update_wafer_listbox()
        self._clear_results()

    def _update_group_combobox(self):
        """Update the group dropdown."""
        groups = ["All Groups"] + sorted(self.grouped_parameters.keys())
        self.group_combo['values'] = groups
        self._update_param_combobox()

    def _update_param_combobox(self):
        """Update the parameter dropdown based on selected group."""
        group = self.group_var.get()

        if group == "All Groups":
            params = list(self.test_parameters.items())
        else:
            params = self.grouped_parameters.get(group, [])

        display_names = [simplify_param_name(p[0] if isinstance(p, tuple) else p)
                        for p in params]
        self.param_combo['values'] = display_names

        # Store mapping
        self._param_mapping = {}
        for i, p in enumerate(params):
            col = p[0] if isinstance(p, tuple) else p
            self._param_mapping[display_names[i]] = col

        if display_names:
            self.param_var.set(display_names[0])

    def _on_group_selected(self, event=None):
        """Handle group selection change."""
        self._update_param_combobox()

    def _on_param_selected(self, event=None):
        """Handle parameter selection change."""
        display_name = self.param_var.get()
        if hasattr(self, '_param_mapping') and display_name in self._param_mapping:
            self.selected_parameter = self._param_mapping[display_name]

    # ============================================================
    # GRR ANALYSIS
    # ============================================================

    def _run_analysis(self):
        """Run GRR analysis for selected parameter."""
        if len(self.wafer_data_list) < 2:
            messagebox.showwarning("Warning", "Need at least 2 wafers for GRR analysis")
            return

        display_name = self.param_var.get()
        if not display_name or not hasattr(self, '_param_mapping'):
            messagebox.showwarning("Warning", "Please select a parameter")
            return

        param_col = self._param_mapping.get(display_name)
        if not param_col:
            return

        # Collect measurements from all wafers
        measurements = []
        parts = []  # Die coordinates as "part"
        operators = []  # Wafer as "operator"

        for wafer_idx, (df, wafer_id) in enumerate(zip(self.wafer_data_list, self.wafer_ids)):
            if param_col not in df.columns:
                continue

            for _, row in df.iterrows():
                if 'x' in df.columns and 'y' in df.columns:
                    part_id = f"({row['x']},{row['y']})"
                else:
                    part_id = str(_)

                val = row[param_col]
                if pd.notna(val):
                    try:
                        measurements.append(float(val))
                        parts.append(part_id)
                        operators.append(wafer_id)
                    except (ValueError, TypeError):
                        pass

        if len(measurements) < 10:
            messagebox.showwarning("Warning", "Not enough data points for GRR analysis")
            return

        # Calculate GRR
        grr_result = calculate_grr(
            np.array(measurements),
            np.array(parts),
            np.array(operators)
        )

        # Store result
        self.grr_results[param_col] = grr_result

        # Update display
        self._update_results_display(param_col, grr_result)
        self._update_charts(param_col, grr_result)

        # Callback
        if self.on_analysis_complete:
            self.on_analysis_complete(param_col, grr_result)

    def _update_results_display(self, param_col: str, result: Dict):
        """Update the results text display."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        param_label = simplify_param_name(param_col)
        grr_pct = result.get('grr_pct', np.nan)
        ndc = result.get('ndc', np.nan)

        # Determine status
        if grr_pct < 10:
            status = "✅ EXCELLENT"
            status_color = "green"
        elif grr_pct < 30:
            status = "⚠️ ACCEPTABLE"
            status_color = "orange"
        else:
            status = "❌ UNACCEPTABLE"
            status_color = "red"

        ndc_status = "✅ Good" if ndc >= 5 else "❌ Poor"

        text = f"""Parameter: {param_label}
{'='*35}

%GRR:           {format_stat_value(grr_pct)}%
Status:         {status}

ndc:            {format_stat_value(ndc)}
ndc Status:     {ndc_status}

{'='*35}
COMPONENTS
{'='*35}

Repeatability:  {format_stat_value(result.get('repeatability', np.nan))}
Reproducibility:{format_stat_value(result.get('reproducibility', np.nan))}
Part Variation: {format_stat_value(result.get('part_variation', np.nan))}
Total Variation:{format_stat_value(result.get('total_variation', np.nan))}

{'='*35}
WAFERS ANALYZED: {len(self.wafer_ids)}
"""

        self.results_text.insert('1.0', text)
        self.results_text.config(state=tk.DISABLED)

    def _update_charts(self, param_col: str, result: Dict):
        """Update the GRR charts."""
        # Clear charts
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        param_label = simplify_param_name(param_col)

        # %GRR Bar
        grr_pct = result.get('grr_pct', 0)
        color = 'green' if grr_pct < 10 else ('orange' if grr_pct < 30 else 'red')
        self.ax1.bar([param_label], [grr_pct], color=color)
        self.ax1.axhline(y=10, color='g', linestyle='--', alpha=0.7)
        self.ax1.axhline(y=30, color='orange', linestyle='--', alpha=0.7)
        self.ax1.set_title("%GRR")
        self.ax1.set_ylabel("%GRR")
        self.ax1.set_ylim(0, max(grr_pct * 1.2, 35))

        # ndc Bar
        ndc = result.get('ndc', 0)
        ndc_color = 'green' if ndc >= 5 else 'red'
        self.ax2.bar([param_label], [ndc], color=ndc_color)
        self.ax2.axhline(y=5, color='g', linestyle='--', alpha=0.7)
        self.ax2.set_title("ndc")
        self.ax2.set_ylabel("ndc")
        self.ax2.set_ylim(0, max(ndc * 1.2, 6))

        # Repeatability & Reproducibility stacked bar
        total_var = result.get('total_variation', 1)
        repeat = result.get('repeatability', 0)
        reprod = result.get('reproducibility', 0)

        if total_var > 0:
            repeat_pct = 100 * (repeat**2) / (total_var**2)
            reprod_pct = 100 * (reprod**2) / (total_var**2)
        else:
            repeat_pct = 0
            reprod_pct = 0

        self.ax3.bar([param_label], [repeat_pct], label='Repeatability', color='#2196F3')
        self.ax3.bar([param_label], [reprod_pct], bottom=[repeat_pct],
                     label='Reproducibility', color='#FF9800')
        self.ax3.set_title("Repeat. & Reprod. (%)")
        self.ax3.set_ylabel("Percentage (%)")
        self.ax3.legend()
        self.ax3.set_ylim(0, 100)

        self.figure.tight_layout()
        self.canvas.draw()

    def _clear_results(self):
        """Clear results display."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', "No analysis run yet")
        self.results_text.config(state=tk.DISABLED)

        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self._init_charts()
        self.canvas.draw()

    # ============================================================
    # PUBLIC METHODS
    # ============================================================

    def reset(self):
        """Reset the tab to initial state."""
        self._clear_all_wafers()
        self.test_parameters.clear()
        self.grouped_parameters.clear()
        self.group_combo['values'] = ["All Groups"]
        self.group_var.set("All Groups")
        self.param_combo['values'] = []

    def get_results(self) -> Dict[str, Dict]:
        """Get all GRR results."""
        return self.grr_results.copy()

    def get_state(self) -> Dict:
        """Get current state for saving."""
        return {
            'wafer_ids': self.wafer_ids.copy(),
            'selected_group': self.group_var.get() if self.group_var else None,
            'selected_param': self.selected_parameter,
        }
