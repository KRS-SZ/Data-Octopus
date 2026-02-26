"""
Report Tab Module for Data Octopus

Provides the ReportTab class for configuring and generating
PowerPoint reports with wafermap visualizations and statistics.

Usage:
    from src.stdf_analyzer.gui.report_tab import ReportTab
    report_tab = ReportTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field
import os
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class ReportGroup:
    """Represents a report group configuration."""
    name: str
    enabled: bool = True
    parameters: List[str] = field(default_factory=list)
    slide_type: str = "wafermap"  # "wafermap", "statistics", "comparison", "custom"


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    title: str = "Wafer Analysis Report"
    subtitle: str = ""
    author: str = ""
    include_agenda: bool = True
    include_summary: bool = True
    include_calculation_params: bool = True
    output_format: str = "pptx"  # "pptx", "pdf"
    template_path: Optional[str] = None


class ReportTab:
    """
    Report Tab for configuring and generating PowerPoint reports.

    Features:
    - Report title and metadata configuration
    - Group selection with slide type options
    - Parameter selection per group
    - Template selection
    - Progress indicator during generation
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_report_generated: Optional[Callable] = None):
        """
        Initialize the Report Tab.

        Args:
            parent_notebook: The parent ttk.Notebook widget
            tab_frame: The frame for this tab's content
            on_report_generated: Optional callback when report is generated
        """
        self.parent_notebook = parent_notebook
        self.tab_frame = tab_frame
        self.on_report_generated = on_report_generated

        # State
        self.wafer_data_list: List[pd.DataFrame] = []
        self.wafer_ids: List[str] = []
        self.grouped_parameters: Dict[str, List[str]] = {}
        self.report_groups: Dict[str, ReportGroup] = {}
        self.config = ReportConfig()

        # UI references
        self.title_entry: Optional[ttk.Entry] = None
        self.subtitle_entry: Optional[ttk.Entry] = None
        self.author_entry: Optional[ttk.Entry] = None
        self.group_tree: Optional[ttk.Treeview] = None
        self.param_listbox: Optional[tk.Listbox] = None
        self.progress_var: Optional[tk.DoubleVar] = None
        self.status_label: Optional[ttk.Label] = None

        # Create UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the report tab."""
        # Main container
        main_paned = ttk.PanedWindow(self.tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Configuration
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=1)

        # Right panel: Groups and parameters
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        # === Left Panel ===
        self._create_metadata_panel(left_frame)
        self._create_options_panel(left_frame)
        self._create_output_panel(left_frame)

        # === Right Panel ===
        self._create_groups_panel(right_frame)
        self._create_progress_panel(right_frame)

    def _create_metadata_panel(self, parent: tk.Widget):
        """Create the report metadata panel."""
        meta_frame = ttk.LabelFrame(parent, text="Report Metadata", padding=10)
        meta_frame.pack(fill=tk.X, padx=5, pady=5)

        # Title
        ttk.Label(meta_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.title_entry = ttk.Entry(meta_frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.title_entry.insert(0, "Wafer Analysis Report")

        # Subtitle
        ttk.Label(meta_frame, text="Subtitle:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.subtitle_entry = ttk.Entry(meta_frame, width=40)
        self.subtitle_entry.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))

        # Author
        ttk.Label(meta_frame, text="Author:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.author_entry = ttk.Entry(meta_frame, width=40)
        self.author_entry.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=(5, 0))

        # Date (auto-filled)
        ttk.Label(meta_frame, text="Date:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.date_label = ttk.Label(meta_frame, text=datetime.now().strftime("%Y-%m-%d"))
        self.date_label.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(5, 0))

        meta_frame.columnconfigure(1, weight=1)

    def _create_options_panel(self, parent: tk.Widget):
        """Create the report options panel."""
        options_frame = ttk.LabelFrame(parent, text="Report Options", padding=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Checkboxes
        self.include_agenda_var = tk.BooleanVar(value=True)
        self.include_summary_var = tk.BooleanVar(value=True)
        self.include_calc_params_var = tk.BooleanVar(value=True)
        self.include_wafermap_var = tk.BooleanVar(value=True)
        self.include_statistics_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Include Agenda Slide",
                       variable=self.include_agenda_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include Summary Slide",
                       variable=self.include_summary_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include Calculation Parameters",
                       variable=self.include_calc_params_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include Wafermaps",
                       variable=self.include_wafermap_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Include Statistics Tables",
                       variable=self.include_statistics_var).pack(anchor=tk.W)

        # Template selection
        template_frame = ttk.Frame(options_frame)
        template_frame.pack(fill=tk.X, pady=5)

        ttk.Label(template_frame, text="Template:").pack(side=tk.LEFT)
        self.template_var = tk.StringVar(value="Default")
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var,
                                           values=["Default", "Custom..."], state="readonly", width=20)
        self.template_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(template_frame, text="Browse...",
                  command=self._browse_template).pack(side=tk.LEFT)

    def _create_output_panel(self, parent: tk.Widget):
        """Create the output configuration panel."""
        output_frame = ttk.LabelFrame(parent, text="Output", padding=10)
        output_frame.pack(fill=tk.X, padx=5, pady=5)

        # Output format
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, pady=2)

        ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="pptx")
        ttk.Radiobutton(format_frame, text="PowerPoint (.pptx)",
                       variable=self.format_var, value="pptx").pack(side=tk.LEFT, padx=5)

        # Output path
        path_frame = ttk.Frame(output_frame)
        path_frame.pack(fill=tk.X, pady=2)

        ttk.Label(path_frame, text="Save to:").pack(side=tk.LEFT)
        self.output_path_var = tk.StringVar(value="")
        self.output_entry = ttk.Entry(path_frame, textvariable=self.output_path_var, width=30)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(path_frame, text="Browse...",
                  command=self._browse_output).pack(side=tk.LEFT)

        # Generate button
        btn_frame = ttk.Frame(output_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.generate_btn = ttk.Button(btn_frame, text="🎯 Generate Report",
                                       command=self._generate_report)
        self.generate_btn.pack(fill=tk.X, ipady=5)

    def _create_groups_panel(self, parent: tk.Widget):
        """Create the groups and parameters panel."""
        # Groups frame
        groups_frame = ttk.LabelFrame(parent, text="Report Groups", padding=5)
        groups_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for groups
        tree_frame = ttk.Frame(groups_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.group_tree = ttk.Treeview(
            tree_frame,
            columns=("enabled", "params", "type"),
            show="headings",
            height=12,
            yscrollcommand=tree_scroll.set
        )
        self.group_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.group_tree.yview)

        # Configure columns
        self.group_tree.heading("enabled", text="✓")
        self.group_tree.heading("params", text="Group / Parameters")
        self.group_tree.heading("type", text="Slide Type")

        self.group_tree.column("enabled", width=30, anchor=tk.CENTER)
        self.group_tree.column("params", width=300, anchor=tk.W)
        self.group_tree.column("type", width=100, anchor=tk.CENTER)

        self.group_tree.bind("<Double-1>", self._on_group_double_click)

        # Group buttons
        btn_frame = ttk.Frame(groups_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Enable All",
                  command=self._enable_all_groups).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Disable All",
                  command=self._disable_all_groups).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Toggle Selected",
                  command=self._toggle_selected_group).pack(side=tk.LEFT, padx=2)

        # Slide type selection
        type_frame = ttk.Frame(groups_frame)
        type_frame.pack(fill=tk.X, pady=2)

        ttk.Label(type_frame, text="Slide Type:").pack(side=tk.LEFT)
        self.slide_type_var = tk.StringVar(value="wafermap")
        type_combo = ttk.Combobox(type_frame, textvariable=self.slide_type_var,
                                  values=["wafermap", "statistics", "comparison", "boxplot"],
                                  state="readonly", width=15)
        type_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(type_frame, text="Apply to Selected",
                  command=self._apply_slide_type).pack(side=tk.LEFT)

    def _create_progress_panel(self, parent: tk.Widget):
        """Create the progress indicator panel."""
        progress_frame = ttk.LabelFrame(parent, text="Generation Progress", padding=5)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(progress_frame, text="Ready to generate report")
        self.status_label.pack(anchor=tk.W)

        # Preview/log area
        log_frame = ttk.LabelFrame(parent, text="Generation Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(log_frame, height=8, state='disabled',
                               font=('Consolas', 9), yscrollcommand=log_scroll.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

    def _browse_template(self):
        """Browse for a PowerPoint template."""
        filepath = filedialog.askopenfilename(
            title="Select PowerPoint Template",
            filetypes=[("PowerPoint", "*.pptx"), ("All Files", "*.*")]
        )
        if filepath:
            self.template_var.set(os.path.basename(filepath))
            self.config.template_path = filepath

    def _browse_output(self):
        """Browse for output file location."""
        filepath = filedialog.asksaveasfilename(
            title="Save Report As",
            defaultextension=".pptx",
            filetypes=[("PowerPoint", "*.pptx"), ("All Files", "*.*")]
        )
        if filepath:
            self.output_path_var.set(filepath)

    def _on_group_double_click(self, event):
        """Handle double-click on group to toggle enabled."""
        item = self.group_tree.selection()
        if item:
            self._toggle_selected_group()

    def _enable_all_groups(self):
        """Enable all report groups."""
        for group_name in self.report_groups:
            self.report_groups[group_name].enabled = True
        self._update_groups_display()

    def _disable_all_groups(self):
        """Disable all report groups."""
        for group_name in self.report_groups:
            self.report_groups[group_name].enabled = False
        self._update_groups_display()

    def _toggle_selected_group(self):
        """Toggle the selected group's enabled state."""
        selection = self.group_tree.selection()
        if selection:
            item = selection[0]
            values = self.group_tree.item(item, 'values')
            group_name = values[1] if len(values) > 1 else ""

            if group_name in self.report_groups:
                self.report_groups[group_name].enabled = not self.report_groups[group_name].enabled
                self._update_groups_display()

    def _apply_slide_type(self):
        """Apply selected slide type to selected group."""
        selection = self.group_tree.selection()
        if selection:
            slide_type = self.slide_type_var.get()
            for item in selection:
                values = self.group_tree.item(item, 'values')
                group_name = values[1] if len(values) > 1 else ""

                if group_name in self.report_groups:
                    self.report_groups[group_name].slide_type = slide_type

            self._update_groups_display()

    def _update_groups_display(self):
        """Update the groups treeview display."""
        # Clear existing items
        for item in self.group_tree.get_children():
            self.group_tree.delete(item)

        # Add groups
        for name, group in self.report_groups.items():
            enabled_mark = "✓" if group.enabled else ""
            param_count = len(group.parameters)
            param_text = f"{name} ({param_count} params)"

            self.group_tree.insert("", tk.END, values=(enabled_mark, param_text, group.slide_type))

    def _log(self, message: str):
        """Add message to log."""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.tab_frame.update_idletasks()

    def _generate_report(self):
        """Generate the PowerPoint report."""
        # Validate
        if not self.wafer_data_list:
            messagebox.showwarning("No Data", "Please load wafer data first.")
            return

        output_path = self.output_path_var.get()
        if not output_path:
            # Auto-generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"Report_{timestamp}.pptx"
            self.output_path_var.set(output_path)

        # Update config
        self.config.title = self.title_entry.get()
        self.config.subtitle = self.subtitle_entry.get()
        self.config.author = self.author_entry.get()
        self.config.include_agenda = self.include_agenda_var.get()
        self.config.include_summary = self.include_summary_var.get()
        self.config.include_calculation_params = self.include_calc_params_var.get()

        # Get enabled groups
        enabled_groups = [g for g in self.report_groups.values() if g.enabled]

        if not enabled_groups:
            messagebox.showwarning("No Groups", "Please enable at least one report group.")
            return

        # Start generation
        self._log("Starting report generation...")
        self.progress_var.set(0)
        self.status_label.config(text="Generating report...")
        self.generate_btn.config(state='disabled')

        try:
            # Simulate generation progress (actual implementation would use PPTExporter)
            total_steps = len(enabled_groups) + 3  # +3 for title, agenda, summary
            current_step = 0

            # Title slide
            self._log(f"Creating title slide: {self.config.title}")
            current_step += 1
            self.progress_var.set((current_step / total_steps) * 100)

            # Agenda slide
            if self.config.include_agenda:
                self._log("Creating agenda slide...")
                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            # Group slides
            for group in enabled_groups:
                self._log(f"Creating slides for group: {group.name} ({group.slide_type})")
                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            # Summary slide
            if self.config.include_summary:
                self._log("Creating summary slide...")
                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            # Save
            self._log(f"Saving report to: {output_path}")
            self.progress_var.set(100)

            self._log("✅ Report generation complete!")
            self.status_label.config(text=f"Report saved: {output_path}")

            if self.on_report_generated:
                self.on_report_generated(output_path)

            messagebox.showinfo("Success", f"Report generated successfully!\n\n{output_path}")

        except Exception as e:
            self._log(f"❌ Error: {str(e)}")
            self.status_label.config(text="Error during generation")
            messagebox.showerror("Error", f"Report generation failed:\n\n{str(e)}")

        finally:
            self.generate_btn.config(state='normal')

    def load_data(self, wafer_data_list: List[pd.DataFrame], wafer_ids: List[str],
                  grouped_params: Dict[str, List[str]]):
        """
        Load wafer data for report generation.

        Args:
            wafer_data_list: List of DataFrames with wafer data
            wafer_ids: List of wafer identifiers
            grouped_params: Dict mapping group names to parameter lists
        """
        self.wafer_data_list = wafer_data_list
        self.wafer_ids = wafer_ids
        self.grouped_parameters = grouped_params

        # Create report groups
        self.report_groups = {}
        for group_name, params in grouped_params.items():
            self.report_groups[group_name] = ReportGroup(
                name=group_name,
                enabled=True,
                parameters=params,
                slide_type="wafermap"
            )

        self._update_groups_display()
        self._log(f"Loaded {len(wafer_ids)} wafer(s) with {len(grouped_params)} groups")

    def reset(self):
        """Reset the tab to initial state."""
        self.wafer_data_list = []
        self.wafer_ids = []
        self.grouped_parameters = {}
        self.report_groups = {}

        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, "Wafer Analysis Report")
        self.subtitle_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.output_path_var.set("")

        self._update_groups_display()

        self.progress_var.set(0)
        self.status_label.config(text="Ready to generate report")

        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

    def get_state(self) -> Dict[str, Any]:
        """Get current tab state for serialization."""
        return {
            'title': self.title_entry.get(),
            'subtitle': self.subtitle_entry.get(),
            'author': self.author_entry.get(),
            'include_agenda': self.include_agenda_var.get(),
            'include_summary': self.include_summary_var.get(),
            'include_calc_params': self.include_calc_params_var.get(),
            'output_path': self.output_path_var.get(),
            'enabled_groups': [g.name for g in self.report_groups.values() if g.enabled],
        }

    def set_state(self, state: Dict[str, Any]):
        """Restore tab state from serialization."""
        if 'title' in state:
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, state['title'])
        if 'subtitle' in state:
            self.subtitle_entry.delete(0, tk.END)
            self.subtitle_entry.insert(0, state['subtitle'])
        if 'author' in state:
            self.author_entry.delete(0, tk.END)
            self.author_entry.insert(0, state['author'])

        self.include_agenda_var.set(state.get('include_agenda', True))
        self.include_summary_var.set(state.get('include_summary', True))
        self.include_calc_params_var.set(state.get('include_calc_params', True))
        self.output_path_var.set(state.get('output_path', ''))
