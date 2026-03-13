"""
Filemanipulator Tab Module for Data Octopus v6.3.0

Merge multiple CSV/STDF files into a single output file.
Use case: Wafer data split across multiple files (e.g., 6 X,Y coordinate files)
→ merge into 1 CSV or 1 STDF file.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import re
import struct
import threading
from datetime import datetime
from typing import List, Optional, Dict, Tuple


class FilemanipulatorTab:
    """Filemanipulator Tab - Merge multiple CSV/STDF files into one."""

    SUPPORTED_EXTENSIONS = ('.csv', '.stdf', '.std', '.txt')

    def __init__(self, parent_notebook: ttk.Notebook, tab_frame: tk.Frame):
        self.parent = parent_notebook
        self.frame = tab_frame
        self.file_list: List[str] = []
        self.file_info: Dict[str, dict] = {}
        self.merged_df: Optional[pd.DataFrame] = None

        self._create_widgets()

    def _create_widgets(self):
        """Create all Filemanipulator widgets."""
        # Header
        header = tk.Frame(self.frame, bg="#1565C0", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="🔧 Filemanipulator – Merge Multiple Files",
            font=("Segoe UI", 14, "bold"), fg="white", bg="#1565C0"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        # Main content
        main_frame = tk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Left panel: File list
        left_frame = tk.LabelFrame(main_frame, text="Input Files", font=("Segoe UI", 10, "bold"))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Buttons row
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(
            btn_frame, text="➕ Add Files", command=self._add_files,
            font=("Segoe UI", 9), bg="#4CAF50", fg="white", width=12
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame, text="📁 Add Folder", command=self._add_folder,
            font=("Segoe UI", 9), bg="#2196F3", fg="white", width=12
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame, text="❌ Remove", command=self._remove_selected,
            font=("Segoe UI", 9), bg="#F44336", fg="white", width=10
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame, text="🗑 Clear All", command=self._clear_all,
            font=("Segoe UI", 9), width=10
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame, text="🔼", command=self._move_up,
            font=("Segoe UI", 9), width=3
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame, text="🔽", command=self._move_down,
            font=("Segoe UI", 9), width=3
        ).pack(side=tk.LEFT, padx=2)

        # File listbox with scrollbar
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.file_listbox = tk.Listbox(
            list_frame, font=("Consolas", 9), selectmode=tk.EXTENDED,
            activestyle='dotbox'
        )
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)

        # File count label
        self.file_count_label = tk.Label(
            left_frame, text="0 files loaded",
            font=("Segoe UI", 9), fg="gray"
        )
        self.file_count_label.pack(pady=(0, 5))

        # Right panel: Preview + Actions
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # File info panel
        info_frame = tk.LabelFrame(right_frame, text="File Info", font=("Segoe UI", 10, "bold"))
        info_frame.pack(fill=tk.X, pady=(0, 5))

        self.info_text = tk.Text(
            info_frame, font=("Consolas", 9), height=8, wrap=tk.WORD,
            state=tk.DISABLED, bg="#F5F5F5"
        )
        self.info_text.pack(fill=tk.X, padx=5, pady=5)

        # Merge options
        options_frame = tk.LabelFrame(right_frame, text="Merge Options", font=("Segoe UI", 10, "bold"))
        options_frame.pack(fill=tk.X, pady=5)

        # Output format
        fmt_frame = tk.Frame(options_frame)
        fmt_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(fmt_frame, text="Output Format:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="CSV (.csv)")
        self.format_combo = ttk.Combobox(
            fmt_frame, textvariable=self.format_var, state="readonly", width=25,
            values=["CSV (.csv)", "STDF (.stdf) – binary merge"]
        )
        self.format_combo.pack(side=tk.LEFT, padx=10)

        # Duplicate handling (only for CSV)
        dup_frame = tk.Frame(options_frame)
        dup_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(dup_frame, text="Duplicate Rows:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.dup_var = tk.StringVar(value="keep")
        self.dup_combo = ttk.Combobox(
            dup_frame, textvariable=self.dup_var, state="readonly", width=25,
            values=["keep", "remove duplicates", "remove by X/Y coords"]
        )
        self.dup_combo.pack(side=tk.LEFT, padx=10)

        # Extract X/Y from folder name checkbox
        xy_frame = tk.Frame(options_frame)
        xy_frame.pack(fill=tk.X, padx=10, pady=5)
        self.extract_xy_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            xy_frame, text="📍 Extract X/Y from folder name (e.g. red_01_X45Y28 → X=45, Y=28)",
            variable=self.extract_xy_var, font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)

        # Merge PLM folders checkbox
        plm_frame = tk.Frame(options_frame)
        plm_frame.pack(fill=tk.X, padx=10, pady=5)
        self.merge_plm_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            plm_frame, text="📁 Merge PLM folders (copy & rename X/Y in filenames)",
            variable=self.merge_plm_var, font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)

        # Merge button
        merge_frame = tk.Frame(right_frame)
        merge_frame.pack(fill=tk.X, pady=10)

        self.merge_btn = tk.Button(
            merge_frame, text="🔗 MERGE FILES", command=self._merge_files,
            font=("Segoe UI", 12, "bold"), bg="#1565C0", fg="white",
            height=2, cursor="hand2"
        )
        self.merge_btn.pack(fill=tk.X, padx=10)

        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            merge_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = tk.Label(
            merge_frame, text="Ready – add files to start",
            font=("Segoe UI", 9), fg="gray"
        )
        self.status_label.pack()

        # Preview panel
        preview_frame = tk.LabelFrame(right_frame, text="Merge Preview", font=("Segoe UI", 10, "bold"))
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.preview_text = tk.Text(
            preview_frame, font=("Consolas", 8), wrap=tk.NONE,
            state=tk.DISABLED, bg="#FAFAFA"
        )
        preview_scroll_y = tk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scroll_x = tk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=preview_scroll_y.set, xscrollcommand=preview_scroll_x.set)
        preview_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        preview_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    # ── File Management ──────────────────────────────────────────────

    def _add_files(self):
        """Add files via file dialog."""
        files = filedialog.askopenfilenames(
            title="Select CSV/STDF files to merge",
            filetypes=[
                ("Supported Files", "*.csv *.stdf *.std *.txt"),
                ("CSV Files", "*.csv"),
                ("STDF Files", "*.stdf *.std"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ]
        )
        if files:
            self._load_files(list(files))

    def _add_folder(self):
        """Add all supported files from a folder."""
        folder = filedialog.askdirectory(title="Select folder with files to merge")
        if folder:
            files = []
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(self.SUPPORTED_EXTENSIONS):
                    files.append(os.path.join(folder, f))
            if files:
                self._load_files(files)
            else:
                messagebox.showinfo("No Files", f"No supported files found in:\n{folder}")

    def _load_files(self, file_paths: List[str]):
        """Load file info and add to list."""
        added = 0
        for fp in file_paths:
            if fp in self.file_list:
                continue
            try:
                info = self._get_file_info(fp)
                self.file_list.append(fp)
                self.file_info[fp] = info
                added += 1
            except Exception as e:
                print(f"Error loading {fp}: {e}")

        if added > 0:
            self._refresh_listbox()
            self._update_status(f"Added {added} file(s)")

    def _get_file_info(self, filepath: str) -> dict:
        """Get basic info about a file."""
        info = {
            'path': filepath,
            'name': os.path.basename(filepath),
            'size': os.path.getsize(filepath),
            'ext': os.path.splitext(filepath)[1].lower(),
            'rows': 0,
            'columns': 0,
            'col_names': [],
        }

        # Try to extract X/Y from path
        xy = self._extract_xy_from_path(filepath)
        if xy:
            info['xy'] = xy

        ext = info['ext']
        if ext in ('.csv', '.txt'):
            try:
                df = pd.read_csv(filepath, nrows=0)
                info['col_names'] = list(df.columns)
                info['columns'] = len(df.columns)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    info['rows'] = sum(1 for _ in f) - 1
            except Exception as e:
                info['error'] = str(e)
        elif ext in ('.stdf', '.std'):
            info['is_stdf'] = True
            # Count PRR records (= number of dies)
            try:
                prr_count = self._count_stdf_prr(filepath)
                info['rows'] = prr_count
            except Exception:
                info['rows'] = -1

        return info

    def _count_stdf_prr(self, filepath: str) -> int:
        """Count PRR records in STDF file (= number of tested dies)."""
        count = 0
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            pos = 0
            while pos + 4 <= len(data):
                rec_len = struct.unpack('<H', data[pos:pos + 2])[0]
                rec_typ = data[pos + 2]
                rec_sub = data[pos + 3]
                if rec_typ == 5 and rec_sub == 20:  # PRR
                    count += 1
                pos += 4 + rec_len
        except Exception:
            return -1
        return count

    def _remove_selected(self):
        """Remove selected files from list."""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        for idx in reversed(selection):
            fp = self.file_list[idx]
            del self.file_info[fp]
            del self.file_list[idx]
        self._refresh_listbox()

    def _clear_all(self):
        """Clear all files."""
        self.file_list.clear()
        self.file_info.clear()
        self.merged_df = None
        self._refresh_listbox()
        self._set_info_text("")
        self._set_preview_text("")
        self._update_status("Cleared – add files to start")

    def _move_up(self):
        sel = self.file_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.file_list[idx], self.file_list[idx - 1] = self.file_list[idx - 1], self.file_list[idx]
        self._refresh_listbox()
        self.file_listbox.selection_set(idx - 1)

    def _move_down(self):
        sel = self.file_listbox.curselection()
        if not sel or sel[0] >= len(self.file_list) - 1:
            return
        idx = sel[0]
        self.file_list[idx], self.file_list[idx + 1] = self.file_list[idx + 1], self.file_list[idx]
        self._refresh_listbox()
        self.file_listbox.selection_set(idx + 1)

    def _refresh_listbox(self):
        """Refresh the file listbox display."""
        self.file_listbox.delete(0, tk.END)
        total_rows = 0
        for i, fp in enumerate(self.file_list):
            info = self.file_info.get(fp, {})
            name = info.get('name', os.path.basename(fp))
            rows = info.get('rows', '?')
            size_kb = info.get('size', 0) / 1024
            ext = info.get('ext', '').upper().replace('.', '')

            if rows == -1:
                row_str = "STDF"
            elif isinstance(rows, int):
                row_str = f"{rows:,} dies" if info.get('is_stdf') else f"{rows:,} rows"
                total_rows += rows
            else:
                row_str = "?"

            display = f"  {i + 1:2d}. [{ext:4s}] {name:<40s}  {row_str:>12s}  ({size_kb:,.1f} KB)"
            xy = info.get('xy')
            if xy:
                display += f"  📍 X={xy[0]}, Y={xy[1]}"
            self.file_listbox.insert(tk.END, display)
            bg = "#FFFFFF" if i % 2 == 0 else "#F0F4F8"
            self.file_listbox.itemconfigure(i, bg=bg)

        self.file_count_label.configure(
            text=f"{len(self.file_list)} files loaded ({total_rows:,} total)"
        )

    def _on_file_select(self, event=None):
        """Show info about selected file."""
        sel = self.file_listbox.curselection()
        if not sel:
            return
        fp = self.file_list[sel[0]]
        info = self.file_info.get(fp, {})

        rows = info.get('rows', '?')
        if isinstance(rows, int) and rows >= 0:
            row_str = f"{rows:,}"
        else:
            row_str = "(requires parsing)"

        lines = [
            f"File:     {info.get('name', '?')}",
            f"Path:     {fp}",
            f"Size:     {info.get('size', 0) / 1024:,.1f} KB",
            f"Type:     {info.get('ext', '?').upper()}",
            f"{'Dies' if info.get('is_stdf') else 'Rows'}:     {row_str}",
            f"Columns:  {info.get('columns', 'n/a' if info.get('is_stdf') else '?')}",
        ]
        if info.get('col_names'):
            lines.append(f"\nColumns:\n  " + "\n  ".join(info['col_names'][:20]))

        self._set_info_text("\n".join(lines))

    # ── X/Y Extraction from Path ────────────────────────────────────

    def _extract_xy_from_path(self, filepath: str) -> Optional[Tuple[int, int]]:
        """Extract X/Y coordinates from folder or file name.

        Patterns matched:
          red_01_X45Y28  → (45, 28)
          X40Y40         → (40, 40)
          _X47_Y30_      → (47, 30)
        """
        # Search in parent folder name first, then filename
        folder_name = os.path.basename(os.path.dirname(filepath))
        file_name = os.path.basename(filepath)

        for name in [folder_name, os.path.dirname(filepath), file_name]:
            # Pattern: X<num>Y<num> (most common: red_01_X45Y28)
            m = re.search(r'X(\d+)[_]?Y(\d+)', name, re.IGNORECASE)
            if m:
                return int(m.group(1)), int(m.group(2))
            # Pattern: X_<num>_Y_<num>
            m = re.search(r'X[_]?(\d+)[_]+Y[_]?(\d+)', name, re.IGNORECASE)
            if m:
                return int(m.group(1)), int(m.group(2))
        return None

    def _patch_prr_xy(self, record_bytes: bytes, x: int, y: int) -> bytes:
        """Patch X_COORD and Y_COORD in a PRR record (binary).

        PRR layout after 4-byte header:
          +0  HEAD_NUM  U*1
          +1  SITE_NUM  U*1
          +2  PART_FLG  B*1
          +3  NUM_TEST  U*2
          +5  HARD_BIN  U*2
          +7  SOFT_BIN  U*2
          +9  X_COORD   I*2  ← patch here
          +11 Y_COORD   I*2  ← patch here
        """
        ba = bytearray(record_bytes)
        x_offset = 4 + 9   # 4 header + 9 data bytes
        y_offset = 4 + 11
        if len(ba) >= y_offset + 2:
            struct.pack_into('<h', ba, x_offset, x)
            struct.pack_into('<h', ba, y_offset, y)
        return bytes(ba)

    # ── Merge Logic ──────────────────────────────────────────────────

    def _merge_files(self):
        """Merge all loaded files into one."""
        if len(self.file_list) < 2:
            messagebox.showwarning("Not Enough Files", "Please add at least 2 files to merge.")
            return

        self.merge_btn.configure(state=tk.DISABLED, text="⏳ Merging...")
        self._update_status("Merging files...")
        self.progress_var.set(0)

        fmt = self.format_var.get()

        if "STDF" in fmt:
            # Check all files are STDF
            all_stdf = all(
                self.file_info.get(fp, {}).get('ext', '') in ('.stdf', '.std')
                for fp in self.file_list
            )
            if not all_stdf:
                messagebox.showwarning(
                    "Format Mismatch",
                    "STDF output requires ALL input files to be STDF (.stdf/.std).\n"
                    "Use CSV output for mixed file types."
                )
                self._reset_merge_btn()
                return
            thread = threading.Thread(target=self._do_stdf_binary_merge, daemon=True)
        else:
            thread = threading.Thread(target=self._do_csv_merge, daemon=True)

        thread.start()

    # ── STDF Binary Merge ────────────────────────────────────────────

    def _do_stdf_binary_merge(self):
        """Merge STDF files at binary level – preserves original data perfectly."""
        try:
            # Ask for save path on main thread
            self.frame.after(0, lambda: self._save_stdf_binary())
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", f"STDF merge failed:\n{e}"))
            self.frame.after(0, self._reset_merge_btn)

    def _save_stdf_binary(self):
        """Choose save path and perform STDF binary merge."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"merged_{len(self.file_list)}files_{timestamp}.stdf"

        filepath = filedialog.asksaveasfilename(
            title="Save Merged STDF File",
            defaultextension=".stdf",
            initialfile=default_name,
            filetypes=[("STDF Files", "*.stdf *.std"), ("All Files", "*.*")]
        )
        if not filepath:
            self._reset_merge_btn()
            return

        thread = threading.Thread(
            target=self._perform_stdf_merge, args=(filepath,), daemon=True
        )
        thread.start()

    def _perform_stdf_merge(self, output_path: str):
        """Binary STDF merge: keep headers from file 1, append die data from all files."""
        try:
            # Per-part data record types (PIR, PRR, PTR, MPR, FTR)
            part_data_types = {(5, 10), (5, 20), (15, 10), (15, 20), (15, 30)}

            total_files = len(self.file_list)
            total_dies = 0
            extract_xy = self.extract_xy_var.get()
            xy_info = []
            mrr_bytes = None

            with open(output_path, 'wb') as out:
                for file_idx, fp in enumerate(self.file_list):
                    fname = os.path.basename(fp)
                    self.frame.after(0, lambda f=fname: self._update_status(f"Reading: {f}"))

                    # Extract X/Y from path if checkbox is enabled
                    xy = self._extract_xy_from_path(fp) if extract_xy else None

                    with open(fp, 'rb') as f:
                        data = f.read()

                    pos = 0
                    file_dies = 0
                    records_written = 0

                    while pos + 4 <= len(data):
                        rec_len = struct.unpack('<H', data[pos:pos + 2])[0]
                        rec_typ = data[pos + 2]
                        rec_sub = data[pos + 3]
                        record_bytes = data[pos:pos + 4 + rec_len]
                        pos += 4 + rec_len

                        # Patch PRR with X/Y coordinates if enabled
                        if rec_typ == 5 and rec_sub == 20:  # PRR
                            file_dies += 1
                            if xy:
                                record_bytes = self._patch_prr_xy(record_bytes, xy[0], xy[1])

                        if file_idx == 0:
                            # File 1: write everything EXCEPT MRR (save for end)
                            if (rec_typ, rec_sub) == (1, 20):  # MRR
                                mrr_bytes = record_bytes
                                continue
                            out.write(record_bytes)
                            records_written += 1
                        else:
                            # Files 2+: only write per-part data records
                            if (rec_typ, rec_sub) in part_data_types:
                                out.write(record_bytes)
                                records_written += 1

                    total_dies += file_dies
                    xy_str = f" → X={xy[0]}, Y={xy[1]}" if xy else ""
                    xy_info.append(f"  {file_idx + 1}. {fname} ({file_dies} dies{xy_str})")
                    progress = ((file_idx + 1) / total_files) * 90
                    self.frame.after(0, lambda p=progress: self.progress_var.set(p))
                    print(f"  {fname}: {file_dies} dies, {records_written} records{xy_str}")

                # Write MRR at the very end
                if mrr_bytes:
                    out.write(mrr_bytes)

            file_size = os.path.getsize(output_path)
            self.frame.after(0, lambda: self.progress_var.set(95))

            # Merge PLM folders if checkbox is enabled
            plm_count = 0
            plm_summary = []
            plm_output = ""
            if self.merge_plm_var.get():
                self.frame.after(0, lambda: self._update_status("Copying PLM files..."))
                plm_count, plm_summary, plm_output = self._merge_plm_folders(output_path)

            self.frame.after(0, lambda: self.progress_var.set(100))
            self.frame.after(0, lambda: self._update_status(
                f"✅ Saved: {os.path.basename(output_path)} ({total_dies:,} dies, {file_size / 1024:,.1f} KB)"
            ))

            preview = [
                "=== STDF BINARY MERGE RESULT ===",
                f"Files merged:  {total_files}",
                f"Total dies:    {total_dies:,}",
                f"Output size:   {file_size / 1024:,.1f} KB",
                f"Output:        {output_path}",
            ]
            if plm_count > 0:
                preview.append(f"\n=== PLM FILES ({plm_count} copied) ===")
                preview.append(f"PLM folder:    {plm_output}")
                preview.extend(plm_summary)
            preview.append("")
            preview.append("=== SOURCE FILES ===")
            for info_line in xy_info:
                preview.append(info_line)

            plm_msg = f"\nPLM files: {plm_count} copied to PLMFiles/" if plm_count > 0 else ""
            self.frame.after(0, lambda: self._set_preview_text("\n".join(preview)))
            self.frame.after(0, lambda: messagebox.showinfo(
                "STDF Merge Complete",
                f"Successfully merged {total_files} STDF files!\n\n"
                f"Total dies: {total_dies:,}\n"
                f"Output size: {file_size / 1024:,.1f} KB\n"
                f"Saved to: {output_path}"
                f"{plm_msg}"
            ))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.frame.after(0, lambda: messagebox.showerror("STDF Merge Error", f"Error:\n{e}"))
        finally:
            self.frame.after(0, self._reset_merge_btn)

    # ── CSV Merge ────────────────────────────────────────────────────

    def _do_csv_merge(self):
        """Merge files into CSV (parses STDF to DataFrame first)."""
        try:
            dataframes = []
            total = len(self.file_list)

            for i, fp in enumerate(self.file_list):
                info = self.file_info.get(fp, {})
                ext = info.get('ext', '').lower()
                fname = os.path.basename(fp)

                self.frame.after(0, lambda f=fname: self._update_status(f"Reading: {f}"))

                df = None
                if ext in ('.csv', '.txt'):
                    df = self._read_csv_file(fp)
                elif ext in ('.stdf', '.std'):
                    df = self._read_stdf_to_dataframe(fp)

                if df is not None and len(df) > 0:
                    # Inject X/Y from folder name if checkbox enabled
                    if self.extract_xy_var.get():
                        xy = self._extract_xy_from_path(fp)
                        if xy:
                            df['X_COORD'] = xy[0]
                            df['Y_COORD'] = xy[1]
                            print(f"    → X/Y from path: X={xy[0]}, Y={xy[1]}")
                    df['_source_file'] = fname
                    dataframes.append(df)
                    print(f"  {fname}: {len(df)} rows, {len(df.columns)} columns")

                progress = ((i + 1) / total) * 80
                self.frame.after(0, lambda p=progress: self.progress_var.set(p))

            if not dataframes:
                self.frame.after(0, lambda: messagebox.showerror(
                    "Error", "No data could be read from the files."
                ))
                self.frame.after(0, self._reset_merge_btn)
                return

            self.frame.after(0, lambda: self._update_status("Concatenating..."))
            merged = pd.concat(dataframes, ignore_index=True)

            # Handle duplicates
            dup_mode = self.dup_var.get()
            if dup_mode == "remove duplicates":
                cols = [c for c in merged.columns if c != '_source_file']
                before = len(merged)
                merged = merged.drop_duplicates(subset=cols, keep='first')
                print(f"Removed {before - len(merged)} duplicate rows")
            elif dup_mode == "remove by X/Y coords":
                xy_cols = self._find_xy_columns(merged)
                if xy_cols:
                    before = len(merged)
                    merged = merged.drop_duplicates(subset=xy_cols, keep='first')
                    print(f"Removed {before - len(merged)} duplicates by {xy_cols}")

            self.merged_df = merged
            self.frame.after(0, lambda: self.progress_var.set(90))
            self.frame.after(0, lambda: self._save_csv(merged))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.frame.after(0, lambda: messagebox.showerror("Merge Error", f"Error:\n{e}"))
            self.frame.after(0, self._reset_merge_btn)

    def _read_csv_file(self, filepath: str) -> Optional[pd.DataFrame]:
        """Read a CSV file into a DataFrame."""
        try:
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(filepath, sep=sep, engine='python')
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
            return pd.read_csv(filepath, sep=None, engine='python')
        except Exception as e:
            print(f"Error reading CSV {filepath}: {e}")
            return None

    def _read_stdf_to_dataframe(self, filepath: str) -> Optional[pd.DataFrame]:
        """Read STDF file into DataFrame using Semi_ATE.STDF (same API as main app)."""
        try:
            import Semi_ATE.STDF as stdf_module

            rows = []
            test_info = {}
            current_die_tests = {}

            with open(filepath, 'rb') as f:
                for record in stdf_module.records_from_file(f):
                    rec_type = type(record).__name__

                    if rec_type == "PIR":
                        current_die_tests = {}

                    elif rec_type == "PTR":
                        test_num = None
                        result = None

                        if hasattr(record, "get_value"):
                            test_num = record.get_value("TEST_NUM")
                            result = record.get_value("RESULT")
                        elif hasattr(record, "TEST_NUM"):
                            test_num = record.TEST_NUM
                            result = getattr(record, "RESULT", None)

                        if test_num is not None:
                            if test_num not in test_info:
                                test_name = None
                                if hasattr(record, "get_value"):
                                    test_name = record.get_value("TEST_TXT")
                                elif hasattr(record, "TEST_TXT"):
                                    test_name = record.TEST_TXT
                                if test_name:
                                    test_info[test_num] = test_name

                            if result is not None:
                                current_die_tests[test_num] = result

                    elif rec_type == "PRR":
                        x_coord = y_coord = hard_bin = soft_bin = None

                        if hasattr(record, "get_value"):
                            x_coord = record.get_value("X_COORD")
                            y_coord = record.get_value("Y_COORD")
                            hard_bin = record.get_value("HARD_BIN")
                            soft_bin = record.get_value("SOFT_BIN")
                        elif hasattr(record, "X_COORD"):
                            x_coord = record.X_COORD
                            y_coord = getattr(record, "Y_COORD", None)
                            hard_bin = getattr(record, "HARD_BIN", None)
                            soft_bin = getattr(record, "SOFT_BIN", None)

                        die = {
                            'X_COORD': x_coord,
                            'Y_COORD': y_coord,
                            'HARD_BIN': hard_bin,
                            'SOFT_BIN': soft_bin,
                        }
                        die.update(current_die_tests)
                        rows.append(die)
                        current_die_tests = {}

            if rows:
                df = pd.DataFrame(rows)
                # Rename test columns to names
                rename_map = {num: name for num, name in test_info.items() if num in df.columns}
                if rename_map:
                    df = df.rename(columns=rename_map)
                return df

            print(f"No die data found in STDF: {filepath}")
            return None

        except ImportError:
            print("Semi_ATE.STDF not available for CSV conversion")
            return None
        except Exception as e:
            print(f"Error reading STDF {filepath}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _find_xy_columns(self, df: pd.DataFrame) -> Optional[List[str]]:
        """Find X/Y coordinate columns in DataFrame."""
        col_lower = {c.lower(): c for c in df.columns}
        for xp, yp in [('x_coord', 'y_coord'), ('x', 'y'), ('die_x', 'die_y'), ('col', 'row')]:
            if xp in col_lower and yp in col_lower:
                return [col_lower[xp], col_lower[yp]]
        return None

    def _save_csv(self, merged_df: pd.DataFrame):
        """Save merged DataFrame as CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"merged_{len(self.file_list)}files_{timestamp}.csv"

        filepath = filedialog.asksaveasfilename(
            title="Save Merged CSV File",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            self._reset_merge_btn()
            return

        try:
            merged_df.to_csv(filepath, index=False)
            self.progress_var.set(95)

            # Merge PLM folders if checkbox is enabled
            plm_count = 0
            plm_summary = []
            plm_output = ""
            if self.merge_plm_var.get():
                self._update_status("Copying PLM files...")
                plm_count, plm_summary, plm_output = self._merge_plm_folders(filepath)

            self.progress_var.set(100)
            self._update_status(f"✅ Saved: {os.path.basename(filepath)} ({len(merged_df):,} rows)")

            preview = [
                "=== CSV MERGE RESULT ===",
                f"Files merged: {len(self.file_list)}",
                f"Total rows:   {len(merged_df):,}",
                f"Columns:      {len(merged_df.columns)}",
                f"Output:       {filepath}",
            ]
            if plm_count > 0:
                preview.append(f"\n=== PLM FILES ({plm_count} copied) ===")
                preview.append(f"PLM folder:   {plm_output}")
                preview.extend(plm_summary)
            preview.append("")
            preview.append("=== FIRST 20 ROWS ===")
            preview.append(merged_df.head(20).to_string(index=False))
            self._set_preview_text("\n".join(preview))

            plm_msg = f"\nPLM files: {plm_count} copied to PLMFiles/" if plm_count > 0 else ""
            messagebox.showinfo(
                "CSV Merge Complete",
                f"Successfully merged {len(self.file_list)} files!\n\n"
                f"Rows: {len(merged_df):,}\n"
                f"Columns: {len(merged_df.columns)}\n"
                f"Saved to: {filepath}"
                f"{plm_msg}"
            )
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving file:\n{e}")
        finally:
            self._reset_merge_btn()

    # ── PLM Folder Merge ─────────────────────────────────────────────

    def _find_plm_dir(self, filepath: str) -> Optional[str]:
        """Find PLM folder relative to a STDF/CSV file.

        Searches: same_dir/plm, parent/plm, grandparent/plm
        """
        base = os.path.dirname(filepath)
        for candidate in [
            os.path.join(base, 'plm'),
            os.path.join(os.path.dirname(base), 'plm'),
            os.path.join(os.path.dirname(os.path.dirname(base)), 'plm'),
        ]:
            if os.path.isdir(candidate):
                return candidate
        return None

    def _merge_plm_folders(self, output_path: str):
        """Copy & rename PLM files from all source folders into one PLMFiles/ directory.

        - Creates PLMFiles/ next to the merge output file
        - Renames X-32768_Y-32768 to actual X/Y from folder name
        - Flat structure so the app's find_plm_files() can match them
        """
        import shutil

        output_dir = os.path.dirname(output_path)
        plm_output = os.path.join(output_dir, 'PLMFiles')
        os.makedirs(plm_output, exist_ok=True)

        total_copied = 0
        plm_summary = []

        for fp in self.file_list:
            plm_dir = self._find_plm_dir(fp)
            if not plm_dir:
                continue

            xy = self._extract_xy_from_path(fp) if self.extract_xy_var.get() else None
            if not xy:
                continue

            x, y = xy
            files_copied = 0

            # Walk through PLM directory (including subdirectories)
            for root, dirs, files in os.walk(plm_dir):
                for fname in files:
                    src = os.path.join(root, fname)

                    # Rename: replace X-32768 → X{actual}, Y-32768 → Y{actual}
                    new_name = fname
                    new_name = re.sub(r'X-32768', f'X{x}', new_name)
                    new_name = re.sub(r'Y-32768', f'Y{y}', new_name)
                    # Also handle positive zero: X0_Y0
                    new_name = re.sub(r'(?<=[_\-])X0(?=[_\-\.])', f'X{x}', new_name)
                    new_name = re.sub(r'(?<=[_\-])Y0(?=[_\-\.])', f'Y{y}', new_name)

                    dst = os.path.join(plm_output, new_name)

                    # Avoid overwriting if same name already exists
                    if os.path.exists(dst):
                        base_name, ext = os.path.splitext(new_name)
                        dst = os.path.join(plm_output, f"{base_name}_dup{ext}")

                    try:
                        shutil.copy2(src, dst)
                        files_copied += 1
                    except Exception as e:
                        print(f"    PLM copy error: {e}")

            total_copied += files_copied
            if files_copied > 0:
                plm_summary.append(f"  📍 X={x}, Y={y}: {files_copied} PLM files")
                print(f"  PLM: X={x}, Y={y} → {files_copied} files copied")

        return total_copied, plm_summary, plm_output

    # ── UI Helpers ───────────────────────────────────────────────────

    def _reset_merge_btn(self):
        self.merge_btn.configure(state=tk.NORMAL, text="🔗 MERGE FILES")

    def _update_status(self, text: str):
        self.status_label.configure(text=text)

    def _set_info_text(self, text: str):
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", text)
        self.info_text.configure(state=tk.DISABLED)

    def _set_preview_text(self, text: str):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state=tk.DISABLED)
