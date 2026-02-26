"""
Wafer Tab Module for Data Octopus

Contains the WaferTab class that handles single wafer visualization
with heatmap, binmap, parameter selection, and die info display.

Usage:
    from src.stdf_analyzer.gui.wafer_tab import WaferTab
    wafer_tab = WaferTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from typing import Optional, Dict, List, Any, Tuple, Callable

from src.stdf_analyzer.core.parameter_utils import (
    simplify_param_name,
    extract_group_from_column,
)
from src.stdf_analyzer.core.binning import get_bin_colormap, BIN_COLORS
from src.stdf_analyzer.core.wafermap_utils import (
    WaferConfig,
    calculate_wafer_center,
    calculate_die_dimensions,
    get_wafer_bounds,
    find_die_at_position,
    transform_coordinates,
)
from src.stdf_analyzer.core.statistics_utils import (
    calculate_basic_stats,
    calculate_percentiles,
)


class WaferTab:
    """
    Wafer Tab - Single Wafer Heatmap Visualization.
    
    Features:
    - Load wafer data from STDF or CSV
    - Heatmap visualization of test parameters
    - Binmap visualization (HardBin/SoftBin)
    - Group and parameter selection
    - Die selection and info display
    - Statistics panel
    - Notch orientation support
    """
    
    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_data_loaded_callback: Optional[Callable] = None):
        """
        Initialize the Wafer Tab.
        
        Args:
            parent_notebook: Parent ttk.Notebook widget
            tab_frame: The frame for this tab (tab6 / tab_wafer)
            on_data_loaded_callback: Optional callback when data is loaded
        """
        self.parent = parent_notebook
        self.frame = tab_frame
        self.on_data_loaded = on_data_loaded_callback
        
        # ============================================================
        # STATE VARIABLES
        # ============================================================
        self.wafer_data: Optional[pd.DataFrame] = None
        self.wafer_id: Optional[str] = None
        self.wafer_config: WaferConfig = WaferConfig()
        self.test_parameters: Dict[str, str] = {}  # column -> display_name
        self.grouped_parameters: Dict[str, List[Tuple[str, str]]] = {}  # group -> [(col, name)]
        self.test_limits: Dict[str, Dict] = {}  # column -> {lo_limit, hi_limit}
        
        # Selection state
        self.selected_die_idx: Optional[int] = None
        self.selected_die_coords: Optional[Tuple[float, float]] = None
        self.selection_rect: Optional[Rectangle] = None
        
        # UI state
        self.current_param: Optional[str] = None
        self.current_group: str = "All Groups"
        self.display_mode: str = "heatmap"  # "heatmap", "binmap"
        
        # UI references
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.figure: Optional[Figure] = None
        self.ax: Optional[plt.Axes] = None
        self.colorbar = None
        self.group_var: Optional[tk.StringVar] = None
        self.group_combo: Optional[ttk.Combobox] = None
        self.param_var: Optional[tk.StringVar] = None
        self.param_combo: Optional[ttk.Combobox] = None
        self.stats_text: Optional[tk.Text] = None
        self.die_info_label: Optional[tk.Label] = None
        self.wafer_info_label: Optional[tk.Label] = None
        
        # Build UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets for the Wafer tab."""
        # ============================================================
        # LEFT PANEL - Controls
        # ============================================================
        left_panel = tk.Frame(self.frame, width=280, bg='#f5f5f5')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)
        
        # Wafer Info Section
        info_frame = tk.LabelFrame(left_panel, text="Wafer Info",
                                    font=("Helvetica", 10, "bold"))
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.wafer_info_label = tk.Label(
            info_frame,
            text="No wafer loaded",
            font=("Helvetica", 9),
            fg="gray",
            justify=tk.LEFT,
            anchor="w"
        )
        self.wafer_info_label.pack(fill=tk.X, padx=5, pady=5)
        
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
        
        # Display Mode Buttons
        mode_frame = tk.LabelFrame(left_panel, text="Display Mode",
                                    font=("Helvetica", 10, "bold"))
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = tk.Frame(mode_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.heatmap_btn = tk.Button(
            btn_frame,
            text="Heatmap",
            command=lambda: self._set_display_mode("heatmap"),
            font=("Helvetica", 9),
            bg="#4CAF50",
            fg="white",
            width=10
        )
        self.heatmap_btn.pack(side=tk.LEFT, padx=2)
        
        self.binmap_btn = tk.Button(
            btn_frame,
            text="Binmap",
            command=lambda: self._set_display_mode("binmap"),
            font=("Helvetica", 9),
            width=10
        )
        self.binmap_btn.pack(side=tk.LEFT, padx=2)
        
        # Notch Orientation
        notch_frame = tk.LabelFrame(left_panel, text="Notch Orientation",
                                     font=("Helvetica", 10, "bold"))
        notch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.notch_var = tk.StringVar(value="down")
        notch_options = [("Down ▼", "down"), ("Up ▲", "up"), 
                        ("Left ◄", "left"), ("Right ►", "right")]
        
        for text, value in notch_options:
            rb = tk.Radiobutton(
                notch_frame,
                text=text,
                variable=self.notch_var,
                value=value,
                command=self._on_notch_changed
            )
            rb.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Die Info Section
        die_frame = tk.LabelFrame(left_panel, text="Selected Die",
                                   font=("Helvetica", 10, "bold"))
        die_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.die_info_label = tk.Label(
            die_frame,
            text="Click on a die to see info",
            font=("Courier", 9),
            fg="gray",
            justify=tk.LEFT,
            anchor="w"
        )
        self.die_info_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Statistics Section
        stats_frame = tk.LabelFrame(left_panel, text="Statistics",
                                     font=("Helvetica", 10, "bold"))
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.stats_text = tk.Text(stats_frame, width=30, height=12,
                                   font=("Courier", 8), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ============================================================
        # RIGHT PANEL - Heatmap Display
        # ============================================================
        right_panel = tk.Frame(self.frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Matplotlib Figure
        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("No data loaded")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_aspect('equal')
        
        self.canvas = FigureCanvasTkAgg(self.figure, right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Navigation toolbar
        toolbar_frame = tk.Frame(right_panel)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # Connect click event
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
    
    # ============================================================
    # DATA LOADING
    # ============================================================
    
    def load_data(self, df: pd.DataFrame, wafer_id: str = "Unknown",
                  test_params: Optional[Dict] = None,
                  grouped_params: Optional[Dict] = None,
                  test_limits: Optional[Dict] = None):
        """
        Load wafer data into the tab.
        
        Args:
            df: DataFrame with x, y, bin, and parameter columns
            wafer_id: Wafer identifier
            test_params: Dict mapping column names to display names
            grouped_params: Dict mapping group names to parameter lists
            test_limits: Dict mapping column names to limit dicts
        """
        self.wafer_data = df
        self.wafer_id = wafer_id
        self.test_parameters = test_params or {}
        self.grouped_parameters = grouped_params or {}
        self.test_limits = test_limits or {}
        
        # Update UI
        self._update_wafer_info()
        self._update_group_combobox()
        self._update_heatmap()
        
        # Callback
        if self.on_data_loaded:
            self.on_data_loaded(df, wafer_id)
    
    def _update_wafer_info(self):
        """Update the wafer info display."""
        if self.wafer_data is None:
            self.wafer_info_label.config(text="No wafer loaded", fg="gray")
            return
        
        df = self.wafer_data
        die_count = len(df)
        
        # Calculate bounds
        x_min, x_max = df['x'].min(), df['x'].max()
        y_min, y_max = df['y'].min(), df['y'].max()
        
        # Bin info
        bin_info = ""
        if 'bin' in df.columns:
            unique_bins = df['bin'].nunique()
            bin_info = f"\nBins: {unique_bins} unique"
        
        info_text = f"""Wafer: {self.wafer_id}
Dies: {die_count:,}
X: {x_min} to {x_max}
Y: {y_min} to {y_max}
Params: {len(self.test_parameters)}{bin_info}"""
        
        self.wafer_info_label.config(text=info_text, fg="black")
    
    def _update_group_combobox(self):
        """Update the group dropdown with available groups."""
        groups = ["All Groups", "Binning"] + sorted(self.grouped_parameters.keys())
        self.group_combo['values'] = groups
        self.group_var.set("All Groups")
        self._update_param_combobox()
    
    def _update_param_combobox(self):
        """Update the parameter dropdown based on selected group."""
        group = self.group_var.get()
        
        if group == "All Groups":
            # Show all parameters
            params = [(col, name) for col, name in self.test_parameters.items()]
        elif group == "Binning":
            # Show bin columns
            params = []
            if self.wafer_data is not None:
                if 'bin' in self.wafer_data.columns:
                    params.append(('bin', 'HardBin'))
                if 'sbin' in self.wafer_data.columns:
                    params.append(('sbin', 'SoftBin'))
        else:
            # Show parameters for selected group
            params = self.grouped_parameters.get(group, [])
        
        # Sort by display name
        params_sorted = sorted(params, key=lambda x: x[1])
        
        # Update combobox
        display_names = [name for _, name in params_sorted]
        self.param_combo['values'] = display_names
        
        # Store mapping for lookup
        self._param_mapping = {name: col for col, name in params_sorted}
        
        if display_names:
            self.param_var.set(display_names[0])
            self.current_param = params_sorted[0][0]
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def _on_group_selected(self, event=None):
        """Handle group selection change."""
        self.current_group = self.group_var.get()
        self._update_param_combobox()
        self._update_heatmap()
    
    def _on_param_selected(self, event=None):
        """Handle parameter selection change."""
        display_name = self.param_var.get()
        if hasattr(self, '_param_mapping') and display_name in self._param_mapping:
            self.current_param = self._param_mapping[display_name]
            self._update_heatmap()
    
    def _on_notch_changed(self):
        """Handle notch orientation change."""
        self.wafer_config.notch_orientation = self.notch_var.get()
        self._update_heatmap()
    
    def _set_display_mode(self, mode: str):
        """Set display mode (heatmap or binmap)."""
        self.display_mode = mode
        
        # Update button colors
        if mode == "heatmap":
            self.heatmap_btn.config(bg="#4CAF50", fg="white")
            self.binmap_btn.config(bg="SystemButtonFace", fg="black")
        else:
            self.heatmap_btn.config(bg="SystemButtonFace", fg="black")
            self.binmap_btn.config(bg="#2196F3", fg="white")
        
        self._update_heatmap()
    
    def _on_canvas_click(self, event):
        """Handle click on heatmap canvas."""
        if event.inaxes != self.ax or self.wafer_data is None:
            return
        
        click_x = event.xdata
        click_y = event.ydata
        
        if click_x is None or click_y is None:
            return
        
        # Find closest die
        die_idx = find_die_at_position(self.wafer_data, click_x, click_y)
        
        if die_idx is not None:
            self.selected_die_idx = die_idx
            self.selected_die_coords = (
                self.wafer_data.loc[die_idx, 'x'],
                self.wafer_data.loc[die_idx, 'y']
            )
            self._update_die_info()
            self._draw_selection_rect()
    
    # ============================================================
    # VISUALIZATION
    # ============================================================
    
    def _update_heatmap(self):
        """Update the heatmap display."""
        if self.wafer_data is None:
            return
        
        self.ax.clear()
        df = self.wafer_data
        
        x_vals = df['x'].values
        y_vals = df['y'].values
        
        # Get values based on display mode
        if self.display_mode == "binmap":
            if 'bin' in df.columns:
                values = df['bin'].values
                title = f"Binmap - {self.wafer_id}"
                cmap = get_bin_colormap()
            else:
                self.ax.set_title("No bin data available")
                self.canvas.draw()
                return
        else:
            # Heatmap mode
            if self.current_param and self.current_param in df.columns:
                values = pd.to_numeric(df[self.current_param], errors='coerce').values
                param_label = simplify_param_name(self.current_param)
                title = f"{param_label} - {self.wafer_id}"
                cmap = 'viridis'
            else:
                self.ax.set_title("Select a parameter")
                self.canvas.draw()
                return
        
        # Remove NaN values for plotting
        mask = ~np.isnan(values)
        x_plot = x_vals[mask]
        y_plot = y_vals[mask]
        values_plot = values[mask]
        
        if len(values_plot) == 0:
            self.ax.set_title("No valid data")
            self.canvas.draw()
            return
        
        # Calculate die size for scatter marker
        die_w, die_h = calculate_die_dimensions(df)
        marker_size = min(die_w, die_h) * 15  # Adjust multiplier as needed
        
        # Create scatter plot
        scatter = self.ax.scatter(
            x_plot, y_plot,
            c=values_plot,
            cmap=cmap,
            s=marker_size,
            marker='s'
        )
        
        # Colorbar
        if self.colorbar:
            self.colorbar.remove()
        self.colorbar = self.figure.colorbar(scatter, ax=self.ax)
        
        # Title and labels
        self.ax.set_title(title)
        self.ax.set_xlabel("X Coordinate")
        self.ax.set_ylabel("Y Coordinate")
        self.ax.set_aspect('equal')
        
        # Set bounds with margin
        bounds = get_wafer_bounds(df, margin=0.5)
        self.ax.set_xlim(bounds['x_min'], bounds['x_max'])
        self.ax.set_ylim(bounds['y_min'], bounds['y_max'])
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        # Update statistics
        self._update_statistics(values_plot)
        
        # Redraw selection if exists
        if self.selected_die_coords:
            self._draw_selection_rect()
    
    def _draw_selection_rect(self):
        """Draw selection rectangle around selected die."""
        if self.selected_die_coords is None or self.wafer_data is None:
            return
        
        # Remove old rectangle
        if self.selection_rect:
            self.selection_rect.remove()
            self.selection_rect = None
        
        x, y = self.selected_die_coords
        die_w, die_h = calculate_die_dimensions(self.wafer_data)
        
        # Draw rectangle
        self.selection_rect = Rectangle(
            (x - die_w/2, y - die_h/2),
            die_w, die_h,
            fill=False,
            edgecolor='red',
            linewidth=2
        )
        self.ax.add_patch(self.selection_rect)
        self.canvas.draw()
    
    def _update_die_info(self):
        """Update the die info display."""
        if self.selected_die_idx is None or self.wafer_data is None:
            self.die_info_label.config(text="Click on a die to see info", fg="gray")
            return
        
        df = self.wafer_data
        row = df.loc[self.selected_die_idx]
        
        x = row['x']
        y = row['y']
        
        info_lines = [f"Die ({x}, {y})"]
        
        # Add bin info
        if 'bin' in df.columns:
            info_lines.append(f"HardBin: {row['bin']}")
        if 'sbin' in df.columns:
            info_lines.append(f"SoftBin: {row['sbin']}")
        
        # Add current parameter value
        if self.current_param and self.current_param in df.columns:
            val = row[self.current_param]
            param_label = simplify_param_name(self.current_param)
            info_lines.append(f"{param_label}: {val:.6g}")
        
        self.die_info_label.config(text="\n".join(info_lines), fg="black")
    
    def _update_statistics(self, values: np.ndarray):
        """Update the statistics display."""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        
        valid = values[~np.isnan(values)]
        
        if len(valid) == 0:
            self.stats_text.insert('1.0', "No valid data")
            self.stats_text.config(state=tk.DISABLED)
            return
        
        # Calculate statistics
        stats = calculate_basic_stats(valid)
        percentiles = calculate_percentiles(valid, [1, 5, 25, 50, 75, 95, 99])
        
        stats_text = f"""Count:  {stats['count']:,}
Mean:   {stats['mean']:.6g}
Std:    {stats['std']:.6g}
Min:    {stats['min']:.6g}
Max:    {stats['max']:.6g}
Median: {stats['median']:.6g}
Range:  {stats['range']:.6g}

Percentiles:
P1:     {percentiles['p1']:.6g}
P5:     {percentiles['p5']:.6g}
P25:    {percentiles['p25']:.6g}
P50:    {percentiles['p50']:.6g}
P75:    {percentiles['p75']:.6g}
P95:    {percentiles['p95']:.6g}
P99:    {percentiles['p99']:.6g}"""
        
        self.stats_text.insert('1.0', stats_text)
        self.stats_text.config(state=tk.DISABLED)
    
    # ============================================================
    # PUBLIC METHODS
    # ============================================================
    
    def reset(self):
        """Reset the tab to initial state."""
        self.wafer_data = None
        self.wafer_id = None
        self.test_parameters = {}
        self.grouped_parameters = {}
        self.test_limits = {}
        self.selected_die_idx = None
        self.selected_die_coords = None
        
        self.wafer_info_label.config(text="No wafer loaded", fg="gray")
        self.die_info_label.config(text="Click on a die to see info", fg="gray")
        self.group_combo['values'] = ["All Groups"]
        self.group_var.set("All Groups")
        self.param_combo['values'] = []
        
        self.ax.clear()
        self.ax.set_title("No data loaded")
        self.canvas.draw()
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.config(state=tk.DISABLED)
    
    def get_selected_parameter(self) -> Optional[str]:
        """Get the currently selected parameter column name."""
        return self.current_param
    
    def get_wafer_data(self) -> Optional[pd.DataFrame]:
        """Get the loaded wafer data."""
        return self.wafer_data
    
    def get_state(self) -> Dict:
        """Get current state for saving."""
        return {
            'wafer_id': self.wafer_id,
            'selected_group': self.group_var.get() if self.group_var else None,
            'selected_param': self.current_param,
            'display_mode': self.display_mode,
            'notch_orientation': self.notch_var.get() if self.notch_var else "down",
        }
    
    def set_state(self, state: Dict):
        """Restore state from saved data."""
        if state.get('selected_group'):
            self.group_var.set(state['selected_group'])
            self._update_param_combobox()
        if state.get('display_mode'):
            self._set_display_mode(state['display_mode'])
        if state.get('notch_orientation'):
            self.notch_var.set(state['notch_orientation'])
            self._on_notch_changed()
