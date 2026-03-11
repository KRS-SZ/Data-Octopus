"""
Master Inventory Tab Module for Data Octopus v6.3.0

Loads the daily-updated Cork Share CSV (master_wafer_inventory_status_all.csv),
downloads it locally to a Master/ folder, and provides search/filter/browse
functionality for wafers with all columns.

View presets let the user switch between focused column sets (e.g. Testing,
Tracking, AM Data) while still being able to see "All" columns at once.

Usage:
    from src.stdf_analyzer.gui.master_inventory_tab import MasterInventoryTab
    master_tab = MasterInventoryTab(parent_notebook, tab_frame)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import shutil
import threading
from datetime import datetime
from typing import Optional, List, Dict
from collections import OrderedDict


class MasterInventoryTab:
    """Master Inventory Tab – Browse & filter the Cork Share master wafer inventory."""

    NETWORK_CSV = (
        r"\\frlcork-storage.thefacebook.com\oresearch_cork_001"
        r"\uLED_Hive_Extracts\Master Tracker\master_wafer_inventory_status_all.csv"
    )
    LOCAL_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )))),
        "Master",
    )
    LOCAL_CSV = os.path.join(LOCAL_DIR, "master_wafer_inventory_status_all.csv")

    # Row-level filter columns (comboboxes)
    FILTER_COLUMNS = OrderedDict([
        ("Color", "asn_color"),
        ("Stage", "lh_tuskar_stage"),
        ("Tool", "lh_tuskar_tool"),
        ("Status", "status"),
    ])

    # ── View Presets ──────────────────────────────────────────────
    # Each preset maps a display-name to a list of column names.
    # "📋 All Columns" is built dynamically from the CSV header.
    VIEW_PRESETS = OrderedDict([
        ("📋 All Columns", None),  # sentinel – will show every column
        ("🔬 Testing", [
            "lh_tuskar_alias", "lh_tuskar_lotid", "lh_tuskar_waferid",
            "asn_color", "status",
            "lh_tuskar_tool", "lh_tuskar_stage",
            "cp2_corkshare_path", "cp2_manifold_location",
            "cp2_status", "cp2_yield", "cp2_test_program",
            "cp1_corkshare_path", "cp1_manifold_location",
            "cp1_status", "cp1_yield", "cp1_test_program",
        ]),
        ("📍 Tracking", [
            "lh_tuskar_alias", "lh_tuskar_lotid", "lh_tuskar_waferid",
            "asn_color",
            "lh_tuskar_tool", "lh_tuskar_stage",
            "lh_tuskar_prev_tool", "lh_tuskar_prev_stage",
            "status", "gen_lot_type",
        ]),
        ("🏭 AM Data", [
            "lh_tuskar_alias", "lh_tuskar_lotid", "lh_tuskar_waferid",
            "asn_color",
            "asn_am_lotid", "asn_am_product_name",
            "am_configuration", "asn_am_waferid",
            "asn_epi_lotid", "asn_epi_waferid",
        ]),
        ("📦 Packaging", [
            "lh_tuskar_alias", "lh_tuskar_lotid", "lh_tuskar_waferid",
            "asn_color", "status",
            "lh_tuskar_tool", "lh_tuskar_stage",
            "gen_lot_type", "am_configuration",
        ]),
        ("🆔 Identity", [
            "lh_tuskar_alias", "lh_tuskar_lotid", "lh_tuskar_waferid",
            "asn_color",
            "asn_am_lotid", "asn_am_waferid",
            "asn_epi_lotid", "asn_epi_waferid",
            "gen_lot_type",
        ]),
    ])

    # Path columns used to locate wafer data files (checked in order)
    WAFER_PATH_COLUMNS = [
        "cp2_corkshare_path",
        "cp2_manifold_location",
        "cp1_corkshare_path",
        "cp1_manifold_location",
    ]

    DEFAULT_COL_WIDTH = 110

    def __init__(
        self,
        parent_notebook: ttk.Notebook,
        tab_frame: tk.Frame,
        on_load_wafer: Optional[callable] = None,
    ):
        self.parent = parent_notebook
        self.frame = tab_frame
        self.df: Optional[pd.DataFrame] = None
        self.filtered_df: Optional[pd.DataFrame] = None
        self.all_columns: List[str] = []
        self.active_columns: List[str] = []
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
        self._search_after_id: Optional[str] = None
        self.filter_combos: Dict[str, ttk.Combobox] = {}
        self.on_load_wafer = on_load_wafer

        self._create_widgets()
        self._load_data_async()

    # ================================================================
    # WIDGET CREATION
    # ================================================================

    def _create_widgets(self):
        """Build the full UI."""
        # --- Header ---
        header = tk.Frame(self.frame, bg="#0D47A1", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="📋 Master Inventory – Cork Share Wafer Tracker",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#0D47A1",
        ).pack(side=tk.LEFT, padx=20, pady=10)

        self.status_label = tk.Label(
            header,
            text="Loading…",
            font=("Segoe UI", 10),
            fg="#BBDEFB",
            bg="#0D47A1",
        )
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # --- Row 1: Refresh + Search + View preset ---
        ctrl = tk.Frame(self.frame)
        ctrl.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.refresh_btn = tk.Button(
            ctrl, text="🔄 Refresh", command=self._on_refresh,
            font=("Segoe UI", 9), bg="#1565C0", fg="white", width=12,
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Search
        tk.Label(ctrl, text="🔍 Search:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(ctrl, textvariable=self.search_var, width=30, font=("Segoe UI", 10))
        self.search_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.search_var.trace_add("write", self._on_search_changed)
        tk.Button(ctrl, text="✕", command=self._clear_search, font=("Segoe UI", 9), width=3).pack(side=tk.LEFT, padx=(0, 10))

        # Load Wafer button
        self.load_wafer_btn = tk.Button(
            ctrl, text="📂 Load Wafer", command=self._on_load_wafer_clicked,
            font=("Segoe UI", 9, "bold"), bg="#4CAF50", fg="white", width=14,
        )
        self.load_wafer_btn.pack(side=tk.LEFT, padx=(0, 16))

        # View preset
        tk.Label(ctrl, text="View:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        self.view_var = tk.StringVar(value="📋 All Columns")
        self.view_combo = ttk.Combobox(
            ctrl, textvariable=self.view_var, state="readonly", width=20,
            font=("Segoe UI", 10), values=list(self.VIEW_PRESETS.keys()),
        )
        self.view_combo.pack(side=tk.LEFT, padx=(0, 4))
        self.view_combo.bind("<<ComboboxSelected>>", self._on_view_changed)

        # --- Row 2: Row-level filters ---
        filt_frame = tk.Frame(self.frame)
        filt_frame.pack(fill=tk.X, padx=10, pady=(0, 4))

        for label, col in self.FILTER_COLUMNS.items():
            tk.Label(filt_frame, text=f"{label}:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(8, 2))
            cb = ttk.Combobox(filt_frame, state="readonly", width=16, font=("Segoe UI", 9))
            cb.set("All")
            cb.bind("<<ComboboxSelected>>", self._on_filter_changed)
            cb.pack(side=tk.LEFT, padx=(0, 4))
            self.filter_combos[col] = cb

        tk.Button(
            filt_frame, text="Reset Filters", command=self._reset_filters,
            font=("Segoe UI", 9), width=12,
        ).pack(side=tk.LEFT, padx=(16, 0))

        # --- Treeview ---
        self.tree_frame = tk.Frame(self.frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        # Treeview + scrollbars are (re)built in _rebuild_tree_columns()
        self.tree: Optional[ttk.Treeview] = None
        self._vsb: Optional[ttk.Scrollbar] = None
        self._hsb: Optional[ttk.Scrollbar] = None

        # Alternating row style
        style = ttk.Style()
        style.configure("MasterInv.Treeview", rowheight=22, font=("Segoe UI", 9))
        style.configure("MasterInv.Treeview.Heading", font=("Segoe UI", 9, "bold"))

        self._build_tree_widget([])  # empty initial tree

        # --- Bottom bar ---
        bottom = tk.Frame(self.frame)
        bottom.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.count_label = tk.Label(bottom, text="", font=("Segoe UI", 9), anchor=tk.W)
        self.count_label.pack(side=tk.LEFT)
        self.source_label = tk.Label(bottom, text="", font=("Segoe UI", 9), anchor=tk.E, fg="gray")
        self.source_label.pack(side=tk.RIGHT)

    # ================================================================
    # TREEVIEW COLUMN MANAGEMENT
    # ================================================================

    def _build_tree_widget(self, columns: List[str]):
        """Destroy old treeview and create a new one with *columns*."""
        if self.tree is not None:
            self.tree.destroy()
        if self._vsb is not None:
            self._vsb.destroy()
        if self._hsb is not None:
            self._hsb.destroy()

        self.active_columns = list(columns)

        self.tree = ttk.Treeview(
            self.tree_frame, columns=self.active_columns,
            show="headings", selectmode="browse", style="MasterInv.Treeview",
        )
        for col in self.active_columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=self.DEFAULT_COL_WIDTH, minwidth=50, stretch=False)

        self._vsb = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self._hsb = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=self._vsb.set, xscrollcommand=self._hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self._vsb.grid(row=0, column=1, sticky="ns")
        self._hsb.grid(row=1, column=0, sticky="ew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        self.tree.tag_configure("evenrow", background="#FFFFFF")

    def _resolve_columns(self) -> List[str]:
        """Return the column list for the currently selected view preset."""
        preset_name = self.view_var.get()
        preset_cols = self.VIEW_PRESETS.get(preset_name)
        if preset_cols is None:
            return list(self.all_columns)
        # Only keep columns that actually exist in the CSV
        return [c for c in preset_cols if c in self.all_columns]

    def _on_view_changed(self, _event=None):
        """User picked a different view preset."""
        cols = self._resolve_columns()
        self._build_tree_widget(cols)
        self.sort_column = None
        self.sort_reverse = False
        self._populate_tree()

    # ================================================================
    # DATA LOADING
    # ================================================================

    def _load_data_async(self):
        self.refresh_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Loading…")
        threading.Thread(target=self._load_data_worker, daemon=True).start()

    def _load_data_worker(self):
        source = "network"
        try:
            if os.path.isfile(self.NETWORK_CSV):
                os.makedirs(self.LOCAL_DIR, exist_ok=True)
                shutil.copy2(self.NETWORK_CSV, self.LOCAL_CSV)
                df = pd.read_csv(self.LOCAL_CSV, low_memory=False)
            elif os.path.isfile(self.LOCAL_CSV):
                df = pd.read_csv(self.LOCAL_CSV, low_memory=False)
                source = "cache"
            else:
                self.frame.after(0, self._show_load_error, "CSV not found on network or in local cache.")
                return
        except Exception as exc:
            if os.path.isfile(self.LOCAL_CSV):
                try:
                    df = pd.read_csv(self.LOCAL_CSV, low_memory=False)
                    source = "cache"
                except Exception as exc2:
                    self.frame.after(0, self._show_load_error, str(exc2))
                    return
            else:
                self.frame.after(0, self._show_load_error, str(exc))
                return

        self.frame.after(0, self._on_data_loaded, df, source)

    def _on_data_loaded(self, df: pd.DataFrame, source: str):
        self.df = df
        self.filtered_df = df.copy()
        self.all_columns = list(df.columns)
        total = len(df)

        # Populate row-level filter combos
        for col, cb in self.filter_combos.items():
            if col in df.columns:
                values = sorted(df[col].dropna().astype(str).unique().tolist())
                cb["values"] = ["All"] + values
                cb.set("All")

        # Build treeview with current preset
        cols = self._resolve_columns()
        self._build_tree_widget(cols)

        # Update status
        mod_time = self._get_local_mod_time()
        if source == "network":
            self.status_label.config(text=f"Source: Cork Share | {total} Wafers | {mod_time}")
            self.source_label.config(text=f"Downloaded from Cork Share – {mod_time}")
        else:
            self.status_label.config(text=f"Source: Local Cache | {total} Wafers | {mod_time}")
            self.source_label.config(text=f"Loaded from local cache – {mod_time}")

        self.refresh_btn.config(state=tk.NORMAL)
        self._populate_tree()

    def _get_local_mod_time(self) -> str:
        try:
            ts = os.path.getmtime(self.LOCAL_CSV)
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except OSError:
            return ""

    def _show_load_error(self, msg: str):
        self.status_label.config(text="⚠ Load failed")
        self.refresh_btn.config(state=tk.NORMAL)
        self.count_label.config(text=f"Error: {msg}")

    def _on_refresh(self):
        self._load_data_async()

    # ================================================================
    # TREE POPULATION
    # ================================================================

    def _populate_tree(self):
        if self.tree is None:
            return
        self.tree.delete(*self.tree.get_children())
        if self.filtered_df is None or self.filtered_df.empty:
            self.count_label.config(text="No wafers to display")
            return

        cols = [c for c in self.active_columns if c in self.filtered_df.columns]
        for idx, (_, row) in enumerate(self.filtered_df.iterrows()):
            values = [str(row[c]) if pd.notna(row.get(c)) else "" for c in cols]
            tag = "oddrow" if idx % 2 else "evenrow"
            self.tree.insert("", tk.END, values=values, tags=(tag,))

        total = len(self.df) if self.df is not None else 0
        shown = len(self.filtered_df)
        self.count_label.config(text=f"Showing {shown:,} of {total:,} wafers")

    # ================================================================
    # SEARCH (debounced)
    # ================================================================

    def _on_search_changed(self, *_args):
        if self._search_after_id:
            self.frame.after_cancel(self._search_after_id)
        self._search_after_id = self.frame.after(300, self._apply_filters)

    def _clear_search(self):
        self.search_var.set("")
        self._apply_filters()

    # ================================================================
    # ROW FILTERS
    # ================================================================

    def _on_filter_changed(self, _event=None):
        self._apply_filters()

    def _reset_filters(self):
        self.search_var.set("")
        for cb in self.filter_combos.values():
            cb.set("All")
        self._apply_filters()

    def _apply_filters(self):
        if self.df is None:
            return

        mask = pd.Series(True, index=self.df.index)

        # Combo filters
        for col, cb in self.filter_combos.items():
            val = cb.get()
            if val and val != "All" and col in self.df.columns:
                mask &= self.df[col].astype(str) == val

        # Free-text search across ALL columns
        text = self.search_var.get().strip().lower()
        if text:
            text_mask = pd.Series(False, index=self.df.index)
            for col in self.all_columns:
                text_mask |= self.df[col].astype(str).str.lower().str.contains(text, na=False)
            mask &= text_mask

        self.filtered_df = self.df.loc[mask].copy()

        # Re-apply sort
        if self.sort_column and self.sort_column in self.filtered_df.columns:
            self.filtered_df.sort_values(
                by=self.sort_column, ascending=not self.sort_reverse,
                inplace=True, key=lambda s: s.astype(str).str.lower(),
            )

        self._populate_tree()

    # ================================================================
    # SORTING
    # ================================================================

    def _sort_by_column(self, col: str):
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        if self.filtered_df is not None and col in self.filtered_df.columns:
            self.filtered_df.sort_values(
                by=col, ascending=not self.sort_reverse,
                inplace=True, key=lambda s: s.astype(str).str.lower(),
            )
            self._populate_tree()

        # Heading indicators
        for c in self.active_columns:
            indicator = ""
            if c == col:
                indicator = " ▼" if self.sort_reverse else " ▲"
            self.tree.heading(c, text=c + indicator)

    # ================================================================
    # DETAIL POPUP (double-click)
    # ================================================================

    def _on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        if not values or self.df is None:
            return

        # Locate the row by first visible column value
        cols_present = [c for c in self.active_columns if c in self.df.columns]
        if not cols_present:
            return

        # Use first two columns for matching to avoid duplicates
        match = self.df.copy()
        for i, col in enumerate(cols_present[:2]):
            if i < len(values):
                match = match[match[col].astype(str) == values[i]]
        if match.empty:
            return

        row = match.iloc[0]
        self._show_detail_popup(row)

    def _show_detail_popup(self, row: pd.Series):
        popup = tk.Toplevel(self.frame)
        popup.title(f"Wafer Details – {row.get('lh_tuskar_alias', '')}")
        popup.geometry("750x680")
        popup.transient(self.frame.winfo_toplevel())

        # Header
        hdr = tk.Frame(popup, bg="#0D47A1", height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(
            hdr,
            text=f"📋 {row.get('lh_tuskar_alias', '')}  |  {row.get('lh_tuskar_lotid', '')}  |  Wafer {row.get('lh_tuskar_waferid', '')}",
            font=("Segoe UI", 12, "bold"), fg="white", bg="#0D47A1",
        ).pack(side=tk.LEFT, padx=16, pady=6)

        # Scrollable key-value list
        container = tk.Frame(popup)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for i, (col_name, val) in enumerate(row.items()):
            bg = "#F0F4FF" if i % 2 == 0 else "#FFFFFF"
            rf = tk.Frame(inner, bg=bg)
            rf.pack(fill=tk.X)
            tk.Label(rf, text=str(col_name), font=("Segoe UI", 9, "bold"),
                     width=32, anchor="w", bg=bg).pack(side=tk.LEFT, padx=(8, 4), pady=2)
            tk.Label(rf, text=str(val) if pd.notna(val) else "", font=("Segoe UI", 9),
                     anchor="w", bg=bg, wraplength=420).pack(side=tk.LEFT, padx=(0, 8), pady=2, fill=tk.X, expand=True)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        popup.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), popup.destroy()))

        # Bottom buttons
        btn_frame = tk.Frame(popup)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        cp2_cork = row.get("cp2_corkshare_path", "")
        cp2_manifold = row.get("cp2_manifold_location", "")

        def _load_cp2():
            path = str(cp2_cork) if pd.notna(cp2_cork) and str(cp2_cork).strip() else ""
            if not path:
                path = str(cp2_manifold) if pd.notna(cp2_manifold) and str(cp2_manifold).strip() else ""
            if path:
                messagebox.showinfo("CP2 Path", f"CP2 data path:\n{path}", parent=popup)
            else:
                messagebox.showwarning("CP2", "No CP2 path available for this wafer.", parent=popup)

        tk.Button(btn_frame, text="📂 Load CP2 Data", command=_load_cp2,
                  font=("Segoe UI", 9), bg="#4CAF50", fg="white", width=16).pack(side=tk.LEFT, padx=4)

        def _load_wafer_from_popup():
            path = self._resolve_wafer_path(row)
            if path and self.on_load_wafer:
                popup.destroy()
                self.on_load_wafer(path)
            elif not path:
                messagebox.showwarning("No Path", "No loadable wafer path found for this row.", parent=popup)

        tk.Button(btn_frame, text="📂 Load Wafer", command=_load_wafer_from_popup,
                  font=("Segoe UI", 9, "bold"), bg="#1565C0", fg="white", width=14).pack(side=tk.LEFT, padx=4)

        tk.Button(btn_frame, text="Close", command=popup.destroy,
                  font=("Segoe UI", 9), width=10).pack(side=tk.RIGHT, padx=4)

    # ================================================================
    # WAFER LOADING HELPERS
    # ================================================================

    def _resolve_wafer_path(self, row: pd.Series) -> Optional[str]:
        """Find the first valid file path from the known path columns."""
        for col in self.WAFER_PATH_COLUMNS:
            val = row.get(col, "")
            if pd.notna(val) and str(val).strip():
                path = str(val).strip()
                if os.path.isfile(path) or os.path.isdir(path):
                    return path
        # Second pass: return first non-empty path even if not reachable now
        for col in self.WAFER_PATH_COLUMNS:
            val = row.get(col, "")
            if pd.notna(val) and str(val).strip():
                return str(val).strip()
        return None

    def _on_load_wafer_clicked(self):
        """Load wafer data for the currently selected row."""
        if self.tree is None:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a wafer row first.")
            return

        values = self.tree.item(sel[0], "values")
        if not values or self.df is None:
            return

        cols_present = [c for c in self.active_columns if c in self.df.columns]
        if not cols_present:
            return

        match = self.df.copy()
        for i, col in enumerate(cols_present[:2]):
            if i < len(values):
                match = match[match[col].astype(str) == values[i]]
        if match.empty:
            return

        row = match.iloc[0]
        path = self._resolve_wafer_path(row)
        if path and self.on_load_wafer:
            self.on_load_wafer(path)
        elif not path:
            messagebox.showwarning(
                "No Path",
                "No loadable wafer data path found for this wafer.\n\n"
                "Checked columns:\n" + "\n".join(f"  • {c}" for c in self.WAFER_PATH_COLUMNS),
            )

    # ================================================================
    # SELECTION MODE (invoked from other tabs)
    # ================================================================

    def enter_selection_mode(self, label: str, callback, multi: bool = False):
        """Activate selection mode – shows a banner and confirm/cancel buttons.

        Args:
            label:    text shown in the banner, e.g. "Select wafer for: 🗺 Wafer Tab"
            callback: called with a *list* of resolved file paths on confirm
            multi:    if True allow Ctrl+Click multi-select
        """
        self._sel_callback = callback
        self._sel_multi = multi

        # Switch treeview selectmode
        if self.tree is not None:
            self.tree.configure(selectmode="extended" if multi else "browse")

        # Build banner (above the treeview)
        if hasattr(self, "_sel_banner") and self._sel_banner is not None:
            self._sel_banner.destroy()

        self._sel_banner = tk.Frame(self.frame, bg="#FF8F00", height=44)
        self._sel_banner.pack(fill=tk.X, padx=10, pady=(4, 0), before=self.tree_frame)
        self._sel_banner.pack_propagate(False)

        tk.Label(
            self._sel_banner, text=label,
            font=("Segoe UI", 11, "bold"), fg="white", bg="#FF8F00",
        ).pack(side=tk.LEFT, padx=14)

        tk.Button(
            self._sel_banner, text="❌ Cancel", command=self._cancel_selection,
            font=("Segoe UI", 9, "bold"), bg="#C62828", fg="white", width=10,
        ).pack(side=tk.RIGHT, padx=6, pady=6)

        tk.Button(
            self._sel_banner, text="✅ Confirm Selection", command=self._confirm_selection,
            font=("Segoe UI", 9, "bold"), bg="#2E7D32", fg="white", width=18,
        ).pack(side=tk.RIGHT, padx=6, pady=6)

    def _confirm_selection(self):
        """Resolve selected rows and call back."""
        if self.tree is None or self.df is None:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select at least one wafer row.")
            return

        paths: List[str] = []
        cols_present = [c for c in self.active_columns if c in self.df.columns]
        for item in sel:
            values = self.tree.item(item, "values")
            if not values:
                continue
            match = self.df.copy()
            for i, col in enumerate(cols_present[:2]):
                if i < len(values):
                    match = match[match[col].astype(str) == values[i]]
            if match.empty:
                continue
            row = match.iloc[0]
            path = self._resolve_wafer_path(row)
            if path:
                paths.append(path)

        if not paths:
            messagebox.showwarning("No Path", "No loadable paths found for the selected wafer(s).")
            return

        cb = self._sel_callback
        self._exit_selection_mode()
        if cb:
            cb(paths)

    def _cancel_selection(self):
        self._exit_selection_mode()

    def _exit_selection_mode(self):
        self._sel_callback = None
        if hasattr(self, "_sel_banner") and self._sel_banner is not None:
            self._sel_banner.destroy()
            self._sel_banner = None
        if self.tree is not None:
            self.tree.configure(selectmode="browse")

    # ================================================================
    # PUBLIC API
    # ================================================================

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        return self.df

    def get_filtered_dataframe(self) -> Optional[pd.DataFrame]:
        return self.filtered_df

    def refresh(self):
        self._load_data_async()
