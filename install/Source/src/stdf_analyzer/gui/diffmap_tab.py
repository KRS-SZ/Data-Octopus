"""
Diffmap Tab Module for Data Octopus

Contains the DiffmapTab class that handles wafer difference map visualization.
Compares two wafers (reference vs comparison) and shows the difference.

Usage:
    from src.stdf_analyzer.gui.diffmap_tab import DiffmapTab
    diffmap_tab = DiffmapTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.colors import Normalize, LinearSegmentedColormap
import matplotlib.patches as mpatches
from typing import Optional, Dict, List, Any, Tuple

from src.stdf_analyzer.core.parameter_utils import (
    simplify_param_name,
    extract_group_from_column,
)
from src.stdf_analyzer.core.data_loader import (
    load_csv_file,
    detect_test_parameters,
    group_parameters,
)


class DiffmapTab:
    """
    Diffmap Tab - Wafer Difference Map Visualization.

    Features:
    - Load reference and comparison wafers (STDF or CSV)
    - Calculate difference between wafers
    - Visualize difference as heatmap
    - Parameter selection by group
    - Statistics display
    - Die info popup on click
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 load_stdf_func=None, load_csv_func=None, on_diffmap_updated=None):
        """
        Initialize the Diffmap Tab.

        Args:
            parent_notebook: Parent ttk.Notebook widget
            tab_frame: The frame for this tab (tab_diffmap)
            load_stdf_func: Function to load STDF files (from main)
            load_csv_func: Function to load CSV files (from main)
            on_diffmap_updated: Optional callback when diffmap is updated
        """
        self.parent = parent_notebook
        self.frame = tab_frame
        self.load_stdf_func = load_stdf_func
        self.load_csv_func = load_csv_func
        self.on_diffmap_updated = on_diffmap_updated

        # ============================================================
        # STATE VARIABLES
        # ============================================================
        self.reference_data: Optional[pd.DataFrame] = None
        self.reference_id: Optional[str] = None
        self.compare_data: Optional[pd.DataFrame] = None
        self.compare_id: Optional[str] = None
        self.result_data: Optional[pd.DataFrame] = None
        self.test_params: Dict[str, str] = {}
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.wafer_config: Optional[Dict] = None

        # UI references (will be set in _create_widgets)
        self.ref_label: Optional[tk.Label] = None
        self.comp_label: Optional[tk.Label] = None
        self.calc_btn: Optional[tk.Button] = None
        self.info_label: Optional[tk.Label] = None
        self.group_var: Optional[tk.StringVar] = None
        self.group_combo: Optional[ttk.Combobox] = None
        self.param_var: Optional[tk.StringVar] = None
        self.param_combo: Optional[ttk.Combobox] = None
        self.stats_text: Optional[tk.Text] = None
        self.figure: Optional[Figure] = None
        self.ax: Optional[plt.Axes] = None

        # Build UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the Diffmap tab."""
        # ============================================================
        # CONTROL FRAME (Top)
        # ============================================================
        control_frame = tk.Frame(self.frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Reference file section
        ref_frame = tk.LabelFrame(control_frame, text="Reference File",
                                   font=("Helvetica", 10, "bold"))
        ref_frame.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        ref_stdf_btn = tk.Button(
            ref_frame,
            text="Select Reference STDF",
            command=self._select_reference_stdf,
            font=("Helvetica", 10),
            bg="#4CAF50",
            fg="white"
        )
        ref_stdf_btn.pack(side=tk.LEFT, padx=5, pady=5)

        ref_csv_btn = tk.Button(
            ref_frame,
            text="Select Reference CSV",
            command=self._select_reference_csv,
            font=("Helvetica", 10),
            bg="#FF9800",
            fg="white"
        )
        ref_csv_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.ref_label = tk.Label(
            ref_frame,
            text="No file selected",
            font=("Helvetica", 9),
            fg="gray",
            width=30,
            anchor="w"
        )
        self.ref_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Comparison file section
        comp_frame = tk.LabelFrame(control_frame, text="Comparison File",
                                    font=("Helvetica", 10, "bold"))
        comp_frame.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        comp_stdf_btn = tk.Button(
            comp_frame,
            text="Select Comparison STDF",
            command=self._select_comparison_stdf,
            font=("Helvetica", 10),
            bg="#2196F3",
            fg="white"
        )
        comp_stdf_btn.pack(side=tk.LEFT, padx=5, pady=5)

        comp_csv_btn = tk.Button(
            comp_frame,
            text="Select Comparison CSV",
            command=self._select_comparison_csv,
            font=("Helvetica", 10),
            bg="#E91E63",
            fg="white"
        )
        comp_csv_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.comp_label = tk.Label(
            comp_frame,
            text="No file selected",
            font=("Helvetica", 9),
            fg="gray",
            width=30,
            anchor="w"
        )
        self.comp_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Calculate button
        self.calc_btn = tk.Button(
            control_frame,
            text="Calculate Diff",
            command=self._calculate_diffmap,
            font=("Helvetica", 11, "bold"),
            bg="#FF9800",
            fg="white",
            state=tk.DISABLED
        )
        self.calc_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # ============================================================
        # STATUS ROW
        # ============================================================
        status_row = tk.Frame(self.frame)
        status_row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        self.info_label = tk.Label(
            status_row,
            text="Load reference and comparison files to calculate difference",
            font=("Helvetica", 10),
            fg="gray"
        )
        self.info_label.pack(side=tk.LEFT, padx=5)

        # ============================================================
        # PARAMETER SELECTION ROW
        # ============================================================
        param_row = tk.Frame(self.frame)
        param_row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Group selection
        tk.Label(param_row, text="Group:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.group_var = tk.StringVar(value="All Groups")
        self.group_combo = ttk.Combobox(
            param_row,
            textvariable=self.group_var,
            values=["All Groups"],
            state="readonly",
            width=20
        )
        self.group_combo.pack(side=tk.LEFT, padx=5)
        self.group_combo.bind("<<ComboboxSelected>>", self._on_group_selected)

        # Parameter selection
        tk.Label(param_row, text="Parameter:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=5)
        self.param_var = tk.StringVar()
        self.param_combo = ttk.Combobox(
            param_row,
            textvariable=self.param_var,
            values=[],
            state="readonly",
            width=50
        )
        self.param_combo.pack(side=tk.LEFT, padx=5)
        self.param_combo.bind("<<ComboboxSelected>>", self._on_param_selected)

        # ============================================================
        # MAIN CONTENT AREA (Heatmap + Stats)
        # ============================================================
        content_frame = tk.Frame(self.frame)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left: Heatmap
        heatmap_frame = tk.LabelFrame(content_frame, text="Difference Map",
                                       font=("Helvetica", 10, "bold"))
        heatmap_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("No data loaded")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")

        self.canvas = FigureCanvasTkAgg(self.figure, heatmap_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self._on_heatmap_click)

        # Right: Statistics
        stats_frame = tk.LabelFrame(content_frame, text="Statistics",
                                     font=("Helvetica", 10, "bold"))
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        self.stats_text = tk.Text(stats_frame, width=35, height=20,
                                   font=("Courier", 9), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ============================================================
    # FILE SELECTION METHODS
    # ============================================================

    def _select_reference_stdf(self):
        """Select reference STDF file."""
        file_path = filedialog.askopenfilename(
            title="Select Reference STDF File",
            filetypes=[("STDF files", "*.stdf"), ("All files", "*.*")]
        )
        if file_path:
            self._load_reference(file_path, "stdf")

    def _select_reference_csv(self):
        """Select reference CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select Reference CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self._load_reference(file_path, "csv")

    def _select_comparison_stdf(self):
        """Select comparison STDF file."""
        file_path = filedialog.askopenfilename(
            title="Select Comparison STDF File",
            filetypes=[("STDF files", "*.stdf"), ("All files", "*.*")]
        )
        if file_path:
            self._load_comparison(file_path, "stdf")

    def _select_comparison_csv(self):
        """Select comparison CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select Comparison CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self._load_comparison(file_path, "csv")

    def _load_reference(self, file_path: str, file_type: str):
        """Load reference file."""
        try:
            if file_type == "stdf":
                # Use the STDF loader from main
                data, wafer_id = self.load_stdf_func(file_path)
            else:
                # Use the CSV loader from main
                data, wafer_id = self.load_csv_func(file_path)

            if data is not None:
                self.reference_data = data
                self.reference_id = wafer_id or os.path.basename(file_path)
                self.ref_label.config(text=self.reference_id[:30], fg="green")
                self._check_ready()
                self._update_info(f"Reference loaded: {len(data)} dies")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load reference: {e}")
            self._update_info(f"Error loading reference: {e}", "red")

    def _load_comparison(self, file_path: str, file_type: str):
        """Load comparison file."""
        try:
            if file_type == "stdf":
                data, wafer_id = self.load_stdf_func(file_path)
            else:
                data, wafer_id = self.load_csv_func(file_path)

            if data is not None:
                self.compare_data = data
                self.compare_id = wafer_id or os.path.basename(file_path)
                self.comp_label.config(text=self.compare_id[:30], fg="blue")
                self._check_ready()
                self._update_info(f"Comparison loaded: {len(data)} dies")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load comparison: {e}")
            self._update_info(f"Error loading comparison: {e}", "red")

    def _check_ready(self):
        """Check if both files are loaded and enable calculate button."""
        if self.reference_data is not None and self.compare_data is not None:
            self.calc_btn.config(state=tk.NORMAL)
            self._update_info("Ready to calculate difference", "green")
        else:
            self.calc_btn.config(state=tk.DISABLED)

    def _update_info(self, message: str, color: str = "gray"):
        """Update the info label."""
        self.info_label.config(text=message, fg=color)

    # ============================================================
    # CALCULATION METHODS
    # ============================================================

    def _calculate_diffmap(self):
        """Calculate difference between reference and comparison wafers."""
        if self.reference_data is None or self.compare_data is None:
            self._update_info("Load both files first", "red")
            return

        self._update_info("Calculating difference...", "blue")
        calc_start = time.time()

        ref_df = self.reference_data
        comp_df = self.compare_data

        # Merge on x, y coordinates
        merged = ref_df.merge(comp_df, on=['x', 'y'], suffixes=('_ref', '_comp'), how='inner')

        if len(merged) == 0:
            self._update_info("No matching die coordinates found!", "red")
            return

        # Build result dataframe
        result_data = {
            'x': merged['x'].values,
            'y': merged['y'].values
        }

        # Calculate difference for bin if present
        if 'bin_ref' in merged.columns and 'bin_comp' in merged.columns:
            result_data['bin'] = merged['bin_ref'].values - merged['bin_comp'].values

        # Calculate difference for all numeric parameters
        diff_count = 0
        grouped_params = {}

        for col in ref_df.columns:
            if col in ['x', 'y', 'bin']:
                continue

            col_ref = f"{col}_ref"
            col_comp = f"{col}_comp"

            if col_ref in merged.columns and col_comp in merged.columns:
                try:
                    ref_vals = pd.to_numeric(merged[col_ref], errors='coerce')
                    comp_vals = pd.to_numeric(merged[col_comp], errors='coerce')

                    if not ref_vals.isna().all() and not comp_vals.isna().all():
                        result_data[col] = ref_vals.values - comp_vals.values
                        diff_count += 1

                        # Group parameters
                        group = extract_group_from_column(col)
                        if group not in grouped_params:
                            grouped_params[group] = []
                        short_name = simplify_param_name(col)
                        grouped_params[group].append((col, short_name))
                except Exception:
                    pass

        self.result_data = pd.DataFrame(result_data)
        self.test_params = grouped_params

        calc_time = time.time() - calc_start
        self._update_info(f"Calculated {diff_count} parameter differences for {len(merged)} dies ({calc_time:.2f}s)", "green")

        # Update group combobox
        self._update_group_combobox()

        # Show first parameter
        if grouped_params:
            first_group = list(grouped_params.keys())[0]
            if grouped_params[first_group]:
                first_param = grouped_params[first_group][0][0]
                self.param_var.set(first_param)
                self._update_heatmap()

    def _update_group_combobox(self):
        """Update the group dropdown with available groups."""
        groups = ["All Groups"] + sorted(self.test_params.keys())
        self.group_combo['values'] = groups
        self.group_var.set("All Groups")
        self._update_param_combobox()

    def _update_param_combobox(self):
        """Update the parameter dropdown based on selected group."""
        group = self.group_var.get()

        if group == "All Groups":
            # Show all parameters
            params = []
            for g, p_list in self.test_params.items():
                for col, short_name in p_list:
                    params.append(col)
        else:
            # Show parameters for selected group
            params = [col for col, _ in self.test_params.get(group, [])]

        self.param_combo['values'] = params
        if params:
            self.param_var.set(params[0])

    def _on_group_selected(self, event=None):
        """Handle group selection change."""
        self._update_param_combobox()
        self._update_heatmap()

    def _on_param_selected(self, event=None):
        """Handle parameter selection change."""
        self._update_heatmap()

    # ============================================================
    # VISUALIZATION METHODS
    # ============================================================

    def _update_heatmap(self):
        """Update the difference heatmap display."""
        if self.result_data is None:
            return

        param = self.param_var.get()
        if not param or param not in self.result_data.columns:
            return

        self.ax.clear()

        df = self.result_data
        x_vals = df['x'].values
        y_vals = df['y'].values
        diff_vals = df[param].values

        # Remove NaN values
        mask = ~np.isnan(diff_vals)
        x_plot = x_vals[mask]
        y_plot = y_vals[mask]
        diff_plot = diff_vals[mask]

        if len(diff_plot) == 0:
            self.ax.set_title(f"No valid data for {simplify_param_name(param)}")
            self.canvas.draw()
            return

        # Create heatmap
        # Use diverging colormap (blue = negative, white = zero, red = positive)
        vmax = max(abs(np.nanmin(diff_plot)), abs(np.nanmax(diff_plot)))
        vmin = -vmax

        scatter = self.ax.scatter(
            x_plot, y_plot,
            c=diff_plot,
            cmap='RdBu_r',
            vmin=vmin, vmax=vmax,
            s=50, marker='s'
        )

        # Colorbar
        if hasattr(self, '_colorbar') and self._colorbar:
            self._colorbar.remove()
        self._colorbar = self.figure.colorbar(scatter, ax=self.ax, label='Difference')

        # Title and labels
        short_name = simplify_param_name(param)
        self.ax.set_title(f"Difference: {short_name}\n(Ref: {self.reference_id} - Comp: {self.compare_id})")
        self.ax.set_xlabel("X Coordinate")
        self.ax.set_ylabel("Y Coordinate")
        self.ax.set_aspect('equal')

        self.figure.tight_layout()
        self.canvas.draw()

        # Update statistics
        self._update_stats(diff_plot, short_name)

    def _update_stats(self, diff_values: np.ndarray, param_label: str):
        """Update the statistics display."""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)

        valid_vals = diff_values[~np.isnan(diff_values)]

        stats_text = f"""Parameter: {param_label}
{'='*35}

Reference:  {self.reference_id}
Comparison: {self.compare_id}

{'='*35}
DIFFERENCE STATISTICS
{'='*35}

Count:     {len(valid_vals):,}
Mean:      {np.mean(valid_vals):.6g}
Std Dev:   {np.std(valid_vals):.6g}
Min:       {np.min(valid_vals):.6g}
Max:       {np.max(valid_vals):.6g}
Median:    {np.median(valid_vals):.6g}

{'='*35}
PERCENTILES
{'='*35}

P1:        {np.percentile(valid_vals, 1):.6g}
P5:        {np.percentile(valid_vals, 5):.6g}
P25:       {np.percentile(valid_vals, 25):.6g}
P50:       {np.percentile(valid_vals, 50):.6g}
P75:       {np.percentile(valid_vals, 75):.6g}
P95:       {np.percentile(valid_vals, 95):.6g}
P99:       {np.percentile(valid_vals, 99):.6g}

{'='*35}
ZERO DIFFERENCE
{'='*35}

Exact Zero:   {np.sum(valid_vals == 0):,} ({100*np.sum(valid_vals == 0)/len(valid_vals):.1f}%)
|Diff| < 1%:  {np.sum(np.abs(valid_vals) < np.abs(np.mean(valid_vals))*0.01):,}
"""

        self.stats_text.insert('1.0', stats_text)
        self.stats_text.config(state=tk.DISABLED)

    def _on_heatmap_click(self, event):
        """Handle click on heatmap to show die info."""
        if event.inaxes != self.ax or self.result_data is None:
            return

        x_click = event.xdata
        y_click = event.ydata

        if x_click is None or y_click is None:
            return

        # Find closest die
        df = self.result_data
        distances = np.sqrt((df['x'] - x_click)**2 + (df['y'] - y_click)**2)
        closest_idx = distances.idxmin()

        die_x = df.loc[closest_idx, 'x']
        die_y = df.loc[closest_idx, 'y']

        param = self.param_var.get()
        if param and param in df.columns:
            diff_val = df.loc[closest_idx, param]
            self._update_info(f"Die ({die_x}, {die_y}): Diff = {diff_val:.6g}", "blue")

    # ============================================================
    # PUBLIC METHODS
    # ============================================================

    def reset(self):
        """Reset the tab to initial state."""
        self.reference_data = None
        self.reference_id = None
        self.compare_data = None
        self.compare_id = None
        self.result_data = None
        self.test_params = {}

        self.ref_label.config(text="No file selected", fg="gray")
        self.comp_label.config(text="No file selected", fg="gray")
        self.calc_btn.config(state=tk.DISABLED)
        self._update_info("Load reference and comparison files to calculate difference")

        self.ax.clear()
        self.ax.set_title("No data loaded")
        self.canvas.draw()

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.config(state=tk.DISABLED)

    def get_state(self) -> Dict:
        """Get current state for saving."""
        return {
            'reference_id': self.reference_id,
            'compare_id': self.compare_id,
            'selected_group': self.group_var.get() if self.group_var else None,
            'selected_param': self.param_var.get() if self.param_var else None,
        }

    def set_state(self, state: Dict):
        """Restore state from saved data."""
        if state.get('selected_group'):
            self.group_var.set(state['selected_group'])
        if state.get('selected_param'):
            self.param_var.set(state['selected_param'])
