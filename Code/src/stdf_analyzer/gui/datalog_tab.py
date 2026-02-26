"""
Datalog Tab Module for Data Octopus

Contains the DatalogTab class that handles TXT Datalog file analysis.
Parses IGXL/93K datalog files and displays test results, statistics,
and failure analysis.

Usage:
    from src.stdf_analyzer.gui.datalog_tab import DatalogTab
    datalog_tab = DatalogTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Any, Callable

from src.stdf_analyzer.core.datalog_parser import (
    parse_datalog_file,
    parse_datalog_advanced,
    get_datalog_summary,
    get_failed_tests,
    get_tests_by_section,
    DatalogHeader,
)


class DatalogTab:
    """
    Datalog Tab - TXT Datalog File Analysis.
    
    Features:
    - Load TXT datalog files from IGXL/93K testers
    - Display header information (Lot, Program, Operator, etc.)
    - Show test results in sortable table
    - Filter by section (DC Tests, Optical Tests, etc.)
    - Show only failed tests
    - Summary statistics (yield, pass/fail count)
    - Export to CSV
    """
    
    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_datalog_loaded: Optional[Callable] = None):
        """
        Initialize the Datalog Tab.
        
        Args:
            parent_notebook: Parent ttk.Notebook widget
            tab_frame: The frame for this tab
            on_datalog_loaded: Optional callback when datalog is loaded
        """
        self.parent = parent_notebook
        self.frame = tab_frame
        self.on_datalog_loaded = on_datalog_loaded
        
        # ============================================================
        # STATE VARIABLES
        # ============================================================
        self.datalog_df: Optional[pd.DataFrame] = None
        self.header: Optional[DatalogHeader] = None
        self.current_file_path: Optional[str] = None
        self.filtered_df: Optional[pd.DataFrame] = None
        
        # UI Variables
        self.section_var: Optional[tk.StringVar] = None
        self.show_fails_var: Optional[tk.BooleanVar] = None
        self.search_var: Optional[tk.StringVar] = None
        
        # Build UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets for the Datalog tab."""
        # ============================================================
        # TOP CONTROL PANEL
        # ============================================================
        control_frame = tk.Frame(self.frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Load button
        load_btn = tk.Button(
            control_frame,
            text="📂 Load Datalog (TXT)",
            command=self._load_datalog,
            font=("Helvetica", 11),
            bg="#4CAF50",
            fg="white",
            width=20
        )
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # Load folder button
        load_folder_btn = tk.Button(
            control_frame,
            text="📁 Load Folder",
            command=self._load_folder,
            font=("Helvetica", 11),
            bg="#2196F3",
            fg="white",
            width=15
        )
        load_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        export_btn = tk.Button(
            control_frame,
            text="📤 Export CSV",
            command=self._export_csv,
            font=("Helvetica", 10),
            width=12
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Section filter
        tk.Label(control_frame, text="Section:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.section_var = tk.StringVar(value="All Sections")
        self.section_combo = ttk.Combobox(
            control_frame,
            textvariable=self.section_var,
            values=["All Sections"],
            state="readonly",
            width=25
        )
        self.section_combo.pack(side=tk.LEFT, padx=5)
        self.section_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Show fails only checkbox
        self.show_fails_var = tk.BooleanVar(value=False)
        fails_cb = tk.Checkbutton(
            control_frame,
            text="Show Fails Only",
            variable=self.show_fails_var,
            command=self._on_filter_changed,
            font=("Helvetica", 10)
        )
        fails_cb.pack(side=tk.LEFT, padx=10)
        
        # Search
        tk.Label(control_frame, text="Search:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # ============================================================
        # HEADER INFO PANEL
        # ============================================================
        header_frame = tk.LabelFrame(self.frame, text="Datalog Information",
                                      font=("Helvetica", 10, "bold"))
        header_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Header info in grid
        self.header_labels = {}
        header_fields = [
            ("Program:", "prog_name"),
            ("Job:", "job_name"),
            ("Lot:", "lot_id"),
            ("Operator:", "operator"),
            ("Part Type:", "part_type"),
            ("Node:", "node_name"),
            ("Test Mode:", "test_mode"),
            ("Wafer Color:", "wafer_color"),
        ]
        
        for i, (label_text, field) in enumerate(header_fields):
            row = i // 4
            col = (i % 4) * 2
            
            tk.Label(header_frame, text=label_text, font=("Helvetica", 9, "bold")).grid(
                row=row, column=col, sticky="e", padx=5, pady=2)
            
            lbl = tk.Label(header_frame, text="-", font=("Helvetica", 9), fg="gray")
            lbl.grid(row=row, column=col+1, sticky="w", padx=5, pady=2)
            self.header_labels[field] = lbl
        
        # ============================================================
        # SUMMARY PANEL
        # ============================================================
        summary_frame = tk.LabelFrame(self.frame, text="Summary",
                                       font=("Helvetica", 10, "bold"))
        summary_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        summary_inner = tk.Frame(summary_frame)
        summary_inner.pack(fill=tk.X, padx=10, pady=5)
        
        self.total_label = tk.Label(summary_inner, text="Total Tests: -", font=("Helvetica", 10))
        self.total_label.pack(side=tk.LEFT, padx=20)
        
        self.pass_label = tk.Label(summary_inner, text="Pass: -", font=("Helvetica", 10), fg="green")
        self.pass_label.pack(side=tk.LEFT, padx=20)
        
        self.fail_label = tk.Label(summary_inner, text="Fail: -", font=("Helvetica", 10), fg="red")
        self.fail_label.pack(side=tk.LEFT, padx=20)
        
        self.yield_label = tk.Label(summary_inner, text="Yield: -", font=("Helvetica", 10, "bold"))
        self.yield_label.pack(side=tk.LEFT, padx=20)
        
        self.sections_label = tk.Label(summary_inner, text="Sections: -", font=("Helvetica", 10))
        self.sections_label.pack(side=tk.LEFT, padx=20)
        
        # ============================================================
        # MAIN TABLE
        # ============================================================
        table_frame = tk.Frame(self.frame)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create Treeview
        columns = ("test_number", "site", "test_name", "pin", "low_limit", 
                   "measured", "high_limit", "unit", "pass_fail", "section")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=25)
        
        # Configure columns
        col_configs = {
            "test_number": ("Test #", 80, "center"),
            "site": ("Site", 50, "center"),
            "test_name": ("Test Name", 350, "w"),
            "pin": ("Pin", 100, "w"),
            "low_limit": ("Low Limit", 100, "e"),
            "measured": ("Measured", 100, "e"),
            "high_limit": ("High Limit", 100, "e"),
            "unit": ("Unit", 60, "center"),
            "pass_fail": ("P/F", 50, "center"),
            "section": ("Section", 150, "w"),
        }
        
        for col, (heading, width, anchor) in col_configs.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor=anchor)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Configure tags for pass/fail coloring
        self.tree.tag_configure("pass", foreground="green")
        self.tree.tag_configure("fail", foreground="red", background="#ffe6e6")
        
        # ============================================================
        # STATUS BAR
        # ============================================================
        self.status_var = tk.StringVar(value="No datalog loaded")
        status_bar = tk.Label(self.frame, textvariable=self.status_var, 
                               bd=1, relief=tk.SUNKEN, anchor=tk.W,
                               font=("Helvetica", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    # ============================================================
    # FILE LOADING
    # ============================================================
    
    def _load_datalog(self):
        """Load a single datalog file."""
        file_path = filedialog.askopenfilename(
            title="Select Datalog File",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self._load_file(file_path)
    
    def _load_folder(self):
        """Load datalog from TXTDatalog folder."""
        folder_path = filedialog.askdirectory(title="Select Folder with TXTDatalog")
        
        if not folder_path:
            return
        
        # Look for TXTDatalog subfolder
        txt_datalog_path = os.path.join(folder_path, "TXTDatalog")
        if os.path.exists(txt_datalog_path):
            folder_path = txt_datalog_path
        
        # Find .txt files
        txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt') and not f.endswith('_SUM.txt')]
        
        if not txt_files:
            messagebox.showwarning("Warning", "No datalog .txt files found in folder")
            return
        
        # Load first file
        file_path = os.path.join(folder_path, txt_files[0])
        self._load_file(file_path)
    
    def _load_file(self, file_path: str):
        """Load and parse a datalog file."""
        self.status_var.set(f"Loading: {file_path}...")
        self.frame.update()
        
        try:
            # Parse the file
            self.header, self.datalog_df = parse_datalog_advanced(file_path)
            self.current_file_path = file_path
            
            if self.datalog_df.empty:
                messagebox.showwarning("Warning", "No test results found in datalog")
                return
            
            # Update UI
            self._update_header_display()
            self._update_summary()
            self._update_section_combo()
            self._update_table()
            
            self.status_var.set(f"Loaded: {os.path.basename(file_path)} - {len(self.datalog_df)} tests")
            
            # Callback
            if self.on_datalog_loaded:
                self.on_datalog_loaded()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load datalog: {e}")
            self.status_var.set(f"Error: {e}")
    
    # ============================================================
    # UI UPDATES
    # ============================================================
    
    def _update_header_display(self):
        """Update the header information display."""
        if self.header is None:
            return
        
        field_map = {
            'prog_name': self.header.prog_name,
            'job_name': self.header.job_name,
            'lot_id': self.header.lot_id,
            'operator': self.header.operator,
            'part_type': self.header.part_type,
            'node_name': self.header.node_name,
            'test_mode': self.header.test_mode,
            'wafer_color': self.header.wafer_color,
        }
        
        for field, value in field_map.items():
            if field in self.header_labels:
                display_value = value if value else "-"
                self.header_labels[field].config(text=display_value[:40], fg="black")
                
                # Special coloring for wafer color
                if field == 'wafer_color' and value:
                    color_map = {'RED': 'red', 'GREEN': 'green', 'BLUE': 'blue'}
                    self.header_labels[field].config(fg=color_map.get(value.upper(), 'black'))
    
    def _update_summary(self):
        """Update the summary statistics."""
        if self.datalog_df is None or self.datalog_df.empty:
            return
        
        summary = get_datalog_summary(self.datalog_df)
        
        self.total_label.config(text=f"Total Tests: {summary['total_tests']:,}")
        self.pass_label.config(text=f"Pass: {summary['pass_count']:,}")
        self.fail_label.config(text=f"Fail: {summary['fail_count']:,}")
        self.yield_label.config(text=f"Yield: {summary['yield_pct']:.2f}%")
        self.sections_label.config(text=f"Sections: {len(summary['sections'])}")
    
    def _update_section_combo(self):
        """Update the section filter dropdown."""
        if self.datalog_df is None or 'section' not in self.datalog_df.columns:
            return
        
        sections = ["All Sections"] + sorted(self.datalog_df['section'].unique().tolist())
        self.section_combo['values'] = sections
        self.section_var.set("All Sections")
    
    def _update_table(self):
        """Update the test results table."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.datalog_df is None:
            return
        
        # Apply filters
        df = self._apply_filters()
        self.filtered_df = df
        
        # Insert rows
        for _, row in df.iterrows():
            values = (
                row.get('test_number', ''),
                row.get('site', ''),
                row.get('test_name', '')[:60],  # Truncate long names
                row.get('pin', ''),
                self._format_value(row.get('low_limit')),
                self._format_value(row.get('measured')),
                self._format_value(row.get('high_limit')),
                row.get('unit', ''),
                row.get('pass_fail', ''),
                row.get('section', ''),
            )
            
            # Determine tag
            tag = "pass" if row.get('pass_fail') == 'P' else "fail"
            
            self.tree.insert("", tk.END, values=values, tags=(tag,))
        
        self.status_var.set(f"Showing {len(df)} of {len(self.datalog_df)} tests")
    
    def _apply_filters(self) -> pd.DataFrame:
        """Apply current filters to the datalog data."""
        if self.datalog_df is None:
            return pd.DataFrame()
        
        df = self.datalog_df.copy()
        
        # Section filter
        section = self.section_var.get()
        if section != "All Sections":
            df = df[df['section'] == section]
        
        # Fails only
        if self.show_fails_var.get():
            df = df[df['pass_fail'] == 'F']
        
        # Search filter
        search = self.search_var.get().strip().lower()
        if search:
            mask = df['test_name'].str.lower().str.contains(search, na=False)
            if 'pin' in df.columns:
                mask |= df['pin'].str.lower().str.contains(search, na=False)
            df = df[mask]
        
        return df
    
    def _format_value(self, value) -> str:
        """Format a numeric value for display."""
        if value is None or pd.isna(value):
            return "-"
        try:
            return f"{float(value):.6g}"
        except:
            return str(value)
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def _on_filter_changed(self, event=None):
        """Handle filter change."""
        self._update_table()
    
    def _on_search_changed(self, *args):
        """Handle search text change."""
        self._update_table()
    
    def _sort_column(self, col: str):
        """Sort table by column."""
        if self.filtered_df is None:
            return
        
        # Get current sort order
        current_order = getattr(self, '_sort_order', {})
        ascending = not current_order.get(col, True)
        current_order[col] = ascending
        self._sort_order = current_order
        
        # Sort
        try:
            self.filtered_df = self.filtered_df.sort_values(by=col, ascending=ascending)
            self._update_table()
        except:
            pass
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def _export_csv(self):
        """Export filtered data to CSV."""
        if self.filtered_df is None or self.filtered_df.empty:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.filtered_df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Exported {len(self.filtered_df)} rows to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    # ============================================================
    # PUBLIC METHODS
    # ============================================================
    
    def load_file(self, file_path: str):
        """Load a datalog file programmatically."""
        self._load_file(file_path)
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get the current datalog data."""
        return self.datalog_df
    
    def get_filtered_data(self) -> Optional[pd.DataFrame]:
        """Get the filtered datalog data."""
        return self.filtered_df
    
    def get_header(self) -> Optional[DatalogHeader]:
        """Get the parsed header information."""
        return self.header
    
    def reset(self):
        """Reset the tab to initial state."""
        self.datalog_df = None
        self.header = None
        self.current_file_path = None
        self.filtered_df = None
        
        # Clear header labels
        for lbl in self.header_labels.values():
            lbl.config(text="-", fg="gray")
        
        # Clear summary
        self.total_label.config(text="Total Tests: -")
        self.pass_label.config(text="Pass: -")
        self.fail_label.config(text="Fail: -")
        self.yield_label.config(text="Yield: -")
        self.sections_label.config(text="Sections: -")
        
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset filters
        self.section_combo['values'] = ["All Sections"]
        self.section_var.set("All Sections")
        self.show_fails_var.set(False)
        self.search_var.set("")
        
        self.status_var.set("No datalog loaded")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state for saving."""
        return {
            'file_path': self.current_file_path,
            'section_filter': self.section_var.get(),
            'show_fails': self.show_fails_var.get(),
            'search': self.search_var.get(),
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Restore state from saved data."""
        if state.get('section_filter'):
            self.section_var.set(state['section_filter'])
        if 'show_fails' in state:
            self.show_fails_var.set(state['show_fails'])
        if state.get('search'):
            self.search_var.set(state['search'])
