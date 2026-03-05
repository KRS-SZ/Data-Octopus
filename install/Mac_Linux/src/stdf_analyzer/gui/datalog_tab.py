"""
Datalog Tab Module for Data Octopus

Displays TXT Datalog files as raw text (1:1 as in the file).
Supports loading single files or folders with TXTDatalog subfolder.

Usage:
    from src.stdf_analyzer.gui.datalog_tab import DatalogTab
    datalog_tab = DatalogTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Optional, Callable


class DatalogTab:
    """
    Datalog Tab - TXT Datalog Raw Text Display.

    Features:
    - Load TXT datalog files
    - Display raw file content 1:1 as in the original file
    - Monospace font for correct alignment
    - Search in text
    - Navigate between multiple files in folder
    """

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_datalog_loaded: Optional[Callable] = None):
        self.parent = parent_notebook
        self.frame = tab_frame
        self.on_datalog_loaded = on_datalog_loaded

        # State
        self.current_file_path: Optional[str] = None
        self.folder_files: list = []
        self.current_file_index: int = 0

        # Build UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets for the Datalog tab."""
        # ============================================================
        # TOP CONTROL PANEL
        # ============================================================
        control_frame = tk.Frame(self.frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Load single file button
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

        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # File navigation (for folder mode)
        self.prev_btn = tk.Button(
            control_frame,
            text="◀ Prev",
            command=self._prev_file,
            font=("Helvetica", 10),
            state=tk.DISABLED,
            width=8
        )
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.file_label_var = tk.StringVar(value="No file loaded")
        file_label = tk.Label(control_frame, textvariable=self.file_label_var,
                              font=("Helvetica", 10, "bold"), width=40, anchor="center")
        file_label.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(
            control_frame,
            text="Next ▶",
            command=self._next_file,
            font=("Helvetica", 10),
            state=tk.DISABLED,
            width=8
        )
        self.next_btn.pack(side=tk.LEFT, padx=2)

        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Search
        tk.Label(control_frame, text="Search:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(5, 2))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind("<Return>", self._search_next)

        search_btn = tk.Button(
            control_frame,
            text="🔍",
            command=self._search_next,
            font=("Helvetica", 10),
            width=3
        )
        search_btn.pack(side=tk.LEFT, padx=2)

        # ============================================================
        # RAW TEXT DISPLAY
        # ============================================================
        text_frame = tk.Frame(self.frame)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Text widget with scrollbars
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Courier New", 9),
            bg="white",
            fg="black",
            state=tk.DISABLED,
            padx=5,
            pady=5
        )

        v_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        h_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.text_widget.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Tag for search highlighting
        self.text_widget.tag_configure("search_highlight", background="yellow", foreground="black")

        # Tag for Device# lines (light gray)
        self.text_widget.tag_configure("device_line", background="#E0E0E0")

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
        """Load a single datalog TXT file."""
        file_path = filedialog.askopenfilename(
            title="Select Datalog File",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        self.folder_files = []
        self.current_file_index = 0
        self._display_file(file_path)
        self._update_nav_buttons()

    def _load_folder(self):
        """Load all TXT datalog files from a folder."""
        folder_path = filedialog.askdirectory(title="Select Folder with TXTDatalog")

        if not folder_path:
            return

        # Look for TXTDatalog subfolder
        txt_datalog_path = os.path.join(folder_path, "TXTDatalog")
        if os.path.exists(txt_datalog_path):
            folder_path = txt_datalog_path

        # Find .txt files
        txt_files = sorted([
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith('.txt')
        ])

        if not txt_files:
            messagebox.showwarning("Warning", "No .txt files found in folder")
            return

        self.folder_files = txt_files
        self.current_file_index = 0
        self._display_file(self.folder_files[0])
        self._update_nav_buttons()

    def _display_file(self, file_path: str):
        """Read and display file content as raw text."""
        try:
            # Try UTF-8 first, fallback to latin-1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()

            self.current_file_path = file_path

            # Display in text widget
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", content)

            # Highlight Device# lines
            self._highlight_device_lines(content)

            self.text_widget.config(state=tk.DISABLED)

            # Scroll to top
            self.text_widget.yview_moveto(0)

            # Update file label
            filename = os.path.basename(file_path)
            if self.folder_files:
                self.file_label_var.set(
                    f"{filename}  ({self.current_file_index + 1}/{len(self.folder_files)})"
                )
            else:
                self.file_label_var.set(filename)

            # Count lines
            line_count = content.count('\n') + 1
            file_size = os.path.getsize(file_path)
            size_str = f"{file_size:,} bytes" if file_size < 1024*1024 else f"{file_size/1024/1024:.1f} MB"
            self.status_var.set(f"Loaded: {filename} — {line_count:,} lines — {size_str}")

            # Callback
            if self.on_datalog_loaded:
                self.on_datalog_loaded()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
            self.status_var.set(f"Error: {e}")

    # ============================================================
    # DEVICE LINE HIGHLIGHTING
    # ============================================================

    def _highlight_device_lines(self, content: str):
        """Highlight lines containing 'Device#:' with light gray background."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "Device#:" in line:
                line_start = f"{i + 1}.0"
                line_end = f"{i + 1}.end"
                self.text_widget.tag_add("device_line", line_start, line_end)

    # ============================================================
    # NAVIGATION
    # ============================================================

    def _prev_file(self):
        """Navigate to previous file in folder."""
        if self.folder_files and self.current_file_index > 0:
            self.current_file_index -= 1
            self._display_file(self.folder_files[self.current_file_index])
            self._update_nav_buttons()

    def _next_file(self):
        """Navigate to next file in folder."""
        if self.folder_files and self.current_file_index < len(self.folder_files) - 1:
            self.current_file_index += 1
            self._display_file(self.folder_files[self.current_file_index])
            self._update_nav_buttons()

    def _update_nav_buttons(self):
        """Enable/disable navigation buttons."""
        if self.folder_files and len(self.folder_files) > 1:
            self.prev_btn.config(state=tk.NORMAL if self.current_file_index > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.current_file_index < len(self.folder_files) - 1 else tk.DISABLED)
        else:
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)

    # ============================================================
    # SEARCH
    # ============================================================

    def _search_next(self, event=None):
        """Search for text and highlight matches."""
        search_term = self.search_var.get().strip()
        if not search_term:
            return

        # Remove previous highlights
        self.text_widget.tag_remove("search_highlight", "1.0", tk.END)

        # Search from current position or start
        start_pos = self.text_widget.index(tk.INSERT)
        pos = self.text_widget.search(search_term, start_pos, stopindex=tk.END, nocase=True)

        if not pos:
            # Wrap around to beginning
            pos = self.text_widget.search(search_term, "1.0", stopindex=start_pos, nocase=True)

        if pos:
            end_pos = f"{pos}+{len(search_term)}c"
            self.text_widget.tag_add("search_highlight", pos, end_pos)
            self.text_widget.see(pos)
            self.text_widget.mark_set(tk.INSERT, end_pos)
            self.status_var.set(f"Found '{search_term}' at line {pos.split('.')[0]}")
        else:
            self.status_var.set(f"'{search_term}' not found")

    # ============================================================
    # PUBLIC METHODS
    # ============================================================

    def load_file(self, file_path: str):
        """Load a datalog file programmatically."""
        self.folder_files = []
        self.current_file_index = 0
        self._display_file(file_path)
        self._update_nav_buttons()

    def get_current_file(self) -> Optional[str]:
        """Get the current file path."""
        return self.current_file_path

    def reset(self):
        """Reset the tab to initial state."""
        self.current_file_path = None
        self.folder_files = []
        self.current_file_index = 0

        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.config(state=tk.DISABLED)

        self.file_label_var.set("No file loaded")
        self.status_var.set("No datalog loaded")
        self._update_nav_buttons()
