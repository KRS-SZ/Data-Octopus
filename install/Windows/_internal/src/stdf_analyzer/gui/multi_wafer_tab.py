"""
Multi-Wafer Tab Module for Data Octopus

Contains the MultiWaferTab class that handles comparison of multiple wafers.

Usage:
    from src.stdf_analyzer.gui.multi_wafer_tab import MultiWaferTab
    multi_wafer_tab = MultiWaferTab(parent_notebook, tab_frame)
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
    calculate_basic_stats,
    calculate_percentiles,
)


class MultiWaferTab:
    """
    Multi-Wafer Tab - Compare multiple wafers.

    Features:
    - Load and display multiple wafers
    - Side-by-side heatmap comparison
    - Boxplot comparison across wafers
    - Distribution overlay
    - Statistics table
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_wafer_selected: Optional[Callable] = None):
        """
        Initialize the Multi-Wafer Tab.

        Args:
            parent_notebook: Parent ttk.Notebook widget
            tab_frame: The frame for this tab
            on_wafer_selected: Optional callback when a wafer is selected
        """
        self.parent = parent_notebook
        self.frame = tab_frame
        self.on_wafer_selected = on_wafer_selected

        # ============================================================
        # STATE VARIABLES
        # ============================================================
        self.wafer_data_list: List[pd.DataFrame] = []
        self.wafer_ids: List[str] = []
        self.selected_wafer_indices: List[int] = []
        self.test_parameters: Dict[str, str] = {}
        self.grouped_parameters: Dict[str, List] = {}
        self.selected_parameter: Optional[str] = None
        self.display_mode: str = "heatmap"  # "heatmap", "boxplot", "distribution"

        # UI references
        self.wafer_listbox: Optional[tk.Listbox] = None
        self.group_var: Optional[tk.StringVar] = None
        self.group_combo: Optional[ttk.Combobox] = None
        self.param_var: Optional[tk.StringVar] = None
        self.param_combo: Optional[ttk.Combobox] = None
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.stats_text: Optional[tk.Text] = None

        # Build UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the Multi-Wafer tab."""
        # ============================================================
        # LEFT PANEL - Wafer Selection & Controls
        # ============================================================
        left_panel = tk.Frame(self.frame, width=280, bg='#f5f5f5')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)

        # Wafer Selection Section
        wafer_frame = tk.LabelFrame(left_panel, text="Loaded Wafers",
                                     font=("Helvetica", 10, "bold"))
        wafer_frame.pack(fill=tk.X, padx=5, pady=5)

        # Wafer Listbox with checkboxes simulation
        listbox_frame = tk.Frame(wafer_frame)
        listbox_frame.pack(fill=tk.X, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.wafer_listbox = tk.Listbox(
            listbox_frame,
            font=("Consolas", 9),
            height=10,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set
        )
        self.wafer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.wafer_listbox.yview)
        self.wafer_listbox.bind('<<ListboxSelect>>', self._on_wafer_selection_changed)

        # Wafer count label
        self.wafer_count_label = tk.Label(
            wafer_frame,
            text="0 wafers loaded, 0 selected",
            font=("Helvetica", 9),
            fg="gray"
        )
        self.wafer_count_label.pack(pady=2)

        # Selection buttons
        sel_btn_frame = tk.Frame(wafer_frame)
        sel_btn_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Button(
            sel_btn_frame,
            text="Select All",
            command=self._select_all_wafers,
            font=("Helvetica", 9),
            width=10
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            sel_btn_frame,
            text="Clear",
            command=self._clear_selection,
            font=("Helvetica", 9),
            width=10
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

        # Display Mode
        mode_frame = tk.LabelFrame(left_panel, text="Display Mode",
                                    font=("Helvetica", 10, "bold"))
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = tk.Frame(mode_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.heatmap_btn = tk.Button(
            btn_frame,
            text="Heatmaps",
            command=lambda: self._set_display_mode("heatmap"),
            font=("Helvetica", 9),
            bg="#4CAF50",
            fg="white",
            width=8
        )
        self.heatmap_btn.pack(side=tk.LEFT, padx=2)

        self.boxplot_btn = tk.Button(
            btn_frame,
            text="Boxplot",
            command=lambda: self._set_display_mode("boxplot"),
            font=("Helvetica", 9),
            width=8
        )
        self.boxplot_btn.pack(side=tk.LEFT, padx=2)

        self.dist_btn = tk.Button(
            btn_frame,
            text="Distribution",
            command=lambda: self._set_display_mode("distribution"),
            font=("Helvetica", 9),
            width=8
        )
        self.dist_btn.pack(side=tk.LEFT, padx=2)

        # Statistics Section
        stats_frame = tk.LabelFrame(left_panel, text="Statistics",
                                     font=("Helvetica", 10, "bold"))
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.stats_text = tk.Text(stats_frame, width=35, height=12,
                                   font=("Courier", 8), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ============================================================
        # RIGHT PANEL - Visualization
        # ============================================================
        right_panel = tk.Frame(self.frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Matplotlib Figure
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ============================================================
    # WAFER MANAGEMENT
    # ============================================================

    def add_wafer(self, df: pd.DataFrame, wafer_id: str,
                  test_params: Optional[Dict] = None,
                  grouped_params: Optional[Dict] = None):
        """Add a wafer to the comparison."""
        self.wafer_data_list.append(df)
        self.wafer_ids.append(wafer_id)

        # Update parameters
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
        """Update the wafer listbox."""
        self.wafer_listbox.delete(0, tk.END)
        for i, wafer_id in enumerate(self.wafer_ids):
            prefix = "☑" if i in self.selected_wafer_indices else "☐"
            self.wafer_listbox.insert(tk.END, f"{prefix} {i+1}. {wafer_id}")

        count = len(self.wafer_ids)
        sel_count = len(self.selected_wafer_indices)
        self.wafer_count_label.config(text=f"{count} wafers loaded, {sel_count} selected")

    def _on_wafer_selection_changed(self, event=None):
        """Handle wafer selection change."""
        selection = list(self.wafer_listbox.curselection())
        self.selected_wafer_indices = selection
        self._update_wafer_listbox()
        self._update_display()

        if self.on_wafer_selected and selection:
            self.on_wafer_selected(selection)

    def _select_all_wafers(self):
        """Select all wafers."""
        self.selected_wafer_indices = list(range(len(self.wafer_ids)))
        self._update_wafer_listbox()
        self._update_display()

    def _clear_selection(self):
        """Clear wafer selection."""
        self.selected_wafer_indices = []
        self._update_wafer_listbox()
        self._update_display()

    def _update_group_combobox(self):
        """Update the group dropdown."""
        groups = ["All Groups"] + sorted(self.grouped_parameters.keys())
        self.group_combo['values'] = groups
        self._update_param_combobox()

    def _update_param_combobox(self):
        """Update the parameter dropdown."""
        group = self.group_var.get()

        if group == "All Groups":
            params = list(self.test_parameters.items())
        else:
            params = self.grouped_parameters.get(group, [])

        display_names = [simplify_param_name(p[0] if isinstance(p, tuple) else p)
                        for p in params]
        self.param_combo['values'] = display_names

        self._param_mapping = {}
        for i, p in enumerate(params):
            col = p[0] if isinstance(p, tuple) else p
            self._param_mapping[display_names[i]] = col

        if display_names:
            self.param_var.set(display_names[0])
            self.selected_parameter = self._param_mapping.get(display_names[0])

    def _on_group_selected(self, event=None):
        """Handle group selection change."""
        self._update_param_combobox()
        self._update_display()

    def _on_param_selected(self, event=None):
        """Handle parameter selection change."""
        display_name = self.param_var.get()
        if hasattr(self, '_param_mapping') and display_name in self._param_mapping:
            self.selected_parameter = self._param_mapping[display_name]
            self._update_display()

    def _set_display_mode(self, mode: str):
        """Set display mode."""
        self.display_mode = mode

        # Update button colors
        default_bg = "SystemButtonFace"
        self.heatmap_btn.config(bg=default_bg, fg="black")
        self.boxplot_btn.config(bg=default_bg, fg="black")
        self.dist_btn.config(bg=default_bg, fg="black")

        if mode == "heatmap":
            self.heatmap_btn.config(bg="#4CAF50", fg="white")
        elif mode == "boxplot":
            self.boxplot_btn.config(bg="#2196F3", fg="white")
        else:
            self.dist_btn.config(bg="#FF9800", fg="white")

        self._update_display()

    # ============================================================
    # VISUALIZATION
    # ============================================================

    def _update_display(self):
        """Update the visualization based on current settings."""
        self.figure.clear()

        if not self.selected_wafer_indices or not self.selected_parameter:
            ax = self.figure.add_subplot(111)
            ax.set_title("Select wafers and a parameter")
            ax.text(0.5, 0.5, "No data to display", ha='center', va='center',
                   fontsize=14, color='gray')
            self.canvas.draw()
            return

        if self.display_mode == "heatmap":
            self._draw_heatmaps()
        elif self.display_mode == "boxplot":
            self._draw_boxplot()
        else:
            self._draw_distribution()

        self._update_statistics()

    def _draw_heatmaps(self):
        """Draw side-by-side heatmaps for selected wafers."""
        n_wafers = len(self.selected_wafer_indices)
        if n_wafers == 0:
            return

        # Determine grid layout
        cols = min(n_wafers, 4)
        rows = (n_wafers + cols - 1) // cols

        param_col = self.selected_parameter
        param_label = simplify_param_name(param_col)

        # Get global min/max for consistent color scale
        all_values = []
        for idx in self.selected_wafer_indices:
            df = self.wafer_data_list[idx]
            if param_col in df.columns:
                vals = pd.to_numeric(df[param_col], errors='coerce').dropna().values
                all_values.extend(vals)

        if not all_values:
            return

        vmin, vmax = np.nanmin(all_values), np.nanmax(all_values)

        # Create subplots
        for i, idx in enumerate(self.selected_wafer_indices):
            ax = self.figure.add_subplot(rows, cols, i + 1)
            df = self.wafer_data_list[idx]
            wafer_id = self.wafer_ids[idx]

            if param_col not in df.columns:
                ax.set_title(f"{wafer_id}\n(no data)")
                continue

            x = df['x'].values
            y = df['y'].values
            values = pd.to_numeric(df[param_col], errors='coerce').values

            scatter = ax.scatter(x, y, c=values, cmap='viridis',
                               vmin=vmin, vmax=vmax, s=20, marker='s')
            ax.set_title(f"{wafer_id}")
            ax.set_aspect('equal')
            ax.set_xlabel("X")
            ax.set_ylabel("Y")

        # Add colorbar
        self.figure.colorbar(scatter, ax=self.figure.axes, label=param_label)
        self.figure.suptitle(f"Multi-Wafer Comparison: {param_label}", fontsize=12)
        self.figure.tight_layout()
        self.canvas.draw()

    def _draw_boxplot(self):
        """Draw boxplot comparison across wafers."""
        ax = self.figure.add_subplot(111)
        param_col = self.selected_parameter
        param_label = simplify_param_name(param_col)

        data = []
        labels = []

        for idx in self.selected_wafer_indices:
            df = self.wafer_data_list[idx]
            wafer_id = self.wafer_ids[idx]

            if param_col in df.columns:
                vals = pd.to_numeric(df[param_col], errors='coerce').dropna().values
                if len(vals) > 0:
                    data.append(vals)
                    labels.append(wafer_id[:15])  # Truncate long names

        if not data:
            ax.set_title("No valid data for boxplot")
            self.canvas.draw()
            return

        bp = ax.boxplot(data, labels=labels, patch_artist=True)

        # Color boxes
        colors = plt.cm.tab10.colors
        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.7)

        ax.set_title(f"Boxplot: {param_label}")
        ax.set_ylabel(param_label)
        ax.set_xlabel("Wafer")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        self.figure.tight_layout()
        self.canvas.draw()

    def _draw_distribution(self):
        """Draw overlaid distribution plots."""
        ax = self.figure.add_subplot(111)
        param_col = self.selected_parameter
        param_label = simplify_param_name(param_col)

        colors = plt.cm.tab10.colors

        for i, idx in enumerate(self.selected_wafer_indices):
            df = self.wafer_data_list[idx]
            wafer_id = self.wafer_ids[idx]

            if param_col in df.columns:
                vals = pd.to_numeric(df[param_col], errors='coerce').dropna().values
                if len(vals) > 0:
                    ax.hist(vals, bins=50, alpha=0.5, label=wafer_id[:15],
                           color=colors[i % len(colors)], density=True)

        ax.set_title(f"Distribution: {param_label}")
        ax.set_xlabel(param_label)
        ax.set_ylabel("Density")
        ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()

    def _update_statistics(self):
        """Update the statistics display."""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)

        if not self.selected_wafer_indices or not self.selected_parameter:
            self.stats_text.insert('1.0', "No data selected")
            self.stats_text.config(state=tk.DISABLED)
            return

        param_col = self.selected_parameter
        param_label = simplify_param_name(param_col)

        text = f"Parameter: {param_label}\n{'='*35}\n\n"
        text += f"{'Wafer':<15} {'Mean':>10} {'Std':>10}\n"
        text += "-" * 35 + "\n"

        for idx in self.selected_wafer_indices:
            df = self.wafer_data_list[idx]
            wafer_id = self.wafer_ids[idx][:15]

            if param_col in df.columns:
                vals = pd.to_numeric(df[param_col], errors='coerce').dropna().values
                if len(vals) > 0:
                    mean = np.mean(vals)
                    std = np.std(vals)
                    text += f"{wafer_id:<15} {mean:>10.4g} {std:>10.4g}\n"

        self.stats_text.insert('1.0', text)
        self.stats_text.config(state=tk.DISABLED)

    # ============================================================
    # PUBLIC METHODS
    # ============================================================

    def reset(self):
        """Reset the tab to initial state."""
        self.wafer_data_list.clear()
        self.wafer_ids.clear()
        self.selected_wafer_indices.clear()
        self.test_parameters.clear()
        self.grouped_parameters.clear()

        self._update_wafer_listbox()
        self.group_combo['values'] = ["All Groups"]
        self.group_var.set("All Groups")
        self.param_combo['values'] = []

        self.figure.clear()
        self.canvas.draw()

    def get_selected_wafers(self) -> List[Tuple[pd.DataFrame, str]]:
        """Get list of selected wafers as (DataFrame, wafer_id) tuples."""
        return [(self.wafer_data_list[i], self.wafer_ids[i])
                for i in self.selected_wafer_indices]

    def get_state(self) -> Dict:
        """Get current state for saving."""
        return {
            'wafer_ids': self.wafer_ids.copy(),
            'selected_indices': self.selected_wafer_indices.copy(),
            'selected_group': self.group_var.get() if self.group_var else None,
            'selected_param': self.selected_parameter,
            'display_mode': self.display_mode,
        }
