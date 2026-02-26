"""
Statistics Tab Module for Data Octopus

Provides the StatisticsTab class for displaying statistical analysis
of wafer test data including basic stats, Cpk, yield, and distributions.

Usage:
    from src.stdf_analyzer.gui.statistics_tab import StatisticsTab
    stats_tab = StatisticsTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from src.stdf_analyzer.core.parameter_utils import simplify_param_name, extract_group_from_column
from src.stdf_analyzer.core.statistics_utils import (
    calculate_basic_stats,
    calculate_percentiles,
    calculate_cpk,
    calculate_yield,
    calculate_bin_summary,
    format_stat_value,
)


@dataclass
class StatisticsConfig:
    """Configuration for statistics display."""
    show_basic_stats: bool = True
    show_percentiles: bool = True
    show_cpk: bool = True
    show_yield: bool = True
    show_histogram: bool = True
    show_boxplot: bool = True
    percentile_list: List[float] = field(default_factory=lambda: [1, 5, 10, 25, 50, 75, 90, 95, 99])
    histogram_bins: int = 50


class StatisticsTab:
    """
    Statistics Tab for wafer data analysis.

    Displays:
    - Basic statistics (count, mean, std, min, max, median, range)
    - Percentiles (p1, p5, p10, p25, p50, p75, p90, p95, p99)
    - Cpk analysis (Cp, Cpk, Cpl, Cpu) if limits are provided
    - Yield analysis (pass/fail counts and percentages)
    - Histogram and boxplot visualizations
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_parameter_selected: Optional[Callable] = None):
        """
        Initialize the Statistics Tab.

        Args:
            parent_notebook: The parent ttk.Notebook widget
            tab_frame: The frame for this tab's content
            on_parameter_selected: Optional callback when a parameter is selected
        """
        self.parent_notebook = parent_notebook
        self.tab_frame = tab_frame
        self.on_parameter_selected = on_parameter_selected

        # State
        self.wafer_data: Optional[pd.DataFrame] = None
        self.wafer_id: str = ""
        self.test_parameters: Dict[str, str] = {}
        self.grouped_parameters: Dict[str, list] = {}
        self.test_limits: Dict[str, Dict[str, float]] = {}
        self.config = StatisticsConfig()

        # Current selection
        self.current_group: str = ""
        self.current_parameter: str = ""

        # UI references
        self.group_combo: Optional[ttk.Combobox] = None
        self.param_combo: Optional[ttk.Combobox] = None
        self.stats_tree: Optional[ttk.Treeview] = None
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.ax_hist: Optional[plt.Axes] = None
        self.ax_box: Optional[plt.Axes] = None

        # Create UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the statistics tab."""
        # Main container with left panel and right visualization
        main_paned = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Controls and statistics table
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=1)

        # Right panel: Visualizations
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        # === Left Panel ===
        self._create_control_panel(left_frame)
        self._create_stats_table(left_frame)

        # === Right Panel ===
        self._create_visualization_panel(right_frame)

    def _create_control_panel(self, parent: tk.Widget):
        """Create the control panel with dropdowns."""
        control_frame = ttk.LabelFrame(parent, text="Parameter Selection", padding=5)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Group selection
        group_frame = ttk.Frame(control_frame)
        group_frame.pack(fill=tk.X, pady=2)

        ttk.Label(group_frame, text="Group:").pack(side=tk.LEFT, padx=(0, 5))
        self.group_combo = ttk.Combobox(group_frame, state="readonly", width=25)
        self.group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)

        # Parameter selection
        param_frame = ttk.Frame(control_frame)
        param_frame.pack(fill=tk.X, pady=2)

        ttk.Label(param_frame, text="Parameter:").pack(side=tk.LEFT, padx=(0, 5))
        self.param_combo = ttk.Combobox(param_frame, state="readonly", width=25)
        self.param_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.param_combo.bind("<<ComboboxSelected>>", self._on_parameter_selected)

        # Limits display
        self.limits_label = ttk.Label(control_frame, text="Limits: N/A", foreground="gray")
        self.limits_label.pack(fill=tk.X, pady=2)

        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Display Options", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Checkboxes for display options
        self.show_histogram_var = tk.BooleanVar(value=True)
        self.show_boxplot_var = tk.BooleanVar(value=True)
        self.show_limits_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Show Histogram",
                       variable=self.show_histogram_var,
                       command=self._update_visualization).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Show Boxplot",
                       variable=self.show_boxplot_var,
                       command=self._update_visualization).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Show Limits",
                       variable=self.show_limits_var,
                       command=self._update_visualization).pack(anchor=tk.W)

    def _create_stats_table(self, parent: tk.Widget):
        """Create the statistics treeview table."""
        table_frame = ttk.LabelFrame(parent, text="Statistics", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(table_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.stats_tree = ttk.Treeview(
            table_frame,
            columns=("metric", "value"),
            show="headings",
            height=20,
            yscrollcommand=tree_scroll.set
        )
        self.stats_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.stats_tree.yview)

        # Configure columns
        self.stats_tree.heading("metric", text="Metric")
        self.stats_tree.heading("value", text="Value")
        self.stats_tree.column("metric", width=150, anchor=tk.W)
        self.stats_tree.column("value", width=150, anchor=tk.E)

        # Configure tags for styling
        self.stats_tree.tag_configure("header", background="#E3F2FD", font=("Arial", 9, "bold"))
        self.stats_tree.tag_configure("pass", foreground="#2E7D32")
        self.stats_tree.tag_configure("fail", foreground="#C62828")
        self.stats_tree.tag_configure("warning", foreground="#F57C00")

    def _create_visualization_panel(self, parent: tk.Widget):
        """Create the visualization panel with histogram and boxplot."""
        viz_frame = ttk.LabelFrame(parent, text="Visualization", padding=5)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor('white')

        # Create subplots
        self.ax_hist = self.figure.add_subplot(211)
        self.ax_box = self.figure.add_subplot(212)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

    def load_data(self, df: pd.DataFrame, wafer_id: str,
                  test_params: Dict[str, str],
                  grouped_params: Dict[str, list],
                  test_limits: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Load wafer data into the statistics tab.

        Args:
            df: DataFrame with wafer data
            wafer_id: Identifier for the wafer
            test_params: Dict mapping column names to display names
            grouped_params: Dict mapping group names to lists of parameters
            test_limits: Optional dict with LSL/USL for each parameter
        """
        self.wafer_data = df
        self.wafer_id = wafer_id
        self.test_parameters = test_params
        self.grouped_parameters = grouped_params
        self.test_limits = test_limits or {}

        # Update group dropdown
        groups = ["All Groups"] + sorted(grouped_params.keys())
        self.group_combo['values'] = groups
        if groups:
            self.group_combo.current(0)
            self._on_group_selected(None)

    def _on_group_selected(self, event):
        """Handle group selection change."""
        group = self.group_combo.get()
        self.current_group = group

        # Update parameter dropdown
        if group == "All Groups":
            params = list(self.test_parameters.keys())
        else:
            params = self.grouped_parameters.get(group, [])

        # Create display names
        param_display = []
        for p in params:
            display_name = self.test_parameters.get(p, simplify_param_name(p))
            param_display.append(f"{p} | {display_name}")

        self.param_combo['values'] = param_display
        if param_display:
            self.param_combo.current(0)
            self._on_parameter_selected(None)

    def _on_parameter_selected(self, event):
        """Handle parameter selection change."""
        selection = self.param_combo.get()
        if not selection or "|" not in selection:
            return

        param_col = selection.split("|")[0].strip()
        self.current_parameter = param_col

        # Update limits label
        if param_col in self.test_limits:
            limits = self.test_limits[param_col]
            lsl = limits.get('lsl', 'N/A')
            usl = limits.get('usl', 'N/A')
            self.limits_label.config(text=f"Limits: LSL={lsl}, USL={usl}", foreground="black")
        else:
            self.limits_label.config(text="Limits: N/A", foreground="gray")

        # Update statistics and visualization
        self._update_statistics()
        self._update_visualization()

        # Callback
        if self.on_parameter_selected:
            self.on_parameter_selected(param_col)

    def _update_statistics(self):
        """Update the statistics table."""
        if self.wafer_data is None or not self.current_parameter:
            return

        if self.current_parameter not in self.wafer_data.columns:
            return

        # Clear existing items
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        # Get values
        values = pd.to_numeric(self.wafer_data[self.current_parameter], errors='coerce').dropna().values

        if len(values) == 0:
            self.stats_tree.insert("", tk.END, values=("No Data", "N/A"))
            return

        # Basic Statistics
        self.stats_tree.insert("", tk.END, values=("─── Basic Statistics ───", ""), tags=("header",))

        basic_stats = calculate_basic_stats(values)
        self.stats_tree.insert("", tk.END, values=("Count", f"{basic_stats['count']:,}"))
        self.stats_tree.insert("", tk.END, values=("Mean", format_stat_value(basic_stats['mean'])))
        self.stats_tree.insert("", tk.END, values=("Std Dev", format_stat_value(basic_stats['std'])))
        self.stats_tree.insert("", tk.END, values=("Min", format_stat_value(basic_stats['min'])))
        self.stats_tree.insert("", tk.END, values=("Max", format_stat_value(basic_stats['max'])))
        self.stats_tree.insert("", tk.END, values=("Median", format_stat_value(basic_stats['median'])))
        self.stats_tree.insert("", tk.END, values=("Range", format_stat_value(basic_stats['range'])))

        # Percentiles
        self.stats_tree.insert("", tk.END, values=("─── Percentiles ───", ""), tags=("header",))

        percentiles = calculate_percentiles(values, self.config.percentile_list)
        for p in self.config.percentile_list:
            key = f"p{int(p)}"
            self.stats_tree.insert("", tk.END, values=(f"P{int(p)}", format_stat_value(percentiles.get(key, 0))))

        # Cpk Analysis (if limits available)
        if self.current_parameter in self.test_limits:
            limits = self.test_limits[self.current_parameter]
            lsl = limits.get('lsl')
            usl = limits.get('usl')

            if lsl is not None or usl is not None:
                self.stats_tree.insert("", tk.END, values=("─── Cpk Analysis ───", ""), tags=("header",))

                cpk_result = calculate_cpk(values, lsl, usl)

                # Cp
                cp = cpk_result.get('cp')
                if cp is not None:
                    tag = "pass" if cp >= 1.33 else ("warning" if cp >= 1.0 else "fail")
                    self.stats_tree.insert("", tk.END, values=("Cp", f"{cp:.3f}"), tags=(tag,))

                # Cpk
                cpk = cpk_result.get('cpk')
                if cpk is not None:
                    tag = "pass" if cpk >= 1.33 else ("warning" if cpk >= 1.0 else "fail")
                    self.stats_tree.insert("", tk.END, values=("Cpk", f"{cpk:.3f}"), tags=(tag,))

                # Cpl and Cpu
                if cpk_result.get('cpl') is not None:
                    self.stats_tree.insert("", tk.END, values=("Cpl", f"{cpk_result['cpl']:.3f}"))
                if cpk_result.get('cpu') is not None:
                    self.stats_tree.insert("", tk.END, values=("Cpu", f"{cpk_result['cpu']:.3f}"))

                # Yield Analysis
                self.stats_tree.insert("", tk.END, values=("─── Yield Analysis ───", ""), tags=("header",))

                yield_result = calculate_yield(values, lsl, usl)

                total = yield_result.get('total', 0)
                pass_count = yield_result.get('pass_count', 0)
                fail_count = yield_result.get('fail_count', 0)
                pass_pct = yield_result.get('pass_pct', 0)
                fail_pct = yield_result.get('fail_pct', 0)

                self.stats_tree.insert("", tk.END, values=("Total", f"{total:,}"))
                self.stats_tree.insert("", tk.END, values=("Pass", f"{pass_count:,} ({pass_pct:.2f}%)"), tags=("pass",))
                self.stats_tree.insert("", tk.END, values=("Fail", f"{fail_count:,} ({fail_pct:.2f}%)"), tags=("fail",))

                # Fail breakdown
                fail_low = yield_result.get('fail_low_count', 0)
                fail_high = yield_result.get('fail_high_count', 0)
                if fail_low > 0:
                    self.stats_tree.insert("", tk.END, values=("  Fail Low", f"{fail_low:,}"), tags=("fail",))
                if fail_high > 0:
                    self.stats_tree.insert("", tk.END, values=("  Fail High", f"{fail_high:,}"), tags=("fail",))

    def _update_visualization(self):
        """Update the histogram and boxplot visualizations."""
        if self.wafer_data is None or not self.current_parameter:
            return

        if self.current_parameter not in self.wafer_data.columns:
            return

        # Get values
        values = pd.to_numeric(self.wafer_data[self.current_parameter], errors='coerce').dropna().values

        if len(values) == 0:
            return

        # Clear axes
        self.ax_hist.clear()
        self.ax_box.clear()

        # Get limits
        lsl, usl = None, None
        if self.current_parameter in self.test_limits:
            limits = self.test_limits[self.current_parameter]
            lsl = limits.get('lsl')
            usl = limits.get('usl')

        # Display name
        display_name = self.test_parameters.get(self.current_parameter,
                                                 simplify_param_name(self.current_parameter))

        # === Histogram ===
        if self.show_histogram_var.get():
            basic_stats = calculate_basic_stats(values)

            # Plot histogram
            n, bins, patches = self.ax_hist.hist(
                values, bins=self.config.histogram_bins,
                density=True, alpha=0.7, color='#3498DB', edgecolor='white'
            )

            # Add mean and std lines
            self.ax_hist.axvline(basic_stats['mean'], color='#E74C3C', linestyle='-',
                               linewidth=2, label=f"Mean: {basic_stats['mean']:.4g}")
            self.ax_hist.axvline(basic_stats['mean'] - basic_stats['std'], color='#F39C12',
                               linestyle='--', linewidth=1.5, alpha=0.7, label=f"±1σ")
            self.ax_hist.axvline(basic_stats['mean'] + basic_stats['std'], color='#F39C12',
                               linestyle='--', linewidth=1.5, alpha=0.7)

            # Add limits if enabled
            if self.show_limits_var.get():
                if lsl is not None:
                    self.ax_hist.axvline(lsl, color='#C62828', linestyle='-', linewidth=2,
                                       label=f"LSL: {lsl:.4g}")
                if usl is not None:
                    self.ax_hist.axvline(usl, color='#C62828', linestyle='-', linewidth=2,
                                       label=f"USL: {usl:.4g}")

            self.ax_hist.set_xlabel(display_name, fontsize=10)
            self.ax_hist.set_ylabel("Density", fontsize=10)
            self.ax_hist.set_title(f"Histogram - {display_name}", fontsize=11, fontweight='bold')
            self.ax_hist.legend(fontsize=8, loc='upper right')
            self.ax_hist.grid(True, alpha=0.3)

        # === Boxplot ===
        if self.show_boxplot_var.get():
            bp = self.ax_box.boxplot(
                values, vert=False, patch_artist=True,
                boxprops=dict(facecolor='#3498DB', alpha=0.7),
                medianprops=dict(color='#E74C3C', linewidth=2),
                whiskerprops=dict(color='#2C3E50', linewidth=1.5),
                capprops=dict(color='#2C3E50', linewidth=1.5),
                flierprops=dict(marker='o', markerfacecolor='#95A5A6', markersize=4, alpha=0.6)
            )

            # Add limits if enabled
            if self.show_limits_var.get():
                if lsl is not None:
                    self.ax_box.axvline(lsl, color='#C62828', linestyle='-', linewidth=2,
                                      label=f"LSL: {lsl:.4g}")
                if usl is not None:
                    self.ax_box.axvline(usl, color='#C62828', linestyle='-', linewidth=2,
                                      label=f"USL: {usl:.4g}")

            self.ax_box.set_xlabel(display_name, fontsize=10)
            self.ax_box.set_title(f"Boxplot - {display_name}", fontsize=11, fontweight='bold')
            if lsl is not None or usl is not None:
                self.ax_box.legend(fontsize=8, loc='upper right')
            self.ax_box.grid(True, alpha=0.3, axis='x')

        self.figure.tight_layout()
        self.canvas.draw()

    def reset(self):
        """Reset the tab to initial state."""
        self.wafer_data = None
        self.wafer_id = ""
        self.test_parameters = {}
        self.grouped_parameters = {}
        self.test_limits = {}
        self.current_group = ""
        self.current_parameter = ""

        self.group_combo.set("")
        self.group_combo['values'] = []
        self.param_combo.set("")
        self.param_combo['values'] = []
        self.limits_label.config(text="Limits: N/A", foreground="gray")

        # Clear stats table
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        # Clear visualization
        self.ax_hist.clear()
        self.ax_box.clear()
        self.canvas.draw()

    def get_state(self) -> Dict[str, Any]:
        """Get current tab state for serialization."""
        return {
            'wafer_id': self.wafer_id,
            'current_group': self.current_group,
            'current_parameter': self.current_parameter,
            'show_histogram': self.show_histogram_var.get(),
            'show_boxplot': self.show_boxplot_var.get(),
            'show_limits': self.show_limits_var.get(),
        }

    def set_state(self, state: Dict[str, Any]):
        """Restore tab state from serialization."""
        self.show_histogram_var.set(state.get('show_histogram', True))
        self.show_boxplot_var.set(state.get('show_boxplot', True))
        self.show_limits_var.set(state.get('show_limits', True))

        # Note: group and parameter selection should be restored after load_data()
