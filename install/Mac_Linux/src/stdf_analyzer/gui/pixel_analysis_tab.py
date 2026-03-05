"""
Pixel Analysis Tab Module for Data Octopus

Provides the PixelAnalysisTab class for PLM (Pixel Level Measurement) analysis
with 25x25 grid visualization, region selection, and pixel statistics.

Usage:
    from src.stdf_analyzer.gui.pixel_analysis_tab import PixelAnalysisTab
    pixel_tab = PixelAnalysisTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PIL import Image

from src.stdf_analyzer.core.statistics_utils import calculate_basic_stats


@dataclass
class PixelConfig:
    """Configuration for pixel analysis."""
    grid_size: int = 25
    colormap: str = "viridis"
    show_grid_lines: bool = True
    show_colorbar: bool = True
    region_colors: List[str] = field(default_factory=lambda: [
        '#E74C3C', '#3498DB', '#2ECC71', '#9B59B6', '#F39C12',
        '#1ABC9C', '#E67E22', '#34495E', '#16A085', '#C0392B'
    ])


@dataclass
class SelectedRegion:
    """Represents a selected region on the pixel map."""
    x: int
    y: int
    width: int
    height: int
    color: str
    rect_id: Optional[int] = None


class PixelAnalysisTab:
    """
    Pixel Analysis Tab for PLM data visualization.

    Features:
    - Load PLM images (PNG, CSV matrices)
    - 25x25 grid visualization with heatmap
    - Multi-region selection with synchronized views
    - Region statistics (mean, std, min, max)
    - Multiple PLM type support (CDMEAN, Bridged, Stitched, etc.)
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_region_selected: Optional[Callable] = None):
        """
        Initialize the Pixel Analysis Tab.

        Args:
            parent_notebook: The parent ttk.Notebook widget
            tab_frame: The frame for this tab's content
            on_region_selected: Optional callback when a region is selected
        """
        self.parent_notebook = parent_notebook
        self.tab_frame = tab_frame
        self.on_region_selected = on_region_selected

        # State
        self.plm_data: Dict[str, np.ndarray] = {}  # PLM type -> matrix
        self.current_plm_type: str = ""
        self.die_coords: Tuple[int, int] = (0, 0)
        self.selected_regions: List[SelectedRegion] = []
        self.config = PixelConfig()

        # Selection state
        self.is_selecting: bool = False
        self.selection_start: Optional[Tuple[int, int]] = None
        self.temp_rect: Optional[int] = None

        # UI references
        self.plm_type_combo: Optional[ttk.Combobox] = None
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.ax: Optional[plt.Axes] = None
        self.region_listbox: Optional[tk.Listbox] = None
        self.stats_text: Optional[tk.Text] = None

        # Create UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the pixel analysis tab."""
        # Main container
        main_paned = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Controls and regions
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)

        # Right panel: Visualization
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)

        # === Left Panel ===
        self._create_control_panel(left_frame)
        self._create_region_panel(left_frame)
        self._create_stats_panel(left_frame)

        # === Right Panel ===
        self._create_visualization_panel(right_frame)

    def _create_control_panel(self, parent: tk.Widget):
        """Create the control panel."""
        control_frame = ttk.LabelFrame(parent, text="PLM Controls", padding=5)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Load PLM button
        ttk.Button(control_frame, text="Load PLM File...",
                  command=self._load_plm_file).pack(fill=tk.X, pady=2)

        # PLM type selection
        type_frame = ttk.Frame(control_frame)
        type_frame.pack(fill=tk.X, pady=2)

        ttk.Label(type_frame, text="PLM Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.plm_type_combo = ttk.Combobox(type_frame, state="readonly", width=20)
        self.plm_type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.plm_type_combo.bind("<<ComboboxSelected>>", self._on_plm_type_changed)

        # Die coordinates display
        self.die_label = ttk.Label(control_frame, text="Die: (0, 0)", foreground="gray")
        self.die_label.pack(anchor=tk.W, pady=2)

        # Options
        options_frame = ttk.LabelFrame(parent, text="Display Options", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_colorbar_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Show Grid Lines",
                       variable=self.show_grid_var,
                       command=self._update_display).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Show Colorbar",
                       variable=self.show_colorbar_var,
                       command=self._update_display).pack(anchor=tk.W)

        # Colormap selection
        cmap_frame = ttk.Frame(options_frame)
        cmap_frame.pack(fill=tk.X, pady=2)

        ttk.Label(cmap_frame, text="Colormap:").pack(side=tk.LEFT, padx=(0, 5))
        self.cmap_combo = ttk.Combobox(cmap_frame, state="readonly", width=15,
                                       values=['viridis', 'plasma', 'inferno', 'magma',
                                              'coolwarm', 'RdYlGn', 'jet', 'gray'])
        self.cmap_combo.set('viridis')
        self.cmap_combo.pack(side=tk.LEFT)
        self.cmap_combo.bind("<<ComboboxSelected>>", lambda e: self._update_display())

    def _create_region_panel(self, parent: tk.Widget):
        """Create the region selection panel."""
        region_frame = ttk.LabelFrame(parent, text="Selected Regions", padding=5)
        region_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Region listbox
        list_scroll = ttk.Scrollbar(region_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.region_listbox = tk.Listbox(region_frame, height=8,
                                         yscrollcommand=list_scroll.set)
        self.region_listbox.pack(fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.region_listbox.yview)

        self.region_listbox.bind("<<ListboxSelect>>", self._on_region_selected)

        # Buttons
        btn_frame = ttk.Frame(region_frame)
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="Add Region",
                  command=self._add_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove",
                  command=self._remove_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All",
                  command=self._clear_regions).pack(side=tk.LEFT, padx=2)

    def _create_stats_panel(self, parent: tk.Widget):
        """Create the statistics panel."""
        stats_frame = ttk.LabelFrame(parent, text="Region Statistics", padding=5)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.stats_text = tk.Text(stats_frame, height=8, width=30, state='disabled',
                                  font=('Consolas', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)

    def _create_visualization_panel(self, parent: tk.Widget):
        """Create the visualization panel."""
        viz_frame = ttk.LabelFrame(parent, text="Pixel Map", padding=5)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.figure.patch.set_facecolor('white')

        self.ax = self.figure.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)

        # Add toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

    def _load_plm_file(self):
        """Load a PLM file (image or CSV)."""
        filetypes = [
            ("PLM Files", "*.png *.csv *.txt"),
            ("PNG Images", "*.png"),
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ]

        filepath = filedialog.askopenfilename(
            title="Select PLM File",
            filetypes=filetypes
        )

        if not filepath:
            return

        try:
            # Determine PLM type from filename
            filename = os.path.basename(filepath)
            plm_type = self._extract_plm_type(filename)

            # Load based on file type
            if filepath.lower().endswith('.png'):
                matrix = self._load_png_as_matrix(filepath)
            else:
                matrix = self._load_csv_as_matrix(filepath)

            if matrix is not None:
                self.plm_data[plm_type] = matrix
                self._update_plm_type_combo()
                self.plm_type_combo.set(plm_type)
                self.current_plm_type = plm_type
                self._update_display()

        except Exception as e:
            print(f"Error loading PLM file: {e}")

    def _extract_plm_type(self, filename: str) -> str:
        """Extract PLM type from filename."""
        known_types = ['CDMEAN', 'Bridged', 'Bridged-Pixels', 'Stitched',
                      'UniformitySyn', 'PLM', 'Pixel']

        for plm_type in known_types:
            if plm_type.lower() in filename.lower():
                return plm_type

        # Default to filename without extension
        return os.path.splitext(filename)[0][:20]

    def _load_png_as_matrix(self, filepath: str) -> Optional[np.ndarray]:
        """Load PNG image as numpy matrix."""
        try:
            img = Image.open(filepath)
            if img.mode != 'L':
                img = img.convert('L')
            return np.array(img, dtype=np.float64)
        except Exception as e:
            print(f"Error loading PNG: {e}")
            return None

    def _load_csv_as_matrix(self, filepath: str) -> Optional[np.ndarray]:
        """Load CSV file as numpy matrix."""
        try:
            return np.loadtxt(filepath, delimiter=',')
        except:
            try:
                return np.loadtxt(filepath, delimiter='\t')
            except Exception as e:
                print(f"Error loading CSV: {e}")
                return None

    def _update_plm_type_combo(self):
        """Update PLM type dropdown."""
        types = list(self.plm_data.keys())
        self.plm_type_combo['values'] = types
        if types and not self.current_plm_type:
            self.plm_type_combo.current(0)
            self.current_plm_type = types[0]

    def _on_plm_type_changed(self, event):
        """Handle PLM type selection change."""
        self.current_plm_type = self.plm_type_combo.get()
        self._update_display()

    def _update_display(self):
        """Update the pixel map display."""
        self.ax.clear()

        if not self.current_plm_type or self.current_plm_type not in self.plm_data:
            self.ax.text(0.5, 0.5, "No PLM data loaded", ha='center', va='center',
                        fontsize=12, transform=self.ax.transAxes)
            self.canvas.draw()
            return

        matrix = self.plm_data[self.current_plm_type]
        cmap = self.cmap_combo.get()

        # Display heatmap
        im = self.ax.imshow(matrix, cmap=cmap, aspect='equal', origin='upper')

        # Add colorbar
        if self.show_colorbar_var.get():
            # Remove old colorbars
            for cb in self.figure.axes[1:]:
                cb.remove()
            self.figure.colorbar(im, ax=self.ax, shrink=0.8)

        # Add grid lines
        if self.show_grid_var.get():
            rows, cols = matrix.shape
            self.ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
            self.ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
            self.ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

        # Draw selected regions
        for i, region in enumerate(self.selected_regions):
            rect = Rectangle((region.x - 0.5, region.y - 0.5),
                            region.width, region.height,
                            linewidth=2, edgecolor=region.color,
                            facecolor='none', linestyle='-')
            self.ax.add_patch(rect)

            # Add region label
            self.ax.text(region.x + region.width/2, region.y - 0.7,
                        f"R{i+1}", ha='center', va='bottom',
                        fontsize=8, fontweight='bold', color=region.color)

        # Styling
        self.ax.set_title(f"PLM: {self.current_plm_type}", fontsize=11, fontweight='bold')
        self.ax.set_xlabel("Column", fontsize=10)
        self.ax.set_ylabel("Row", fontsize=10)

        self.figure.tight_layout()
        self.canvas.draw()

    def _on_mouse_press(self, event):
        """Handle mouse press for region selection."""
        if event.inaxes != self.ax or event.button != 1:
            return

        self.is_selecting = True
        self.selection_start = (int(event.xdata + 0.5), int(event.ydata + 0.5))

    def _on_mouse_motion(self, event):
        """Handle mouse motion during selection."""
        if not self.is_selecting or event.inaxes != self.ax:
            return

        # Could add visual feedback here
        pass

    def _on_mouse_release(self, event):
        """Handle mouse release to complete selection."""
        if not self.is_selecting or event.inaxes != self.ax:
            self.is_selecting = False
            return

        self.is_selecting = False

        if self.selection_start is None:
            return

        end_x = int(event.xdata + 0.5)
        end_y = int(event.ydata + 0.5)

        x1, x2 = min(self.selection_start[0], end_x), max(self.selection_start[0], end_x)
        y1, y2 = min(self.selection_start[1], end_y), max(self.selection_start[1], end_y)

        width = max(1, x2 - x1 + 1)
        height = max(1, y2 - y1 + 1)

        # Add region
        color_idx = len(self.selected_regions) % len(self.config.region_colors)
        region = SelectedRegion(
            x=x1, y=y1, width=width, height=height,
            color=self.config.region_colors[color_idx]
        )

        self.selected_regions.append(region)
        self._update_region_list()
        self._update_display()
        self._update_stats()

        if self.on_region_selected:
            self.on_region_selected(region)

    def _add_region(self):
        """Add a new region (prompts for coordinates)."""
        # Simple dialog would be added here
        pass

    def _remove_region(self):
        """Remove the selected region."""
        selection = self.region_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.selected_regions[idx]
            self._update_region_list()
            self._update_display()
            self._update_stats()

    def _clear_regions(self):
        """Clear all selected regions."""
        self.selected_regions = []
        self._update_region_list()
        self._update_display()
        self._update_stats()

    def _update_region_list(self):
        """Update the region listbox."""
        self.region_listbox.delete(0, tk.END)

        for i, region in enumerate(self.selected_regions):
            text = f"R{i+1}: ({region.x},{region.y}) {region.width}x{region.height}"
            self.region_listbox.insert(tk.END, text)
            self.region_listbox.itemconfig(tk.END, fg=region.color)

    def _on_region_selected(self, event):
        """Handle region selection in listbox."""
        self._update_stats()

    def _update_stats(self):
        """Update statistics display for selected region."""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)

        if not self.current_plm_type or self.current_plm_type not in self.plm_data:
            self.stats_text.insert(tk.END, "No PLM data loaded")
            self.stats_text.config(state='disabled')
            return

        matrix = self.plm_data[self.current_plm_type]

        # Get selected region
        selection = self.region_listbox.curselection()
        if selection:
            idx = selection[0]
            region = self.selected_regions[idx]

            # Extract region data
            y1, y2 = region.y, min(region.y + region.height, matrix.shape[0])
            x1, x2 = region.x, min(region.x + region.width, matrix.shape[1])
            region_data = matrix[y1:y2, x1:x2].flatten()

            # Calculate statistics
            valid_data = region_data[~np.isnan(region_data)]

            if len(valid_data) > 0:
                stats = calculate_basic_stats(valid_data)

                text = f"Region R{idx+1} Statistics\n"
                text += f"{'─' * 25}\n"
                text += f"Position: ({region.x}, {region.y})\n"
                text += f"Size: {region.width} x {region.height}\n"
                text += f"Pixels: {stats['count']}\n"
                text += f"{'─' * 25}\n"
                text += f"Mean:   {stats['mean']:.4g}\n"
                text += f"Std:    {stats['std']:.4g}\n"
                text += f"Min:    {stats['min']:.4g}\n"
                text += f"Max:    {stats['max']:.4g}\n"
                text += f"Median: {stats['median']:.4g}\n"
                text += f"Range:  {stats['range']:.4g}\n"
            else:
                text = "No valid data in region"
        else:
            # Show overall statistics
            valid_data = matrix[~np.isnan(matrix)].flatten()

            if len(valid_data) > 0:
                stats = calculate_basic_stats(valid_data)

                text = f"Overall PLM Statistics\n"
                text += f"{'─' * 25}\n"
                text += f"Type: {self.current_plm_type}\n"
                text += f"Size: {matrix.shape[1]} x {matrix.shape[0]}\n"
                text += f"Pixels: {stats['count']}\n"
                text += f"{'─' * 25}\n"
                text += f"Mean:   {stats['mean']:.4g}\n"
                text += f"Std:    {stats['std']:.4g}\n"
                text += f"Min:    {stats['min']:.4g}\n"
                text += f"Max:    {stats['max']:.4g}\n"
            else:
                text = "No valid data"

        self.stats_text.insert(tk.END, text)
        self.stats_text.config(state='disabled')

    def load_plm_matrix(self, matrix: np.ndarray, plm_type: str,
                        die_coords: Tuple[int, int] = (0, 0)):
        """
        Load a PLM matrix directly.

        Args:
            matrix: 2D numpy array with pixel values
            plm_type: Type identifier (e.g., 'CDMEAN')
            die_coords: Die coordinates (x, y)
        """
        self.plm_data[plm_type] = matrix
        self.die_coords = die_coords
        self.die_label.config(text=f"Die: {die_coords}")

        self._update_plm_type_combo()
        self.plm_type_combo.set(plm_type)
        self.current_plm_type = plm_type
        self._update_display()
        self._update_stats()

    def reset(self):
        """Reset the tab to initial state."""
        self.plm_data = {}
        self.current_plm_type = ""
        self.die_coords = (0, 0)
        self.selected_regions = []

        self.plm_type_combo.set("")
        self.plm_type_combo['values'] = []
        self.die_label.config(text="Die: (0, 0)")

        self._update_region_list()
        self._update_display()
        self._update_stats()

    def get_state(self) -> Dict[str, Any]:
        """Get current tab state for serialization."""
        return {
            'current_plm_type': self.current_plm_type,
            'die_coords': self.die_coords,
            'regions': [(r.x, r.y, r.width, r.height) for r in self.selected_regions],
            'show_grid': self.show_grid_var.get(),
            'show_colorbar': self.show_colorbar_var.get(),
            'colormap': self.cmap_combo.get(),
        }

    def set_state(self, state: Dict[str, Any]):
        """Restore tab state from serialization."""
        self.show_grid_var.set(state.get('show_grid', True))
        self.show_colorbar_var.set(state.get('show_colorbar', True))
        self.cmap_combo.set(state.get('colormap', 'viridis'))
