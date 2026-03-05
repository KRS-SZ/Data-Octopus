"""
Dashboard Tab Module for Data Octopus v5.2.0

Professional Dashboard with Manifold Tool Overview, Analytics, and Charts.
Shows which wafers are on each tool, activity timeline, lot analysis, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, List
from collections import Counter
import re
import os

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


class DashboardTab:
    """Dashboard Tab - Professional Manifold Tool Overview with Analytics."""

    # Manifold Paths
    MANIFOLD_BASE_TSK = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tuskar/uled/incoming/tool_data"
    MANIFOLD_BASE_TPW = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tpw/PEQUIN/CP2"
    MANIFOLD_BASE_RGS = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/arranmore/testing"  # Regensburg - Coming soon
    MANIFOLD_WEB_BASE = "https://www.internalfb.com/manifold/explorer/"

    TOOLS = {
        "ATE": ["9ATE1", "9ATE2", "9ATE3", "9ATE4"],
        "Prober": ["9PRB3", "9PRF3"],
        "Taiwan": ["TPW-CP2"],
        "Regensburg": ["RGS-ATE"]  # Coming soon
    }

    COLORS = {
        "header_bg": "#1565C0",
        "header_fg": "#FFFFFF",
        "bg": "#ECEFF1",
        "card_bg": "#FFFFFF",
        "ate": "#2196F3",       # Blue for Tuscar ATE
        "prober": "#9C27B0",    # Purple for Prober
        "taiwan": "#FF5722",    # Orange for Taiwan
        "regensburg": "#00BCD4", # Cyan for Regensburg (Coming soon)
        "online": "#4CAF50",
        "offline": "#9E9E9E",
        "error": "#F44336",
    }

    WAFER_COLORS = {"Red": "#F44336", "Blue": "#2196F3", "Green": "#4CAF50", "---": "#9E9E9E"}

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame,
                 on_wafer_load: Optional[Callable] = None):
        self.parent = parent_notebook
        self.frame = tab_frame
        self.on_wafer_load = on_wafer_load

        self.tool_data: Dict[str, List[Dict]] = {}
        self.all_wafers: List[Dict] = []
        self.recent_wafers: List[Dict] = []
        self.auto_refresh = False
        self.tools_loaded = 0
        self.total_tools = 8  # 4 ATE + 2 Prober + 1 Taiwan + 1 Regensburg

        self.tool_cards: Dict[str, Dict] = {}
        self.kpi_labels: Dict[str, tk.Label] = {}
        self.chart_canvases: Dict[str, dict] = {}

        self._create_widgets()
        self._refresh_all_tools()

    def _create_widgets(self):
        """Create all Dashboard widgets."""
        # Header
        header = tk.Frame(self.frame, bg=self.COLORS["header_bg"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📊 DASHBOARD - Tool Analytics", font=("Segoe UI", 16, "bold"),
                 bg=self.COLORS["header_bg"], fg=self.COLORS["header_fg"]).pack(side=tk.LEFT, padx=15, pady=10)

        # Controls
        ctrl = tk.Frame(header, bg=self.COLORS["header_bg"])
        ctrl.pack(side=tk.RIGHT, padx=15)

        tk.Label(ctrl, text="Time:", font=("Segoe UI", 9), bg=self.COLORS["header_bg"],
                 fg=self.COLORS["header_fg"]).pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="All Time")
        ttk.Combobox(ctrl, textvariable=self.time_var, values=["Last 24h", "Last 7d", "Last 30d", "All Time"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=5)

        self.auto_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Auto", variable=self.auto_var, command=self._toggle_auto,
                       bg=self.COLORS["header_bg"], fg=self.COLORS["header_fg"],
                       selectcolor=self.COLORS["header_bg"]).pack(side=tk.LEFT, padx=10)

        tk.Button(ctrl, text="🔄 Refresh", command=self._refresh_all_tools, font=("Segoe UI", 9, "bold"),
                  bg="#42A5F5", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT)

        # Scrollable content
        self.canvas = tk.Canvas(self.frame, bg=self.COLORS["bg"], highlightthickness=0)
        scroll = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=self.COLORS["bg"])

        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # KPI Cards
        self._create_kpi_section()

        # Tool Cards
        self._create_tools_section()

        # Charts
        self._create_charts_section()

        # Lot Details
        self._create_lot_detail_section()

        # Recent Wafers Table
        self._create_table_section()

        # Status
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                 font=("Segoe UI", 9), bg="#FAFAFA").pack(side=tk.BOTTOM, fill=tk.X)

    def _create_kpi_section(self):
        """Create KPI summary cards."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.X, padx=15, pady=10)

        kpis = [("📊 Total Wafers", "0", "#2196F3", "total"),
                ("🟢 Online", "0/6", "#4CAF50", "online"),
                ("📅 Today", "0", "#FF9800", "today"),
                ("📈 Avg/Tool", "0", "#9C27B0", "avg")]

        for i, (title, val, color, key) in enumerate(kpis):
            card = tk.Frame(section, bg="white", relief=tk.RIDGE, bd=1, width=180, height=70)
            card.pack(side=tk.LEFT, padx=8, pady=5)
            card.pack_propagate(False)
            tk.Label(card, text=title, font=("Segoe UI", 9), bg="white", fg="#757575").pack(pady=(8,0))
            lbl = tk.Label(card, text=val, font=("Segoe UI", 20, "bold"), bg="white", fg=color)
            lbl.pack()
            self.kpi_labels[key] = lbl

    def _create_tools_section(self):
        """Create tool status cards with browse buttons."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.X, padx=15, pady=5)

        # Header with Prober checkbox
        header_frame = tk.Frame(section, bg=self.COLORS["bg"])
        header_frame.pack(fill=tk.X, pady=(0,8))

        tk.Label(header_frame, text="🔧 TUSCAR - ATE TESTERS", font=("Segoe UI", 12, "bold"),
                 bg=self.COLORS["bg"], fg="#37474F").pack(side=tk.LEFT)

        # Prober checkbox (optional)
        self.show_prober_var = tk.BooleanVar(value=False)
        prober_cb = tk.Checkbutton(header_frame, text="Show Probers",
                                   variable=self.show_prober_var, command=self._toggle_probers,
                                   bg=self.COLORS["bg"], font=("Segoe UI", 9))
        prober_cb.pack(side=tk.RIGHT)

        # Taiwan checkbox
        self.show_taiwan_var = tk.BooleanVar(value=True)
        taiwan_cb = tk.Checkbutton(header_frame, text="Show Taiwan 🇹🇼",
                                   variable=self.show_taiwan_var, command=self._toggle_taiwan,
                                   bg=self.COLORS["bg"], font=("Segoe UI", 9))
        taiwan_cb.pack(side=tk.RIGHT, padx=10)

        # ATE Tool cards container
        self.ate_cards_frame = tk.Frame(section, bg=self.COLORS["bg"])
        self.ate_cards_frame.pack(fill=tk.X)

        # Create ATE tool cards (always visible)
        for col, tool in enumerate(self.TOOLS["ATE"]):
            self._create_tool_card(self.ate_cards_frame, tool, "ATE", col)

        # Prober Tool cards container (hidden by default)
        self.prober_cards_frame = tk.Frame(section, bg=self.COLORS["bg"])
        for col, tool in enumerate(self.TOOLS["Prober"]):
            self._create_tool_card(self.prober_cards_frame, tool, "Prober", col)

        # Taiwan Tool cards container (shown by default)
        self.taiwan_cards_frame = tk.Frame(section, bg=self.COLORS["bg"])
        self.taiwan_cards_frame.pack(fill=tk.X, pady=(10, 0))

        # Taiwan header
        taiwan_header = tk.Frame(self.taiwan_cards_frame, bg=self.COLORS["bg"])
        taiwan_header.pack(fill=tk.X, pady=(0,5))
        tk.Label(taiwan_header, text="🇹🇼 TAIWAN - CP2", font=("Segoe UI", 11, "bold"),
                 bg=self.COLORS["bg"], fg=self.COLORS["taiwan"]).pack(side=tk.LEFT)

        # Taiwan tool card
        taiwan_tools_frame = tk.Frame(self.taiwan_cards_frame, bg=self.COLORS["bg"])
        taiwan_tools_frame.pack(fill=tk.X)
        self._create_tool_card(taiwan_tools_frame, "TPW-CP2", "Taiwan", 0)

        # Regensburg Tool cards container (Coming soon)
        self.regensburg_cards_frame = tk.Frame(section, bg=self.COLORS["bg"])
        self.regensburg_cards_frame.pack(fill=tk.X, pady=(10, 0))

        # Regensburg header
        rgs_header = tk.Frame(self.regensburg_cards_frame, bg=self.COLORS["bg"])
        rgs_header.pack(fill=tk.X, pady=(0,5))
        tk.Label(rgs_header, text="🇩🇪 REGENSBURG - ATE (Coming soon)", font=("Segoe UI", 11, "bold"),
                 bg=self.COLORS["bg"], fg=self.COLORS["regensburg"]).pack(side=tk.LEFT)

        # Regensburg tool card
        rgs_tools_frame = tk.Frame(self.regensburg_cards_frame, bg=self.COLORS["bg"])
        rgs_tools_frame.pack(fill=tk.X)
        self._create_tool_card(rgs_tools_frame, "RGS-ATE", "Regensburg", 0)

    def _toggle_probers(self):
        """Toggle visibility of Prober cards."""
        if self.show_prober_var.get():
            self.prober_cards_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.prober_cards_frame.pack_forget()

    def _toggle_taiwan(self):
        """Toggle visibility of Taiwan cards."""
        if self.show_taiwan_var.get():
            self.taiwan_cards_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.taiwan_cards_frame.pack_forget()

    def _create_tool_card(self, parent, name: str, cat: str, col: int):
        """Create a single tool card with browse button."""
        if cat == "ATE":
            color = self.COLORS["ate"]
            icon = "🔧"
        elif cat == "Prober":
            color = self.COLORS["prober"]
            icon = "🔬"
        elif cat == "Taiwan":
            color = self.COLORS["taiwan"]
            icon = "🇹🇼"
        else:  # Regensburg
            color = self.COLORS["regensburg"]
            icon = "🇩🇪"

        card = tk.Frame(parent, bg="white", relief=tk.RIDGE, bd=1, width=170, height=140)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        card.pack_propagate(False)
        parent.grid_columnconfigure(col, weight=1)

        # Header
        hdr = tk.Frame(card, bg=color, height=28)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"{icon} {name}", font=("Segoe UI", 10, "bold"), bg=color, fg="white").pack(side=tk.LEFT, padx=8, pady=4)

        # Content
        cnt = tk.Frame(card, bg="white", padx=8, pady=4)
        cnt.pack(fill=tk.BOTH, expand=True)

        status = tk.Label(cnt, text="● Loading", font=("Segoe UI", 8), bg="white", fg=self.COLORS["offline"])
        status.pack(anchor=tk.W)
        wafer = tk.Label(cnt, text="---", font=("Segoe UI", 8), bg="white", fg="#424242")
        wafer.pack(anchor=tk.W)
        time_lbl = tk.Label(cnt, text="---", font=("Segoe UI", 8), bg="white", fg="#757575")
        time_lbl.pack(anchor=tk.W)
        count = tk.Label(cnt, text="0 files", font=("Segoe UI", 8), bg="white", fg="#757575")
        count.pack(anchor=tk.W)

        # Browse button
        browse_btn = tk.Button(cnt, text="📂 Browse", font=("Segoe UI", 8),
                              bg="#E3F2FD" if cat != "Taiwan" else "#FFF3E0",
                              fg="#1565C0" if cat != "Taiwan" else "#E65100",
                              relief=tk.FLAT, cursor="hand2",
                              command=lambda t=name, c=cat: self._open_tool_in_browser(t, c))
        browse_btn.pack(fill=tk.X, pady=(4, 0))

        self.tool_cards[name] = {"status": status, "wafer": wafer, "time": time_lbl, "count": count}

    def _open_tool_in_browser(self, tool: str, cat: str):
        """Open tool folder in Manifold web browser."""
        import webbrowser
        if cat == "Taiwan":
            url = f"{self.MANIFOLD_WEB_BASE}{self.MANIFOLD_BASE_TPW}"
        elif cat == "Regensburg":
            url = f"{self.MANIFOLD_WEB_BASE}{self.MANIFOLD_BASE_RGS}"
        else:  # ATE or Prober (Tuscar)
            url = f"{self.MANIFOLD_WEB_BASE}{self.MANIFOLD_BASE_TSK}/{tool}"
        webbrowser.open(url)

    def _create_taiwan_section(self):
        """Create Taiwan data section."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.X, padx=15, pady=10)

        # Header
        header = tk.Frame(section, bg=self.COLORS["bg"])
        header.pack(fill=tk.X, pady=(0,8))

        tk.Label(header, text="🇹🇼 TAIWAN - CP2 Data", font=("Segoe UI", 12, "bold"),
                 bg=self.COLORS["bg"], fg=self.COLORS["taiwan"]).pack(side=tk.LEFT)

        # Browse Taiwan button
        tk.Button(header, text="📂 Browse Taiwan", font=("Segoe UI", 9, "bold"),
                 bg="#FFF3E0", fg="#E65100", relief=tk.FLAT, padx=10, cursor="hand2",
                 command=self._open_taiwan_in_browser).pack(side=tk.LEFT, padx=10)

        # Refresh Taiwan button
        tk.Button(header, text="🔄 Refresh", font=("Segoe UI", 9),
                 bg="#FFCCBC", fg="#BF360C", relief=tk.FLAT, padx=8, cursor="hand2",
                 command=self._refresh_taiwan).pack(side=tk.LEFT)

        # Taiwan data container
        taiwan_frame = tk.Frame(section, bg="white", relief=tk.RIDGE, bd=1)
        taiwan_frame.pack(fill=tk.X)

        # Left: Summary card
        summary_card = tk.Frame(taiwan_frame, bg="white", width=200)
        summary_card.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        summary_card.pack_propagate(False)

        tk.Label(summary_card, text="📊 Summary", font=("Segoe UI", 10, "bold"),
                bg="white", fg=self.COLORS["taiwan"]).pack(anchor=tk.W)

        self.taiwan_status = tk.Label(summary_card, text="● Loading...", font=("Segoe UI", 9),
                                      bg="white", fg=self.COLORS["offline"])
        self.taiwan_status.pack(anchor=tk.W, pady=(5,0))

        self.taiwan_files_count = tk.Label(summary_card, text="Files: ---", font=("Segoe UI", 9),
                                           bg="white", fg="#424242")
        self.taiwan_files_count.pack(anchor=tk.W)

        self.taiwan_lots_count = tk.Label(summary_card, text="Lots: ---", font=("Segoe UI", 9),
                                          bg="white", fg="#424242")
        self.taiwan_lots_count.pack(anchor=tk.W)

        self.taiwan_last_update = tk.Label(summary_card, text="Last: ---", font=("Segoe UI", 9),
                                           bg="white", fg="#757575")
        self.taiwan_last_update.pack(anchor=tk.W)

        # Right: Lot list
        lot_frame = tk.Frame(taiwan_frame, bg="white")
        lot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(lot_frame, text="📦 Recent Lots", font=("Segoe UI", 10, "bold"),
                bg="white", fg="#37474F").pack(anchor=tk.W)

        # Taiwan lot treeview
        cols = ("lot", "wafers", "last_date", "size")
        self.taiwan_tree = ttk.Treeview(lot_frame, columns=cols, show="headings", height=4)

        for c, w, txt in [("lot", 100, "Lot"), ("wafers", 60, "Wafers"),
                          ("last_date", 120, "Last Date"), ("size", 80, "Size")]:
            self.taiwan_tree.heading(c, text=txt)
            self.taiwan_tree.column(c, width=w, anchor="center")

        self.taiwan_tree.pack(fill=tk.BOTH, expand=True)

    def _open_taiwan_in_browser(self):
        """Open Taiwan folder in Manifold web browser."""
        import webbrowser
        url = f"{self.MANIFOLD_WEB_BASE}{self.MANIFOLD_BASE_TPW}"
        webbrowser.open(url)

    def _refresh_taiwan(self):
        """Refresh Taiwan data from Manifold."""
        self.taiwan_status.config(text="● Loading...", fg=self.COLORS["offline"])
        threading.Thread(target=self._fetch_taiwan, daemon=True).start()

    def _fetch_taiwan(self):
        """Fetch Taiwan data from Manifold."""
        try:
            cmd = f'manifold --vip ls {self.MANIFOLD_BASE_TPW}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                files = self._parse_taiwan_output(result.stdout)
                self.frame.after(0, lambda: self._update_taiwan(files))
            else:
                self.frame.after(0, lambda: self._update_taiwan_error())
        except Exception as e:
            self.frame.after(0, lambda: self._update_taiwan_error())

    def _parse_taiwan_output(self, output: str) -> List[Dict]:
        """Parse Taiwan manifold ls output."""
        files = []
        for line in output.strip().split('\n'):
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            size_str, name = parts
            if size_str == "DIR" or not name.endswith('.zip') or name.endswith('.manifest'):
                continue
            try:
                size = int(size_str)
            except:
                continue

            # Parse Taiwan filename: TPW_P03004_CP2S_..._PROD_P40570.1_07_19_STYLE_X_0_20251119-192228.zip
            info = self._parse_taiwan_filename(name, size)
            if info:
                files.append(info)

        return files

    def _parse_taiwan_filename(self, filename: str, size: int) -> Optional[Dict]:
        """Parse Taiwan wafer info from filename."""
        try:
            name = filename.replace('.zip', '')

            # Extract lot (P40570, P40549, etc.)
            lot_match = re.search(r'_PROD_(P\d+)\.', name)
            lot = lot_match.group(1) if lot_match else "---"

            # Extract wafer number (07_19 = wafer 07, slot 19)
            wafer_match = re.search(r'_PROD_P\d+\.\d+_(\d+)_(\d+)_', name)
            if wafer_match:
                wafer = f"W{wafer_match.group(1)}"
                slot = f"S{wafer_match.group(2)}"
            else:
                wafer, slot = "---", "---"

            # Extract product (STYLE, CARDS, LARCH, etc.)
            product_match = re.search(r'_(\d+)_(STYLE|CARDS|LARCH|PEQUIN)_', name, re.IGNORECASE)
            product = product_match.group(2) if product_match else "---"

            # DateTime
            dt_match = re.search(r'_(\d{8})-(\d{6})\.zip', filename)
            if dt_match:
                dt_raw = f"{dt_match.group(1)}-{dt_match.group(2)}"
                try:
                    dt_obj = datetime.strptime(dt_raw, "%Y%m%d-%H%M%S")
                    dt_disp = dt_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_obj, dt_disp = None, dt_raw
            else:
                dt_raw, dt_obj, dt_disp = "", None, "---"

            # Size
            if size > 1e9:
                size_str = f"{size/1e9:.1f}GB"
            elif size > 1e6:
                size_str = f"{size/1e6:.1f}MB"
            else:
                size_str = f"{size/1e3:.1f}KB"

            return {"lot": lot, "wafer": wafer, "slot": slot, "product": product,
                    "datetime": dt_disp, "datetime_raw": dt_raw, "datetime_obj": dt_obj,
                    "size": size_str, "size_bytes": size, "filename": filename}
        except:
            return None

    def _update_taiwan(self, files: List[Dict]):
        """Update Taiwan section with fetched data."""
        self.taiwan_data = files

        if files:
            self.taiwan_status.config(text="● Online", fg=self.COLORS["online"])
            self.taiwan_files_count.config(text=f"Files: {len(files)}")

            # Group by lot
            lots = {}
            for f in files:
                lot = f.get("lot", "---")
                if lot not in lots:
                    lots[lot] = []
                lots[lot].append(f)

            self.taiwan_lots_count.config(text=f"Lots: {len(lots)}")

            # Last update
            if files:
                latest = max(files, key=lambda x: x.get("datetime_raw", ""))
                self.taiwan_last_update.config(text=f"Last: {latest.get('datetime', '---')}")

            # Update lot tree
            for item in self.taiwan_tree.get_children():
                self.taiwan_tree.delete(item)

            sorted_lots = sorted(lots.items(), key=lambda x: max(f.get("datetime_raw", "") for f in x[1]), reverse=True)

            for lot, lot_files in sorted_lots[:10]:  # Top 10 lots
                total_size = sum(f.get("size_bytes", 0) for f in lot_files)
                if total_size > 1e9:
                    size_str = f"{total_size/1e9:.1f}GB"
                else:
                    size_str = f"{total_size/1e6:.1f}MB"

                last_date = max(f.get("datetime", "---") for f in lot_files)
                self.taiwan_tree.insert("", tk.END, values=(lot, len(lot_files), last_date, size_str))
        else:
            self.taiwan_status.config(text="● No data", fg=self.COLORS["offline"])

    def _update_taiwan_error(self):
        """Update Taiwan section with error."""
        self.taiwan_status.config(text="● Error", fg=self.COLORS["error"])
        self.taiwan_files_count.config(text="Files: ---")
        self.taiwan_lots_count.config(text="Lots: ---")

    def _create_charts_section(self):
        """Create analytics charts."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        tk.Label(section, text="📈 ANALYTICS", font=("Segoe UI", 12, "bold"),
                 bg=self.COLORS["bg"], fg="#37474F").pack(anchor=tk.W, pady=(0,8))

        charts = tk.Frame(section, bg=self.COLORS["bg"])
        charts.pack(fill=tk.BOTH, expand=True)

        # Chart 1: Wafers per Tool
        self._create_chart(charts, "wafers_tool", "📊 Wafers per Tool", 0, 0)

        # Chart 2: Site Distribution (NEW!)
        self._create_chart(charts, "sites", "🌍 Site Distribution", 0, 1)

        # Chart 3: Color Distribution (moved)
        self._create_chart(charts, "colors", "🎨 Color/Product Distribution", 0, 2)

        # Chart 4: Timeline
        self._create_chart(charts, "timeline", "📅 Activity Timeline", 1, 0)

        # Chart 5: Lots per Tool
        self._create_chart(charts, "lots", "📦 Lots per Tool", 1, 1)

        for i in range(3):
            charts.grid_columnconfigure(i, weight=1, uniform="chart")
        for i in range(2):
            charts.grid_rowconfigure(i, weight=1)

    def _create_chart(self, parent, key: str, title: str, row: int, col: int):
        """Create a single chart container."""
        frame = tk.Frame(parent, bg="white", relief=tk.RIDGE, bd=1)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        tk.Label(frame, text=title, font=("Segoe UI", 9, "bold"), bg="#FAFAFA", fg="#37474F").pack(fill=tk.X, pady=3)

        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Loading...', ha='center', va='center', fontsize=10, color='#9E9E9E')
        ax.axis('off')
        fig.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        self.chart_canvases[key] = {"fig": fig, "ax": ax, "canvas": canvas}

    def _create_lot_detail_section(self):
        """Create detailed lot analysis section."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        tk.Label(section, text="📦 LOT DETAILS - Tool Analysis", font=("Segoe UI", 12, "bold"),
                 bg=self.COLORS["bg"], fg="#37474F").pack(anchor=tk.W, pady=(0,8))

        # Main container
        main = tk.Frame(section, bg="white", relief=tk.RIDGE, bd=1)
        main.pack(fill=tk.BOTH, expand=True)

        # Left: Tool selection
        left = tk.Frame(main, bg="white", width=120)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left.pack_propagate(False)

        tk.Label(left, text="Select Tool:", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor=tk.W)

        self.lot_tool_var = tk.StringVar(value="9ATE1")

        # ATE Tools
        tk.Label(left, text="── ATE ──", font=("Segoe UI", 8), bg="white", fg="#757575").pack(anchor=tk.W, pady=(5,0))
        for tool in self.TOOLS["ATE"]:
            rb = tk.Radiobutton(left, text=tool, variable=self.lot_tool_var, value=tool,
                               command=self._update_lot_details, bg="white", font=("Segoe UI", 9))
            rb.pack(anchor=tk.W)

        # Prober Tools
        tk.Label(left, text="── Prober ──", font=("Segoe UI", 8), bg="white", fg="#757575").pack(anchor=tk.W, pady=(5,0))
        for tool in self.TOOLS["Prober"]:
            rb = tk.Radiobutton(left, text=tool, variable=self.lot_tool_var, value=tool,
                               command=self._update_lot_details, bg="white", font=("Segoe UI", 9))
            rb.pack(anchor=tk.W)

        # Taiwan
        tk.Label(left, text="── Taiwan ──", font=("Segoe UI", 8), bg="white", fg=self.COLORS["taiwan"]).pack(anchor=tk.W, pady=(5,0))
        for tool in self.TOOLS["Taiwan"]:
            rb = tk.Radiobutton(left, text=tool, variable=self.lot_tool_var, value=tool,
                               command=self._update_lot_details, bg="white", font=("Segoe UI", 9),
                               fg=self.COLORS["taiwan"])
            rb.pack(anchor=tk.W)

        # Regensburg (Coming soon)
        tk.Label(left, text="── Regensburg ──", font=("Segoe UI", 8), bg="white", fg=self.COLORS["regensburg"]).pack(anchor=tk.W, pady=(5,0))
        for tool in self.TOOLS["Regensburg"]:
            rb = tk.Radiobutton(left, text=f"{tool} ⏳", variable=self.lot_tool_var, value=tool,
                               command=self._update_lot_details, bg="white", font=("Segoe UI", 9),
                               fg=self.COLORS["regensburg"])
            rb.pack(anchor=tk.W)

        # Middle: Lot list
        mid = tk.Frame(main, bg="white", width=200)
        mid.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        mid.pack_propagate(False)

        tk.Label(mid, text="Lots on Tool:", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor=tk.W)

        lot_frame = tk.Frame(mid, bg="white")
        lot_frame.pack(fill=tk.BOTH, expand=True)

        self.lot_listbox = tk.Listbox(lot_frame, font=("Segoe UI", 9), height=8, exportselection=False)
        lot_scroll = ttk.Scrollbar(lot_frame, orient=tk.VERTICAL, command=self.lot_listbox.yview)
        self.lot_listbox.configure(yscrollcommand=lot_scroll.set)
        self.lot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lot_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.lot_listbox.bind("<<ListboxSelect>>", self._on_lot_select)

        # Right: Wafer details for selected lot
        right = tk.Frame(main, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(right, text="Wafers in Selected Lot:", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor=tk.W)

        # Wafer detail treeview
        cols = ("slot", "color", "datetime", "size", "delta")
        self.lot_tree = ttk.Treeview(right, columns=cols, show="headings", height=6)

        for c, w, txt in [("slot", 60, "Slot"), ("color", 60, "Color"),
                          ("datetime", 130, "Date/Time"), ("size", 80, "Size"), ("delta", 100, "Δ Time")]:
            self.lot_tree.heading(c, text=txt)
            self.lot_tree.column(c, width=w, anchor="center")

        lot_tree_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.lot_tree.yview)
        self.lot_tree.configure(yscrollcommand=lot_tree_scroll.set)
        self.lot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lot_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Summary stats
        self.lot_summary_var = tk.StringVar(value="Select a lot to see details")
        tk.Label(right, textvariable=self.lot_summary_var, font=("Segoe UI", 9),
                 bg="#E3F2FD", fg="#1565C0", wraplength=400, justify=tk.LEFT).pack(fill=tk.X, pady=(5,0))

    def _update_lot_details(self):
        """Update lot list for selected tool."""
        self.lot_listbox.delete(0, tk.END)
        for item in self.lot_tree.get_children():
            self.lot_tree.delete(item)
        self.lot_summary_var.set("Select a lot to see details")

        tool = self.lot_tool_var.get()
        wafers = self.tool_data.get(tool, [])

        # Group by lot
        lots = {}
        for w in wafers:
            lot = w.get("lot", "---")
            if lot not in lots:
                lots[lot] = []
            lots[lot].append(w)

        # Sort lots by most recent wafer
        sorted_lots = sorted(lots.items(), key=lambda x: max(w.get("datetime_raw", "") for w in x[1]), reverse=True)

        for lot, wlist in sorted_lots:
            self.lot_listbox.insert(tk.END, f"{lot} ({len(wlist)} wafers)")

    def _on_lot_select(self, event):
        """Handle lot selection - show wafer details."""
        sel = self.lot_listbox.curselection()
        if not sel:
            return

        lot_text = self.lot_listbox.get(sel[0])
        lot_name = lot_text.split(" (")[0]

        tool = self.lot_tool_var.get()
        wafers = [w for w in self.tool_data.get(tool, []) if w.get("lot") == lot_name]

        # Sort by datetime
        wafers.sort(key=lambda x: x.get("datetime_raw", ""))

        # Clear and populate tree
        for item in self.lot_tree.get_children():
            self.lot_tree.delete(item)

        total_size = 0
        prev_dt = None
        deltas = []

        for w in wafers:
            dt_obj = w.get("datetime_obj")
            delta_str = "---"

            if dt_obj and prev_dt:
                delta = dt_obj - prev_dt
                delta_hours = delta.total_seconds() / 3600
                if delta_hours < 24:
                    delta_str = f"{delta_hours:.1f}h"
                else:
                    delta_str = f"{delta_hours/24:.1f}d"
                deltas.append(delta.total_seconds())

            self.lot_tree.insert("", tk.END, values=(
                w.get("slot", "---"),
                w.get("color", "---"),
                w.get("datetime", "---"),
                w.get("size", "---"),
                delta_str
            ))

            total_size += w.get("size_bytes", 0)
            if dt_obj:
                prev_dt = dt_obj

        # Summary
        total_gb = total_size / 1e9
        first_dt = wafers[0].get("datetime", "---") if wafers else "---"
        last_dt = wafers[-1].get("datetime", "---") if wafers else "---"
        avg_delta = np.mean(deltas) / 3600 if deltas else 0

        summary = f"📊 {len(wafers)} wafers | 💾 {total_gb:.1f} GB | ⏱ Avg interval: {avg_delta:.1f}h\n"
        summary += f"📅 First: {first_dt} → Last: {last_dt}"
        self.lot_summary_var.set(summary)

    def _create_table_section(self):
        """Create recent wafers table."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(section, text="📋 RECENT WAFERS", font=("Segoe UI", 12, "bold"),
                 bg=self.COLORS["bg"], fg="#37474F").pack(anchor=tk.W, pady=(0,8))

        tree_frame = tk.Frame(section, bg="white", relief=tk.RIDGE, bd=1)
        tree_frame.pack(fill=tk.X)

        cols = ("tool", "lot", "slot", "color", "datetime", "size")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=6)

        for c, w in [("tool", 70), ("lot", 100), ("slot", 50), ("color", 60), ("datetime", 120), ("size", 80)]:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=w, anchor="center")

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _toggle_auto(self):
        self.auto_refresh = self.auto_var.get()
        if self.auto_refresh:
            self.frame.after(60000, self._auto_tick)

    def _auto_tick(self):
        if self.auto_refresh:
            self._refresh_all_tools()
            self.frame.after(60000, self._auto_tick)

    def _refresh_all_tools(self):
        """Refresh all tool data from Manifold."""
        self.status_var.set("🔄 Loading from Manifold...")
        self.tool_data = {}
        self.all_wafers = []
        self.tools_loaded = 0

        for cat, tools in self.TOOLS.items():
            for tool in tools:
                threading.Thread(target=self._fetch_tool, args=(tool, cat), daemon=True).start()

    def _fetch_tool(self, tool: str, cat: str = "ATE"):
        """Fetch data for one tool."""
        try:
            if cat == "Taiwan":
                cmd = f'manifold --vip ls {self.MANIFOLD_BASE_TPW}'
            elif cat == "Regensburg":
                cmd = f'manifold --vip ls {self.MANIFOLD_BASE_RGS}'
            else:  # ATE or Prober (Tuscar)
                cmd = f'manifold --vip ls {self.MANIFOLD_BASE_TSK}/{tool}'

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                if cat == "Taiwan":
                    files = self._parse_taiwan_output(result.stdout, tool)
                elif cat == "Regensburg":
                    files = self._parse_output(result.stdout, tool)  # Same format as Tuscar (or custom later)
                else:
                    files = self._parse_output(result.stdout, tool)
                self.frame.after(0, lambda t=tool, f=files: self._update_tool(t, f))
            else:
                self.frame.after(0, lambda t=tool: self._update_tool_error(t))
        except:
            self.frame.after(0, lambda t=tool: self._update_tool_error(t))

    def _parse_taiwan_output(self, output: str, tool: str) -> List[Dict]:
        """Parse Taiwan manifold ls output."""
        files = []
        for line in output.strip().split('\n'):
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            size_str, name = parts
            if size_str == "DIR" or not name.endswith('.zip') or name.endswith('.manifest'):
                continue
            try:
                size = int(size_str)
            except:
                continue

            info = self._parse_taiwan_filename(name, tool, size)
            if info:
                files.append(info)

        files.sort(key=lambda x: x.get('datetime_raw', ''), reverse=True)
        return files

    def _parse_taiwan_filename(self, filename: str, tool: str, size: int) -> Optional[Dict]:
        """Parse Taiwan wafer info from filename."""
        try:
            name = filename.replace('.zip', '')

            # Extract lot (P40570, P40549, etc.)
            lot_match = re.search(r'_PROD_(P\d+)\.', name)
            lot = lot_match.group(1) if lot_match else "---"

            # Extract wafer number
            wafer_match = re.search(r'_PROD_P\d+\.\d+_(\d+)_(\d+)_', name)
            slot = f"S{wafer_match.group(1)}" if wafer_match else "---"

            # Extract product (STYLE, CARDS, LARCH, etc.)
            product_match = re.search(r'_(\d+)_(STYLE|CARDS|LARCH|PEQUIN)_', name, re.IGNORECASE)
            color = product_match.group(2) if product_match else "---"  # Use product as "color"

            # DateTime
            dt_match = re.search(r'_(\d{8})-(\d{6})\.zip', filename)
            if dt_match:
                dt_raw = f"{dt_match.group(1)}-{dt_match.group(2)}"
                try:
                    dt_obj = datetime.strptime(dt_raw, "%Y%m%d-%H%M%S")
                    dt_disp = dt_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_obj, dt_disp = None, dt_raw
            else:
                dt_raw, dt_obj, dt_disp = "", None, "---"

            # Size
            if size > 1e9:
                size_str = f"{size/1e9:.1f}GB"
            elif size > 1e6:
                size_str = f"{size/1e6:.1f}MB"
            else:
                size_str = f"{size/1e3:.1f}KB"

            return {"tool": tool, "filename": filename, "lot": lot, "slot": slot, "color": color,
                    "datetime": dt_disp, "datetime_raw": dt_raw, "datetime_obj": dt_obj,
                    "size": size_str, "size_bytes": size}
        except:
            return None

    def _parse_output(self, output: str, tool: str) -> List[Dict]:
        """Parse manifold ls output."""
        files = []
        for line in output.strip().split('\n'):
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            size_str, name = parts
            if size_str == "DIR" or not name.endswith('.zip') or name.endswith('.manifest'):
                continue
            try:
                size = int(size_str)
            except:
                continue

            info = self._parse_filename(name, tool, size)
            if info:
                files.append(info)

        files.sort(key=lambda x: x.get('datetime_raw', ''), reverse=True)
        return files

    def _parse_filename(self, filename: str, tool: str, size: int) -> Optional[Dict]:
        """Parse wafer info from filename."""
        try:
            name = filename.replace('.zip', '').replace('_fix', '')

            # DateTime
            dt_match = re.search(r'_(\d{8})-(\d{6})$', name)
            if dt_match:
                dt_raw = f"{dt_match.group(1)}-{dt_match.group(2)}"
                try:
                    dt_obj = datetime.strptime(dt_raw, "%Y%m%d-%H%M%S")
                    dt_disp = dt_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_obj, dt_disp = None, dt_raw
            else:
                dt_raw, dt_obj, dt_disp = "", None, "---"

            # Lot
            lot_match = re.search(r'(UNAC?\d+)', name)
            lot = lot_match.group(1) if lot_match else "---"

            # Slot
            slot_match = re.search(r'_(\d+)_Slot(\d+)', name)
            slot = f"S{slot_match.group(2)}" if slot_match else "---"

            # Color
            color_match = re.search(r'_(red|blue|green)_', name, re.IGNORECASE)
            color = color_match.group(1).capitalize() if color_match else "---"

            # Size
            if size > 1e9:
                size_str = f"{size/1e9:.1f}GB"
            elif size > 1e6:
                size_str = f"{size/1e6:.1f}MB"
            else:
                size_str = f"{size/1e3:.1f}KB"

            return {"tool": tool, "filename": filename, "lot": lot, "slot": slot, "color": color,
                    "datetime": dt_disp, "datetime_raw": dt_raw, "datetime_obj": dt_obj,
                    "size": size_str, "size_bytes": size}
        except:
            return None

    def _update_tool(self, tool: str, files: List[Dict]):
        """Update tool card and collect data."""
        self.tool_data[tool] = files
        card = self.tool_cards.get(tool)

        if card:
            if files:
                card["status"].config(text="● Online", fg=self.COLORS["online"])
                latest = files[0]
                card["wafer"].config(text=f"{latest['lot']}_{latest['slot']}")
                card["time"].config(text=latest["datetime"])
                card["count"].config(text=f"{len(files)} files")
                self.all_wafers.extend(files)
            else:
                card["status"].config(text="● No data", fg=self.COLORS["offline"])

        self.tools_loaded += 1
        if self.tools_loaded >= self.total_tools:
            self._update_all()

    def _update_tool_error(self, tool: str):
        """Update tool card with error."""
        self.tool_data[tool] = []
        card = self.tool_cards.get(tool)
        if card:
            card["status"].config(text="● Error", fg=self.COLORS["error"])

        self.tools_loaded += 1
        if self.tools_loaded >= self.total_tools:
            self._update_all()

    def _update_all(self):
        """Update KPIs, charts, and table."""
        self._update_kpis()
        self._update_charts()
        self._update_table()
        self.status_var.set(f"✓ Updated {datetime.now().strftime('%H:%M:%S')} - {len(self.all_wafers)} wafers")

    def _update_kpis(self):
        """Update KPI cards."""
        total = len(self.all_wafers)
        online = sum(1 for f in self.tool_data.values() if f)
        today = sum(1 for w in self.all_wafers if w.get("datetime_obj") and w["datetime_obj"].date() == datetime.now().date())
        avg = total // max(self.total_tools, 1)

        self.kpi_labels.get("total", tk.Label()).config(text=str(total))
        self.kpi_labels.get("online", tk.Label()).config(text=f"{online}/{self.total_tools}")
        self.kpi_labels.get("today", tk.Label()).config(text=str(today))
        self.kpi_labels.get("avg", tk.Label()).config(text=str(avg))

    def _update_charts(self):
        """Update all charts."""
        self._update_wafers_chart()
        self._update_site_chart()
        self._update_colors_chart()
        self._update_timeline_chart()
        self._update_lots_chart()

    def _update_wafers_chart(self):
        """Bar chart: Wafers per tool."""
        c = self.chart_canvases.get("wafers_tool")
        if not c:
            return
        ax = c["ax"]
        ax.clear()

        # Get visible tools
        tools = list(self.TOOLS["ATE"])
        colors = [self.COLORS["ate"]] * len(tools)

        if self.show_prober_var.get():
            tools += list(self.TOOLS["Prober"])
            colors += [self.COLORS["prober"]] * len(self.TOOLS["Prober"])

        if self.show_taiwan_var.get():
            tools += list(self.TOOLS["Taiwan"])
            colors += [self.COLORS["taiwan"]] * len(self.TOOLS["Taiwan"])

        vals = [len(self.tool_data.get(t, [])) for t in tools]

        bars = ax.bar(tools, vals, color=colors, edgecolor='white')
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(v),
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

        ax.set_ylabel('Count', fontsize=8)
        ax.tick_params(axis='x', labelsize=7, rotation=45)
        ax.tick_params(axis='y', labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        c["fig"].tight_layout(pad=1)
        c["canvas"].draw()

    def _update_colors_chart(self):
        """Pie chart: Color/Product distribution with site breakdown."""
        c = self.chart_canvases.get("colors")
        if not c:
            return
        ax = c["ax"]
        ax.clear()

        # Replace "---" with "NA" and count
        color_counts = Counter()
        for w in self.all_wafers:
            color = w.get("color", "---")
            if color == "---":
                color = "NA"
            color_counts[color] += 1

        if not color_counts:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=10, color='#9E9E9E')
            ax.axis('off')
        else:
            labels, sizes = zip(*color_counts.items())
            # Extended colors including NA
            color_map = {
                "Red": "#F44336", "Blue": "#2196F3", "Green": "#4CAF50",
                "CARDS": "#FF9800", "LARCH": "#795548", "STYLE": "#E91E63",
                "PEQUIN": "#9C27B0", "NA": "#607D8B"  # NA = Blue-Gray
            }
            colors = [color_map.get(l, "#9E9E9E") for l in labels]
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90, textprops={'fontsize': 7})
            ax.axis('equal')

        c["fig"].tight_layout(pad=1)
        c["canvas"].draw()

    def _update_site_chart(self):
        """Pie chart: Site distribution (Tuscar/Taiwan/Regensburg)."""
        c = self.chart_canvases.get("sites")
        if not c:
            return
        ax = c["ax"]
        ax.clear()

        # Count by site
        site_counts = {"Tuscar": 0, "Taiwan": 0, "Regensburg": 0}

        for tool, files in self.tool_data.items():
            if tool in self.TOOLS["ATE"] or tool in self.TOOLS["Prober"]:
                site_counts["Tuscar"] += len(files)
            elif tool in self.TOOLS["Taiwan"]:
                site_counts["Taiwan"] += len(files)
            elif tool in self.TOOLS["Regensburg"]:
                site_counts["Regensburg"] += len(files)

        # Remove empty sites
        site_counts = {k: v for k, v in site_counts.items() if v > 0}

        if not site_counts:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=10, color='#9E9E9E')
            ax.axis('off')
        else:
            labels, sizes = zip(*site_counts.items())
            site_colors = {
                "Tuscar": self.COLORS["ate"],
                "Taiwan": self.COLORS["taiwan"],
                "Regensburg": self.COLORS["regensburg"]
            }
            colors = [site_colors.get(l, "#9E9E9E") for l in labels]

            # Show percentages and counts
            def make_autopct(sizes):
                def autopct(pct):
                    total = sum(sizes)
                    val = int(round(pct * total / 100.0))
                    return f'{pct:.0f}%\n({val})'
                return autopct

            ax.pie(sizes, labels=labels, colors=colors, autopct=make_autopct(sizes),
                   startangle=90, textprops={'fontsize': 7})
            ax.axis('equal')

        c["fig"].tight_layout(pad=1)
        c["canvas"].draw()

    def _update_timeline_chart(self):
        """Line chart: Activity over time."""
        c = self.chart_canvases.get("timeline")
        if not c:
            return
        ax = c["ax"]
        ax.clear()

        wafers = [w for w in self.all_wafers if w.get("datetime_obj")]
        if not wafers:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=10, color='#9E9E9E')
            ax.axis('off')
        else:
            counts = Counter(w["datetime_obj"].date() for w in wafers)
            dates = sorted(counts.keys())
            vals = [counts[d] for d in dates]

            ax.fill_between(dates, vals, alpha=0.3, color=self.COLORS["ate"])
            ax.plot(dates, vals, '-o', color=self.COLORS["ate"], linewidth=1.5, markersize=3)
            ax.set_ylabel('Wafers', fontsize=8)
            ax.tick_params(axis='both', labelsize=7)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            if len(dates) > 5:
                ax.xaxis.set_major_locator(plt.MaxNLocator(5))
            for label in ax.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')

        c["fig"].tight_layout(pad=1)
        c["canvas"].draw()

    def _update_lots_chart(self):
        """Horizontal bar: Unique lots per tool."""
        c = self.chart_canvases.get("lots")
        if not c:
            return
        ax = c["ax"]
        ax.clear()

        # Get visible tools
        tools = list(self.TOOLS["ATE"])
        colors = [self.COLORS["ate"]] * len(tools)

        if self.show_prober_var.get():
            tools += list(self.TOOLS["Prober"])
            colors += [self.COLORS["prober"]] * len(self.TOOLS["Prober"])

        if self.show_taiwan_var.get():
            tools += list(self.TOOLS["Taiwan"])
            colors += [self.COLORS["taiwan"]] * len(self.TOOLS["Taiwan"])

        lot_counts = []
        for t in tools:
            lots = set(w.get("lot") for w in self.tool_data.get(t, []) if w.get("lot") != "---")
            lot_counts.append(len(lots))

        y = range(len(tools))

        bars = ax.barh(y, lot_counts, color=colors, edgecolor='white')
        for bar, v in zip(bars, lot_counts):
            if v > 0:
                ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, str(v),
                       va='center', fontsize=8, fontweight='bold')

        ax.set_yticks(y)
        ax.set_yticklabels(tools, fontsize=7)
        ax.set_xlabel('Unique Lots', fontsize=8)
        ax.tick_params(axis='x', labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        c["fig"].tight_layout(pad=1)
        c["canvas"].draw()

    def _update_table(self):
        """Update recent wafers table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.all_wafers.sort(key=lambda x: x.get('datetime_raw', ''), reverse=True)

        for w in self.all_wafers[:15]:
            self.tree.insert("", tk.END, values=(w["tool"], w["lot"], w["slot"], w["color"], w["datetime"], w["size"]))

    def _on_double_click(self, event):
        """Handle double-click on table row."""
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])["values"]
            if vals:
                messagebox.showinfo("Wafer Info", f"Tool: {vals[0]}\nLot: {vals[1]}\nSlot: {vals[2]}\nColor: {vals[3]}")

    def refresh(self):
        """Public refresh method."""
        self._refresh_all_tools()
