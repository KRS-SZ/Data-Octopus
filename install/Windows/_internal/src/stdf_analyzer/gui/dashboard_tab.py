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

    MANIFOLD_BASE = "odin_archive/tree/manifold/hwte-quantum_prod/mfghwteste-quantum_prod/tuskar/uled/incoming/tool_data"

    TOOLS = {
        "ATE": ["9ATE1", "9ATE2", "9ATE3", "9ATE4"],
        "Prober": ["9PRB3", "9PRF3"]
    }

    COLORS = {
        "header_bg": "#1565C0",
        "header_fg": "#FFFFFF",
        "bg": "#ECEFF1",
        "card_bg": "#FFFFFF",
        "ate": "#2196F3",
        "prober": "#9C27B0",
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
        self.total_tools = 6

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
        """Create tool status cards."""
        section = tk.Frame(self.content, bg=self.COLORS["bg"])
        section.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(section, text="🔧 TOOL STATUS", font=("Segoe UI", 12, "bold"),
                 bg=self.COLORS["bg"], fg="#37474F").pack(anchor=tk.W, pady=(0,8))

        cards = tk.Frame(section, bg=self.COLORS["bg"])
        cards.pack(fill=tk.X)

        col = 0
        for cat, tools in self.TOOLS.items():
            for tool in tools:
                self._create_tool_card(cards, tool, cat, col)
                col += 1

    def _create_tool_card(self, parent, name: str, cat: str, col: int):
        """Create a single tool card."""
        color = self.COLORS["ate"] if cat == "ATE" else self.COLORS["prober"]
        icon = "🔧" if cat == "ATE" else "🔬"

        card = tk.Frame(parent, bg="white", relief=tk.RIDGE, bd=1, width=150, height=120)
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

        self.tool_cards[name] = {"status": status, "wafer": wafer, "time": time_lbl, "count": count}

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

        # Chart 2: Color Distribution
        self._create_chart(charts, "colors", "🎨 Color Distribution", 0, 1)

        # Chart 3: Timeline
        self._create_chart(charts, "timeline", "📅 Activity Timeline", 1, 0)

        # Chart 4: Lots per Tool
        self._create_chart(charts, "lots", "📦 Lots per Tool", 1, 1)

        for i in range(2):
            charts.grid_columnconfigure(i, weight=1, uniform="chart")
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
        for cat, tools in self.TOOLS.items():
            for tool in tools:
                rb = tk.Radiobutton(left, text=tool, variable=self.lot_tool_var, value=tool,
                                   command=self._update_lot_details, bg="white", font=("Segoe UI", 9))
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
                threading.Thread(target=self._fetch_tool, args=(tool,), daemon=True).start()

    def _fetch_tool(self, tool: str):
        """Fetch data for one tool."""
        try:
            cmd = f'manifold --vip ls {self.MANIFOLD_BASE}/{tool}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                files = self._parse_output(result.stdout, tool)
                self.frame.after(0, lambda: self._update_tool(tool, files))
            else:
                self.frame.after(0, lambda: self._update_tool_error(tool))
        except:
            self.frame.after(0, lambda: self._update_tool_error(tool))

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

        tools = list(self.TOOLS["ATE"]) + list(self.TOOLS["Prober"])
        vals = [len(self.tool_data.get(t, [])) for t in tools]
        colors = [self.COLORS["ate"]]*4 + [self.COLORS["prober"]]*2

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
        """Pie chart: Color distribution."""
        c = self.chart_canvases.get("colors")
        if not c:
            return
        ax = c["ax"]
        ax.clear()

        counts = Counter(w.get("color", "---") for w in self.all_wafers)
        if not counts:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=10, color='#9E9E9E')
            ax.axis('off')
        else:
            labels, sizes = zip(*counts.items())
            colors = [self.WAFER_COLORS.get(l, "#9E9E9E") for l in labels]
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90, textprops={'fontsize': 8})
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

        tools = list(self.TOOLS["ATE"]) + list(self.TOOLS["Prober"])
        lot_counts = []
        for t in tools:
            lots = set(w.get("lot") for w in self.tool_data.get(t, []) if w.get("lot") != "---")
            lot_counts.append(len(lots))

        colors = [self.COLORS["ate"]]*4 + [self.COLORS["prober"]]*2
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
