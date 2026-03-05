"""
Characteristic Curve Tab Module for Data Octopus

Provides the CharacCurveTab class for displaying X/Y parameter plots
with scatter, line, and combined visualizations.

Usage:
    from src.stdf_analyzer.gui.charac_curve_tab import CharacCurveTab
    curve_tab = CharacCurveTab(parent_notebook, tab_frame)
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
from src.stdf_analyzer.core.statistics_utils import calculate_basic_stats


@dataclass
class CurveConfig:
    """Configuration for characteristic curve display."""
    plot_type: str = "scatter"  # "scatter", "line", "scatter+line"
    show_limits: bool = True
    show_legend: bool = True
    show_grid: bool = True
    marker_size: int = 30
    line_width: float = 1.5
    color_per_wafer: bool = True


class CharacCurveTab:
    """
    Characteristic Curve Tab for wafer data analysis.

    Features:
    - X/Y parameter selection
    - Plot types: Scatter, Line, Scatter+Line
    - Multi-wafer support with color per wafer
    - Limit lines (LSL/USL) display
    - Interactive zoom and pan
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_plot_updated: Optional[Callable] = None):
        """
        Initialize the Characteristic Curve Tab.

        Args:
            parent_notebook: The parent ttk.Notebook widget
            tab_frame: The frame for this tab's content
            on_plot_updated: Optional callback when plot is updated
        """
        self.parent_notebook = parent_notebook
        self.tab_frame = tab_frame
        self.on_plot_updated = on_plot_updated

        # State - supports multiple wafers
        self.wafer_data_list: List[pd.DataFrame] = []
        self.wafer_ids: List[str] = []
        self.test_parameters: Dict[str, str] = {}
        self.grouped_parameters: Dict[str, list] = {}
        self.test_limits: Dict[str, Dict[str, float]] = {}
        self.config = CurveConfig()

        # Current selection
        self.current_group: str = ""
        self.current_x_param: str = ""
        self.current_y_param: str = ""

        # UI references
        self.group_combo: Optional[ttk.Combobox] = None
        self.x_param_combo: Optional[ttk.Combobox] = None
        self.y_param_combo: Optional[ttk.Combobox] = None
        self.plot_type_var: Optional[tk.StringVar] = None
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.ax: Optional[plt.Axes] = None

        # Colors for multiple wafers
        self.wafer_colors = [
            '#3498DB', '#E74C3C', '#2ECC71', '#9B59B6', '#F39C12',
            '#1ABC9C', '#E67E22', '#34495E', '#16A085', '#C0392B'
        ]

        # Create UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the characteristic curve tab."""
        # Main container with left panel and right visualization
        main_paned = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Controls
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)

        # Right panel: Visualization
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)

        # === Left Panel ===
        self._create_control_panel(left_frame)
        self._create_wafer_list(left_frame)

        # === Right Panel ===
        self._create_visualization_panel(right_frame)

    def _create_control_panel(self, parent: tk.Widget):
        """Create the control panel with parameter selection."""
        # Group selection
        group_frame = ttk.LabelFrame(parent, text="Group Selection", padding=5)
        group_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(group_frame, text="Group:").pack(anchor=tk.W)
        self.group_combo = ttk.Combobox(group_frame, state="readonly", width=30)
        self.group_combo.pack(fill=tk.X, pady=2)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)

        # X Parameter selection
        x_frame = ttk.LabelFrame(parent, text="X-Axis Parameter", padding=5)
        x_frame.pack(fill=tk.X, padx=5, pady=5)

        self.x_param_combo = ttk.Combobox(x_frame, state="readonly", width=30)
        self.x_param_combo.pack(fill=tk.X, pady=2)
        self.x_param_combo.bind("<<ComboboxSelected>>", self._on_parameter_changed)

        # X limits display
        self.x_limits_label = ttk.Label(x_frame, text="Limits: N/A", foreground="gray")
        self.x_limits_label.pack(anchor=tk.W)

        # Y Parameter selection
        y_frame = ttk.LabelFrame(parent, text="Y-Axis Parameter", padding=5)
        y_frame.pack(fill=tk.X, padx=5, pady=5)

        self.y_param_combo = ttk.Combobox(y_frame, state="readonly", width=30)
        self.y_param_combo.pack(fill=tk.X, pady=2)
        self.y_param_combo.bind("<<ComboboxSelected>>", self._on_parameter_changed)

        # Y limits display
        self.y_limits_label = ttk.Label(y_frame, text="Limits: N/A", foreground="gray")
        self.y_limits_label.pack(anchor=tk.W)

        # Plot options
        options_frame = ttk.LabelFrame(parent, text="Plot Options", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Plot type
        ttk.Label(options_frame, text="Plot Type:").pack(anchor=tk.W)
        self.plot_type_var = tk.StringVar(value="scatter")

        plot_types = [("Scatter", "scatter"), ("Line", "line"), ("Scatter + Line", "scatter+line")]
        for text, value in plot_types:
            ttk.Radiobutton(options_frame, text=text, variable=self.plot_type_var,
                           value=value, command=self._update_plot).pack(anchor=tk.W)

        # Checkboxes
        self.show_limits_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)
        self.show_grid_var = tk.BooleanVar(value=True)
        self.color_per_wafer_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Show Limits",
                       variable=self.show_limits_var,
                       command=self._update_plot).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Show Legend",
                       variable=self.show_legend_var,
                       command=self._update_plot).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Show Grid",
                       variable=self.show_grid_var,
                       command=self._update_plot).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Color per Wafer",
                       variable=self.color_per_wafer_var,
                       command=self._update_plot).pack(anchor=tk.W)

        # Update button
        ttk.Button(options_frame, text="Update Plot",
                  command=self._update_plot).pack(fill=tk.X, pady=5)

    def _create_wafer_list(self, parent: tk.Widget):
        """Create the wafer list for multi-wafer support."""
        wafer_frame = ttk.LabelFrame(parent, text="Loaded Wafers", padding=5)
        wafer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Listbox with scrollbar
        list_scroll = ttk.Scrollbar(wafer_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.wafer_listbox = tk.Listbox(wafer_frame, height=8, selectmode=tk.MULTIPLE,
                                        yscrollcommand=list_scroll.set)
        self.wafer_listbox.pack(fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.wafer_listbox.yview)

        self.wafer_listbox.bind("<<ListboxSelect>>", lambda e: self._update_plot())

        # Buttons
        btn_frame = ttk.Frame(wafer_frame)
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="Select All",
                  command=self._select_all_wafers).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear",
                  command=self._clear_wafer_selection).pack(side=tk.LEFT, padx=2)

    def _create_visualization_panel(self, parent: tk.Widget):
        """Create the visualization panel with the plot."""
        viz_frame = ttk.LabelFrame(parent, text="Characteristic Curve", padding=5)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 7), dpi=100)
        self.figure.patch.set_facecolor('white')

        # Create axes
        self.ax = self.figure.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

    def add_wafer(self, df: pd.DataFrame, wafer_id: str,
                  test_params: Dict[str, str],
                  grouped_params: Dict[str, list],
                  test_limits: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Add a wafer to the characteristic curve tab.

        Args:
            df: DataFrame with wafer data
            wafer_id: Identifier for the wafer
            test_params: Dict mapping column names to display names
            grouped_params: Dict mapping group names to lists of parameters
            test_limits: Optional dict with LSL/USL for each parameter
        """
        self.wafer_data_list.append(df)
        self.wafer_ids.append(wafer_id)

        # Update parameters (merge with existing)
        self.test_parameters.update(test_params)
        for group, params in grouped_params.items():
            if group in self.grouped_parameters:
                self.grouped_parameters[group] = list(set(self.grouped_parameters[group] + params))
            else:
                self.grouped_parameters[group] = params

        if test_limits:
            self.test_limits.update(test_limits)

        # Update wafer listbox
        color_idx = len(self.wafer_ids) - 1
        color = self.wafer_colors[color_idx % len(self.wafer_colors)]
        self.wafer_listbox.insert(tk.END, f"● {wafer_id}")
        self.wafer_listbox.itemconfig(tk.END, fg=color)
        self.wafer_listbox.selection_set(tk.END)

        # Update dropdowns if this is the first wafer
        if len(self.wafer_data_list) == 1:
            groups = ["All Groups"] + sorted(self.grouped_parameters.keys())
            self.group_combo['values'] = groups
            if groups:
                self.group_combo.current(0)
                self._on_group_selected(None)

    def load_data(self, df: pd.DataFrame, wafer_id: str,
                  test_params: Dict[str, str],
                  grouped_params: Dict[str, list],
                  test_limits: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Load wafer data (clears existing and adds new).

        Args:
            df: DataFrame with wafer data
            wafer_id: Identifier for the wafer
            test_params: Dict mapping column names to display names
            grouped_params: Dict mapping group names to lists of parameters
            test_limits: Optional dict with LSL/USL for each parameter
        """
        self.reset()
        self.add_wafer(df, wafer_id, test_params, grouped_params, test_limits)

    def _on_group_selected(self, event):
        """Handle group selection change."""
        group = self.group_combo.get()
        self.current_group = group

        # Update parameter dropdowns
        if group == "All Groups":
            params = list(self.test_parameters.keys())
        else:
            params = self.grouped_parameters.get(group, [])

        # Create display names
        param_display = []
        for p in params:
            display_name = self.test_parameters.get(p, simplify_param_name(p))
            param_display.append(f"{p} | {display_name}")

        self.x_param_combo['values'] = param_display
        self.y_param_combo['values'] = param_display

        if param_display:
            self.x_param_combo.current(0)
            if len(param_display) > 1:
                self.y_param_combo.current(1)
            else:
                self.y_param_combo.current(0)
            self._on_parameter_changed(None)

    def _on_parameter_changed(self, event):
        """Handle parameter selection change."""
        # Get X parameter
        x_selection = self.x_param_combo.get()
        if x_selection and "|" in x_selection:
            self.current_x_param = x_selection.split("|")[0].strip()
            self._update_limits_label(self.current_x_param, self.x_limits_label)

        # Get Y parameter
        y_selection = self.y_param_combo.get()
        if y_selection and "|" in y_selection:
            self.current_y_param = y_selection.split("|")[0].strip()
            self._update_limits_label(self.current_y_param, self.y_limits_label)

        # Update plot
        self._update_plot()

    def _update_limits_label(self, param: str, label: ttk.Label):
        """Update limits label for a parameter."""
        if param in self.test_limits:
            limits = self.test_limits[param]
            lsl = limits.get('lsl', 'N/A')
            usl = limits.get('usl', 'N/A')
            label.config(text=f"Limits: LSL={lsl}, USL={usl}", foreground="black")
        else:
            label.config(text="Limits: N/A", foreground="gray")

    def _select_all_wafers(self):
        """Select all wafers in the listbox."""
        self.wafer_listbox.selection_set(0, tk.END)
        self._update_plot()

    def _clear_wafer_selection(self):
        """Clear wafer selection."""
        self.wafer_listbox.selection_clear(0, tk.END)
        self._update_plot()

    def _get_selected_wafer_indices(self) -> List[int]:
        """Get indices of selected wafers."""
        return list(self.wafer_listbox.curselection())

    def _update_plot(self):
        """Update the characteristic curve plot."""
        if not self.wafer_data_list or not self.current_x_param or not self.current_y_param:
            return

        # Get selected wafer indices
        selected_indices = self._get_selected_wafer_indices()
        if not selected_indices:
            selected_indices = list(range(len(self.wafer_data_list)))

        # Clear axes
        self.ax.clear()

        # Get plot settings
        plot_type = self.plot_type_var.get()
        show_limits = self.show_limits_var.get()
        show_legend = self.show_legend_var.get()
        show_grid = self.show_grid_var.get()
        color_per_wafer = self.color_per_wafer_var.get()

        # Get display names
        x_display = self.test_parameters.get(self.current_x_param,
                                              simplify_param_name(self.current_x_param))
        y_display = self.test_parameters.get(self.current_y_param,
                                              simplify_param_name(self.current_y_param))

        # Plot each selected wafer
        for idx in selected_indices:
            df = self.wafer_data_list[idx]
            wafer_id = self.wafer_ids[idx]
            color = self.wafer_colors[idx % len(self.wafer_colors)] if color_per_wafer else '#3498DB'

            # Get X and Y values
            if self.current_x_param not in df.columns or self.current_y_param not in df.columns:
                continue

            x_vals = pd.to_numeric(df[self.current_x_param], errors='coerce')
            y_vals = pd.to_numeric(df[self.current_y_param], errors='coerce')

            # Remove NaN pairs
            mask = ~(x_vals.isna() | y_vals.isna())
            x_vals = x_vals[mask].values
            y_vals = y_vals[mask].values

            if len(x_vals) == 0:
                continue

            # Sort by X for line plots
            sort_idx = np.argsort(x_vals)
            x_sorted = x_vals[sort_idx]
            y_sorted = y_vals[sort_idx]

            label = wafer_id if color_per_wafer else None

            # Plot based on type
            if plot_type == "scatter":
                self.ax.scatter(x_vals, y_vals, c=color, s=30, alpha=0.7, label=label)
            elif plot_type == "line":
                self.ax.plot(x_sorted, y_sorted, c=color, linewidth=1.5, alpha=0.8, label=label)
            elif plot_type == "scatter+line":
                self.ax.scatter(x_vals, y_vals, c=color, s=20, alpha=0.5)
                self.ax.plot(x_sorted, y_sorted, c=color, linewidth=1.5, alpha=0.8, label=label)

        # Add limit lines
        if show_limits:
            # X limits
            if self.current_x_param in self.test_limits:
                limits = self.test_limits[self.current_x_param]
                if 'lsl' in limits and limits['lsl'] is not None:
                    self.ax.axvline(limits['lsl'], color='#C62828', linestyle='--', linewidth=1.5,
                                   alpha=0.7, label=f"X LSL: {limits['lsl']:.4g}")
                if 'usl' in limits and limits['usl'] is not None:
                    self.ax.axvline(limits['usl'], color='#C62828', linestyle='--', linewidth=1.5,
                                   alpha=0.7, label=f"X USL: {limits['usl']:.4g}")

            # Y limits
            if self.current_y_param in self.test_limits:
                limits = self.test_limits[self.current_y_param]
                if 'lsl' in limits and limits['lsl'] is not None:
                    self.ax.axhline(limits['lsl'], color='#1565C0', linestyle='--', linewidth=1.5,
                                   alpha=0.7, label=f"Y LSL: {limits['lsl']:.4g}")
                if 'usl' in limits and limits['usl'] is not None:
                    self.ax.axhline(limits['usl'], color='#1565C0', linestyle='--', linewidth=1.5,
                                   alpha=0.7, label=f"Y USL: {limits['usl']:.4g}")

        # Styling
        self.ax.set_xlabel(x_display, fontsize=11)
        self.ax.set_ylabel(y_display, fontsize=11)
        self.ax.set_title(f"{y_display} vs {x_display}", fontsize=12, fontweight='bold')

        if show_grid:
            self.ax.grid(True, alpha=0.3)

        if show_legend and (color_per_wafer or show_limits):
            self.ax.legend(fontsize=8, loc='best')

        self.ax.set_facecolor('#FAFAFA')

        self.figure.tight_layout()
        self.canvas.draw()

        # Callback
        if self.on_plot_updated:
            self.on_plot_updated()

    def reset(self):
        """Reset the tab to initial state."""
        self.wafer_data_list = []
        self.wafer_ids = []
        self.test_parameters = {}
        self.grouped_parameters = {}
        self.test_limits = {}
        self.current_group = ""
        self.current_x_param = ""
        self.current_y_param = ""

        self.group_combo.set("")
        self.group_combo['values'] = []
        self.x_param_combo.set("")
        self.x_param_combo['values'] = []
        self.y_param_combo.set("")
        self.y_param_combo['values'] = []

        self.x_limits_label.config(text="Limits: N/A", foreground="gray")
        self.y_limits_label.config(text="Limits: N/A", foreground="gray")

        self.wafer_listbox.delete(0, tk.END)

        # Clear visualization
        self.ax.clear()
        self.canvas.draw()

    def get_state(self) -> Dict[str, Any]:
        """Get current tab state for serialization."""
        return {
            'wafer_ids': self.wafer_ids.copy(),
            'current_group': self.current_group,
            'current_x_param': self.current_x_param,
            'current_y_param': self.current_y_param,
            'plot_type': self.plot_type_var.get(),
            'show_limits': self.show_limits_var.get(),
            'show_legend': self.show_legend_var.get(),
            'show_grid': self.show_grid_var.get(),
            'color_per_wafer': self.color_per_wafer_var.get(),
            'selected_wafers': self._get_selected_wafer_indices(),
        }

    def set_state(self, state: Dict[str, Any]):
        """Restore tab state from serialization."""
        self.plot_type_var.set(state.get('plot_type', 'scatter'))
        self.show_limits_var.set(state.get('show_limits', True))
        self.show_legend_var.set(state.get('show_legend', True))
        self.show_grid_var.set(state.get('show_grid', True))
        self.color_per_wafer_var.set(state.get('color_per_wafer', True))
