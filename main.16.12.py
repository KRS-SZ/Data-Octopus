#!/usr/bin/env python3
# Python
# from Semi_ATE.STDF.STDFFile import STDFFile

import sys

print(sys.executable)

import os

# Try to set MATPLOTLIBDATA for Meta environments
try:
    from libfb import parutil

    os.environ["MATPLOTLIBDATA"] = parutil.get_dir_path("matplotlib/mpl-data")
except ImportError:
    pass

import tkinter as tk
from tkinter import filedialog, ttk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk

# Robust STDF import - try to import the module
STDF_MODULE = None
STDF_TYPE = None

try:
    import Semi_ATE.STDF

    STDF_MODULE = Semi_ATE.STDF
    STDF_TYPE = "Semi_ATE"
    print(f"Successfully imported Semi_ATE.STDF module")
    print(
        f"Available functions: {[x for x in dir(STDF_MODULE) if not x.startswith('_')][:15]}"
    )
except ImportError as e:
    print(f"Failed to import Semi_ATE.STDF: {e}")
    try:
        import pystdf

        STDF_MODULE = pystdf
        STDF_TYPE = "pystdf"
        print("Successfully imported pystdf")
    except ImportError:
        print("Warning: No STDF library found. STDF file features will not work.")
        STDF_MODULE = None
        STDF_TYPE = None

import pandas as pd

print("Starting application...")

# Initialize empty data storage
data_arrays = []
file_names = []

# Language translations dictionary
TRANSLATIONS = {
    "en": {
        "window_title": "Measurement Data Visualization",
        "tab_plot": "Plot",
        "tab_boxplot": "Boxplot",
        "tab_probability": "Probability",
        "tab_images": "Images",
        "tab_wafermap": "Wafermap",
        "tab_stdf_heatmap": "STDF Heatmap",
        "select_measurement_files": "Select Measurement Files",
        "no_data_loaded": "No data loaded. Click 'Select Measurement Files' to begin.",
        "select_stdf_file": "Select STDF File",
        "file": "File:",
        "parameter": "Parameter:",
        "refresh": "Refresh",
        "load_multiple_stdf": "Load Multiple STDF Files",
        "no_stdf_loaded": "No STDF files loaded",
        "show_grid": "Show Grid",
        "select_images": "Select Image(s)",
        "zoom_in": "Zoom In",
        "zoom_out": "Zoom Out",
        "language": "Language:",
        "heatmap_title": "Heatmap:",
        "wafer": "Wafer",
        "x_coordinate": "X Coordinate",
        "y_coordinate": "Y Coordinate",
        "column_index": "Column Index",
        "row_index": "Row Index",
        "min": "Min",
        "max": "Max",
        "mean": "Mean",
        "median": "Median",
        "dies": "Dies",
        "die_coordinates": "Die Coordinates",
        "additional_info": "Additional Information",
        "bin": "Bin",
        "boxplot_title": "Boxplot of Each Dataset (with Mean and Median)",
        "dataset": "Dataset",
        "luminance_value": "Luminance Value",
        "probability_title": "Probability Plot of Measurement Values",
        "value": "Value",
        "probability": "Probability",
        "histogram_title": "Combined Histogram of Measurement Values",
        "frequency": "Frequency",
        "zoomed": "Zoomed",
        "die_info": "Die Information",
        "loaded_files": "Loaded {count} file(s)",
        "loaded_params": "Loaded: {count} parameters available",
    },
    "de": {
        "window_title": "Messdaten-Visualisierung",
        "tab_plot": "Diagramm",
        "tab_boxplot": "Boxplot",
        "tab_probability": "Wahrscheinlichkeit",
        "tab_images": "Bilder",
        "tab_wafermap": "Wafermap",
        "tab_stdf_heatmap": "STDF Heatmap",
        "select_measurement_files": "Messdateien auswählen",
        "no_data_loaded": "Keine Daten geladen. Klicken Sie auf 'Messdateien auswählen'.",
        "select_stdf_file": "STDF-Datei auswählen",
        "file": "Datei:",
        "parameter": "Parameter:",
        "refresh": "Aktualisieren",
        "load_multiple_stdf": "Mehrere STDF-Dateien laden",
        "no_stdf_loaded": "Keine STDF-Dateien geladen",
        "show_grid": "Raster anzeigen",
        "select_images": "Bild(er) auswählen",
        "zoom_in": "Vergrößern",
        "zoom_out": "Verkleinern",
        "language": "Sprache:",
        "heatmap_title": "Heatmap:",
        "wafer": "Wafer",
        "x_coordinate": "X-Koordinate",
        "y_coordinate": "Y-Koordinate",
        "column_index": "Spaltenindex",
        "row_index": "Zeilenindex",
        "min": "Min",
        "max": "Max",
        "mean": "Mittelwert",
        "median": "Median",
        "dies": "Dies",
        "die_coordinates": "Die-Koordinaten",
        "additional_info": "Zusätzliche Informationen",
        "bin": "Bin",
        "boxplot_title": "Boxplot der Datensätze (mit Mittelwert und Median)",
        "dataset": "Datensatz",
        "luminance_value": "Luminanzwert",
        "probability_title": "Wahrscheinlichkeitsdiagramm der Messwerte",
        "value": "Wert",
        "probability": "Wahrscheinlichkeit",
        "histogram_title": "Kombiniertes Histogramm der Messwerte",
        "frequency": "Häufigkeit",
        "zoomed": "Vergrößert",
        "die_info": "Die-Information",
        "loaded_files": "{count} Datei(en) geladen",
        "loaded_params": "Geladen: {count} Parameter verfügbar",
    },
}

# Current language
current_language = "en"


def get_text(key):
    """Get translated text for the current language"""
    return TRANSLATIONS.get(current_language, TRANSLATIONS["en"]).get(key, key)

# Create main Tkinter window with tabs and large tab font
print("Creating main window...")
main_win = tk.Tk()
main_win.title("Measurement Data Visualization")
main_win.geometry("1200x800")
print("Main window created successfully")

style = ttk.Style(main_win)
style.configure("TNotebook.Tab", font=("Helvetica", 20, "bold"))

# Top bar for language selection
top_bar = tk.Frame(main_win)
top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

language_label = tk.Label(top_bar, text="Language:", font=("Helvetica", 10))
language_label.pack(side=tk.RIGHT, padx=5)

language_var = tk.StringVar(value="English")
language_combobox = ttk.Combobox(
    top_bar,
    textvariable=language_var,
    values=["English", "Deutsch"],
    state="readonly",
    width=10,
    font=("Helvetica", 10),
)
language_combobox.pack(side=tk.RIGHT, padx=5)


def change_language(event=None):
    """Change the application language and update all UI elements"""
    global current_language

    selected_lang = language_var.get()
    current_language = "de" if selected_lang == "Deutsch" else "en"

    # Update window title
    main_win.title(get_text("window_title"))

    # Update tab names
    notebook.tab(tab7, text="Configuration")
    notebook.tab(tab6, text=get_text("tab_stdf_heatmap"))

    # Update buttons and labels
    select_multiple_stdf_button.config(text=get_text("load_multiple_stdf"))
    heatmap_param_label.config(text=get_text("parameter"))
    heatmap_refresh_button.config(text=get_text("refresh"))
    show_grid_checkbox.config(text=get_text("show_grid"))
    language_label.config(text=get_text("language"))

    print(f"Language changed to: {selected_lang}")


language_combobox.bind("<<ComboboxSelected>>", change_language)

notebook = ttk.Notebook(main_win)
notebook.pack(fill="both", expand=True)

# Tab 1: Configuration (moved to first position)
tab7 = ttk.Frame(notebook)
notebook.add(tab7, text="Configuration")

# Tab 2: STDF Heatmap with Parameter Selection
tab6 = ttk.Frame(notebook)
notebook.add(tab6, text="STDF Heatmap")

# Global variables for plot canvases
canvas1 = None
canvas1_hist = None
fig1 = None
fig1_hist = None
axes1 = None


def load_measurement_files():
    """Load measurement data files and update all visualizations"""
    global data_arrays, file_names, canvas1, canvas1_hist, fig1, fig1_hist, axes1

    file_paths = filedialog.askopenfilenames(
        title="Select one or more measurement data files",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
    )

    if not file_paths:
        print("No files selected.")
        return

    # Clear existing data
    data_arrays = []
    file_names = []

    # Load files
    for file_path in file_paths:
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            data_start = 0
            for i, line in enumerate(lines):
                if line.strip() and line[0].isdigit():
                    data_start = i
                    break

            raw_data = lines[data_start:]
            matrix = [
                list(map(float, row.strip().split(",")))
                for row in raw_data
                if row.strip()
            ]

            arr = np.array(matrix)
            data_arrays.append(arr)
            file_names.append(file_path.split("/")[-1])
            print(f"Loaded: {file_path.split('/')[-1]} - Shape: {arr.shape}")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if not data_arrays:
        print("No valid data files loaded.")
        return

    # Clear existing canvases
    if canvas1:
        canvas1.get_tk_widget().destroy()
    if canvas1_hist:
        canvas1_hist.get_tk_widget().destroy()
    if fig1:
        plt.close(fig1)
    if fig1_hist:
        plt.close(fig1_hist)

    # Create heatmap plots
    fig1, axes1 = plt.subplots(
        1, len(data_arrays), figsize=(8 * len(data_arrays), 8), constrained_layout=True
    )
    if len(data_arrays) == 1:
        axes1 = [axes1]

    for idx, arr in enumerate(data_arrays):
        ax = axes1[idx]
        im = ax.imshow(arr, cmap="viridis", aspect="equal")
        ax.set_title(f"Heatmap: {file_names[idx]}")
        ax.set_xlabel("Column Index")
        ax.set_ylabel("Row Index")
        fig1.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # Create histogram
    fig1_hist, ax_hist = plt.subplots(figsize=(8, 4))
    for idx, arr in enumerate(data_arrays):
        ax_hist.hist(arr.flatten(), bins=100, alpha=0.5, label=file_names[idx])
    ax_hist.set_title("Combined Histogram of Measurement Values")
    ax_hist.set_xlabel("Luminance Value")
    ax_hist.set_ylabel("Frequency")
    ax_hist.legend(loc="upper right")
    fig1_hist.tight_layout()

    # Create canvases
    canvas1 = FigureCanvasTkAgg(fig1, master=plot_frame)
    canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    canvas1_hist = FigureCanvasTkAgg(fig1_hist, master=plot_frame)
    canvas1_hist.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    # Connect double-click event
    canvas1.mpl_connect("button_press_event", on_subplot_doubleclick)

    # Update other tabs
    update_boxplot_tab()
    update_probability_tab()

    print(f"Successfully loaded {len(data_arrays)} file(s)")


def on_subplot_doubleclick(event):
    """Handle double-click on subplot to show zoomed view"""
    if event.dblclick and axes1 is not None:
        for idx, ax in enumerate(axes1):
            if event.inaxes == ax:
                arr = data_arrays[idx]
                title = file_names[idx]

                zoom_win = tk.Toplevel(main_win)
                zoom_win.title(f"Zoomed: {title}")

                fig_zoom, ax_zoom = plt.subplots(figsize=(16, 12))
                im_zoom = ax_zoom.imshow(arr, cmap="viridis", aspect="equal")
                ax_zoom.set_title(f"Zoomed: {title}")
                ax_zoom.set_xlabel("Column Index")
                ax_zoom.set_ylabel("Row Index")
                fig_zoom.colorbar(im_zoom, ax=ax_zoom, fraction=0.046, pad=0.04)

                canvas_zoom = FigureCanvasTkAgg(fig_zoom, master=zoom_win)
                canvas_zoom.get_tk_widget().pack(fill=tk.BOTH, expand=True)

                def on_close():
                    plt.close(fig_zoom)
                    zoom_win.destroy()

                zoom_win.protocol("WM_DELETE_WINDOW", on_close)
                break


def update_boxplot_tab():
    """Update boxplot visualization with mean and median values - NOT USED (tab deleted)"""
    pass


def update_probability_tab():
    """Update probability plot visualization - NOT USED (tab deleted)"""
    pass

wafermap_canvas = None
current_stdf_data = None
current_wafer_id = None
test_parameters = {}


def select_stdf_file():
    stdf_path = filedialog.askopenfilename(
        title="Select an STDF file",
        filetypes=[("STDF files", "*.stdf"), ("All files", "*.*")],
    )

    if stdf_path:
        load_stdf_data(stdf_path)
def read_wafermap_from_stdf(stdf_path):
    wafermap = []
    wafer_id = None
    test_params = {}

    if STDF_MODULE is None:
        print("\n" + "=" * 60)
        print("ERROR: STDF library not installed!")
        print("=" * 60)
        print("To use STDF wafermap features, install one of these libraries:")
        print("\nOption 1 (Recommended):")
        print("  pip install Semi-ATE-STDF")
        print("\nOption 2:")
        print("  pip install pystdf")
        print("\nAfter installation, restart the application.")
        print("=" * 60 + "\n")
        return pd.DataFrame(), None, {}

    try:
        if STDF_TYPE == "pystdf":
            wafermap, wafer_id, test_params = read_with_pystdf(stdf_path)
        else:
            print(f"Opening STDF file: {stdf_path}")
            print(f"Using STDF_TYPE: {STDF_TYPE}")

            test_info = {}
            current_die_tests = {}

            print("Reading STDF file (optimized)...")

            with open(stdf_path, "rb") as f:
                records_gen = STDF_MODULE.records_from_file(f)
                record_count = 0
                prr_count = 0
                ptr_count = 0
                record_types = {}

                for record in records_gen:
                    record_count += 1
                    if record_count % 100000 == 0:
                        print(f"Processed {record_count} records, {prr_count} dies...")

                    rec_type = type(record).__name__
                    record_types[rec_type] = record_types.get(rec_type, 0) + 1

                    if rec_type == "WIR":
                        try:
                            if hasattr(record, "WAFER_ID"):
                                wafer_id = record.WAFER_ID
                            else:
                                wafer_id = record.get_value("WAFER_ID")
                        except Exception as e:
                            print(f"Warning: Could not read WIR record: {e}")

                    elif rec_type == "PIR":
                        current_die_tests = {}

                    elif rec_type == "PTR":
                        ptr_count += 1
                        try:
                            if hasattr(record, "TEST_NUM"):
                                test_num = record.TEST_NUM
                                test_name = (
                                    record.TEST_TXT
                                    if hasattr(record, "TEST_TXT")
                                    else None
                                )
                                result = (
                                    record.RESULT if hasattr(record, "RESULT") else None
                                )
                            else:
                                test_num = record.get_value("TEST_NUM")
                                test_name = (
                                    record.get_value("TEST_TXT")
                                    if test_num is not None
                                    else None
                                )
                                result = (
                                    record.get_value("RESULT")
                                    if test_num is not None
                                    else None
                                )

                            if test_num is not None:
                                if test_num not in test_info and test_name:
                                    test_info[test_num] = test_name
                                if result is not None:
                                    current_die_tests[test_num] = result
                        except Exception as e:
                            if ptr_count <= 5:
                                print(
                                    f"Warning: Could not read PTR record #{ptr_count}: {e}"
                                )

                    elif rec_type == "PRR":
                        prr_count += 1
                        try:
                            if hasattr(record, "X_COORD") and hasattr(
                                record, "Y_COORD"
                            ):
                                x_coord = record.X_COORD
                                y_coord = record.Y_COORD
                            else:
                                x_coord = record.get_value("X_COORD")
                                y_coord = record.get_value("Y_COORD")

                            if x_coord is not None and y_coord is not None:
                                if hasattr(record, "HARD_BIN"):
                                    hard_bin = record.HARD_BIN
                                    soft_bin = (
                                        record.SOFT_BIN
                                        if hasattr(record, "SOFT_BIN")
                                        else None
                                    )
                                else:
                                    hard_bin = record.get_value("HARD_BIN")
                                    soft_bin = record.get_value("SOFT_BIN")

                                die_data = {
                                    "x": x_coord,
                                    "y": y_coord,
                                    "bin": hard_bin
                                    if hard_bin is not None
                                    else soft_bin,
                                }
                                die_data.update(current_die_tests)
                                wafermap.append(die_data)
                        except Exception as e:
                            if prr_count <= 5:
                                print(
                                    f"Warning: Could not read PRR record #{prr_count}: {e}"
                                )
                                print(f"  Record type: {type(record)}")
                                attrs = [
                                    attr
                                    for attr in dir(record)
                                    if not attr.startswith("_") and attr.isupper()
                                ]
                                print(f"  Available attributes: {attrs[:15]}")

                test_params = {f"test_{num}": name for num, name in test_info.items()}

                print(f"\n=== STDF File Summary ===")
                print(f"Total records processed: {record_count}")
                print(f"PRR records found: {prr_count}")
                print(f"PTR records found: {ptr_count}")
                print(f"Dies collected: {len(wafermap)}")
                print(f"Test parameters found: {len(test_params)}")
                print(f"Wafer ID: {wafer_id}")

                if prr_count == 0:
                    print("\nWARNING: No PRR (Part Result Records) found!")
                    print("This file may not contain wafer map data.")
                elif len(wafermap) == 0 and prr_count > 0:
                    print(
                        f"\nWARNING: Found {prr_count} PRR records but no valid dies!"
                    )
                    print("PRR records may be missing X_COORD or Y_COORD values.")

                print(f"\nRecord types found: {dict(sorted(record_types.items()))}")

        df = pd.DataFrame(wafermap)
        if len(df) > 0:
            print(f"Successfully loaded {len(df)} die records from STDF file")
            print(f"X range: {df['x'].min()} to {df['x'].max()}")
            print(f"Y range: {df['y'].min()} to {df['y'].max()}")
            print(f"Unique bins: {df['bin'].unique()}")
        else:
            print("WARNING: No die records found in STDF file")

        return df, wafer_id, test_params

    except Exception as e:
        print(f"Error reading STDF file: {e}")
        import traceback

        traceback.print_exc()
        return pd.DataFrame(), None, {}


def read_with_pystdf(stdf_path):
    import pystdf

    wafermap = []
    wafer_id = None
    test_params = {}
    test_info = {}
    current_die_tests = {}

    with open(stdf_path, "rb") as f:
        parser = pystdf.Parser(inp=f)

        for record in parser:
            if record.id == "WIR":
                wafer_id = record.WAFER_ID

            elif record.id == "PIR":
                current_die_tests = {}

            elif record.id == "PTR":
                try:
                    test_num = record.TEST_NUM
                    test_name = record.TEST_TXT
                    result = record.RESULT

                    if test_num is not None and test_name:
                        test_info[test_num] = test_name

                    if test_num is not None and result is not None:
                        current_die_tests[test_num] = result

                except (ValueError, KeyError, AttributeError) as e:
                    print(f"Warning: Could not read PTR record: {e}")

            elif record.id == "PRR":
                try:
                    if record.X_COORD is not None and record.Y_COORD is not None:
                        die_data = {
                            "x": record.X_COORD,
                            "y": record.Y_COORD,
                            "bin": record.HARD_BIN
                            if record.HARD_BIN is not None
                            else record.SOFT_BIN,
                        }

                        for test_num in current_die_tests:
                            die_data[f"test_{test_num}"] = current_die_tests[test_num]

                        wafermap.append(die_data)

                except (ValueError, KeyError, AttributeError) as e:
                    print(f"Warning: Could not read PRR record: {e}")

    test_params = {f"test_{num}": name for num, name in test_info.items()}

    return wafermap, wafer_id, test_params


def load_stdf_data(stdf_path):
    """Load STDF file and populate parameter selection"""
    global current_stdf_data, current_wafer_id, test_parameters

    df, wafer_id, test_params = read_wafermap_from_stdf(stdf_path)

    current_stdf_data = df
    current_wafer_id = wafer_id
    test_parameters = test_params

    param_options = ["BIN (Bin Number)"]
    for test_key, test_name in sorted(test_parameters.items()):
        param_options.append(f"{test_key}: {test_name}")

    param_combobox["values"] = param_options
    if param_options:
        param_combobox.current(0)

    print(f"Available parameters: {len(param_options)}")

    update_wafermap_with_parameter()
    update_heatmap_parameter_list()


def update_wafermap_with_parameter():
    """Update wafermap display based on selected parameter"""
    global current_stdf_data, current_wafer_id

    if current_stdf_data is None or current_stdf_data.empty:
        print("No STDF data loaded")
        return

    selected = param_combobox.get()
    print(f"\n=== Parameter Selection Debug ===")
    print(f"Selected from combobox: '{selected}'")

    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        # Extract test number from "test_XXXXX: Test Name" format
        test_key = selected.split(":")[0].strip()
        print(f"Extracted test_key: '{test_key}'")
        # Remove 'test_' prefix if present to get the actual column name
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label = selected
        print(f"Looking for column: {param_column} (type: {type(param_column).__name__})")

    print(f"Available columns (first 10): {list(current_stdf_data.columns[:10])}")
    print(f"Column types: {[type(col).__name__ for col in current_stdf_data.columns[:10]]}")

    update_wafermap_display(param_column, param_label)


def update_wafermap_display(parameter="bin", param_label="Bin"):
    """Display wafermap colored by specified parameter"""
    global wafermap_canvas, current_stdf_data, current_wafer_id

    fig, ax = plt.subplots(figsize=(10, 10))

    if current_stdf_data is not None and not current_stdf_data.empty:
        if parameter not in current_stdf_data.columns:
            ax.set_title(f"Parameter '{parameter}' not found in data")
            print(f"Available columns: {current_stdf_data.columns.tolist()}")
        else:
            plot_data = current_stdf_data.dropna(subset=[parameter])

            if len(plot_data) > 0:
                sc = ax.scatter(
                    plot_data["x"],
                    plot_data["y"],
                    c=plot_data[parameter],
                    cmap="viridis" if parameter != "bin" else "tab20",
                    s=80,
                    edgecolors="black",
                    linewidth=0.5,
                )

                ax.set_xlabel("X Coordinate", fontsize=12)
                ax.set_ylabel("Y Coordinate", fontsize=12)
                ax.set_title(
                    f"Wafermap for Wafer {current_wafer_id}\n{param_label}", fontsize=14
                )
                ax.grid(True, alpha=0.3)
                ax.set_aspect("equal")

                cbar = plt.colorbar(sc, ax=ax, label=param_label)
                cbar.ax.tick_params(labelsize=10)

                print(f"Plotted {len(plot_data)} dies with {parameter}")
                print(
                    f"Value range: {plot_data[parameter].min()} to {plot_data[parameter].max()}"
                )

            else:
                ax.set_title(f"No valid data for parameter '{param_label}'")
    else:
        ax.set_title("No wafermap data available")

    fig.tight_layout()

    if wafermap_canvas:
        wafermap_canvas.get_tk_widget().destroy()

    wafermap_canvas = FigureCanvasTkAgg(fig, master=wafermap_frame)
    wafermap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
    wafermap_canvas.draw()
# Tab 6: STDF Heatmap with Parameter Selection - Already created above, just add components

heatmap_canvas = None
current_heatmap_data = None
show_grid_var = tk.BooleanVar(value=False)
selected_die_coords = None
multiple_stdf_data = []
multiple_wafer_ids = []

# Performance optimization: Cache for computed grids
_grid_cache = {}
_current_fig = None
_current_ax = None
_die_info_window = None  # Track current die info popup window

# Canvases for statistics plots
stats_boxplot_canvas = None
stats_prob_canvas = None

# Image directory for die images
die_image_directory = None
die_image_refs = []  # Keep references to prevent garbage collection

# Image type filter
image_type_var = None  # Will be initialized later
available_image_types = ["All"]  # Will be populated when images are found
current_selected_die = None  # Store current die coordinates for refresh

# Project folder structure
project_folder = None
project_subfolders = {
    "stdf": "STDDatalog",
    "images": "ImageCaptures",
    "csv": "CSVFiles",
    "txt": "TXTDatalog",
    "plm": "PLMFiles"
}

# Control frame for STDF heatmap
control_frame_heatmap = tk.Frame(tab6)
control_frame_heatmap.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

select_multiple_stdf_button = tk.Button(
    control_frame_heatmap,
    text="Load Multiple STDF Files",
    command=lambda: load_multiple_stdf_files(),
    font=("Helvetica", 10),
)
select_multiple_stdf_button.pack(side=tk.LEFT, padx=3)

# Button to load entire project folder
load_project_button = tk.Button(
    control_frame_heatmap,
    text="Load Project Folder",
    command=lambda: load_project_folder(),
    font=("Helvetica", 10),
    bg="#FF9800",
    fg="white",
)
load_project_button.pack(side=tk.LEFT, padx=3)

heatmap_info_label = tk.Label(
    control_frame_heatmap,
    text="No STDF files loaded",
    font=("Helvetica", 9),
)
heatmap_info_label.pack(side=tk.LEFT, padx=3)

heatmap_param_label = tk.Label(
    control_frame_heatmap, text="Parameter:", font=("Helvetica", 10)
)
heatmap_param_label.pack(side=tk.LEFT, padx=5)

heatmap_param_combobox = ttk.Combobox(
    control_frame_heatmap, state="readonly", width=40, font=("Helvetica", 10)
)
heatmap_param_combobox.pack(side=tk.LEFT, padx=5)
heatmap_param_combobox.bind("<<ComboboxSelected>>", lambda e: refresh_heatmap_display())

heatmap_refresh_button = tk.Button(
    control_frame_heatmap,
    text="Refresh",
    command=lambda: refresh_heatmap_display(),
    font=("Helvetica", 12),
)
heatmap_refresh_button.pack(side=tk.LEFT, padx=5)

show_grid_checkbox = tk.Checkbutton(
    control_frame_heatmap,
    text="Show Grid",
    variable=show_grid_var,
    command=lambda: refresh_heatmap_display(),
    font=("Helvetica", 10),
)
show_grid_checkbox.pack(side=tk.LEFT, padx=5)

# Add zoom buttons as alternative to scroll wheel
zoom_in_button = tk.Button(
    control_frame_heatmap,
    text="Zoom +",
    command=lambda: zoom_heatmap(True),
    font=("Helvetica", 10),
)
zoom_in_button.pack(side=tk.LEFT, padx=2)

zoom_out_button = tk.Button(
    control_frame_heatmap,
    text="Zoom -",
    command=lambda: zoom_heatmap(False),
    font=("Helvetica", 10),
)
zoom_out_button.pack(side=tk.LEFT, padx=2)

reset_zoom_button = tk.Button(
    control_frame_heatmap,
    text="Reset Zoom",
    command=lambda: refresh_heatmap_display(),
    font=("Helvetica", 10),
)
reset_zoom_button.pack(side=tk.LEFT, padx=2)

# Colorbar limit variables (used by integrated colorbar sliders)
colorbar_low_var = tk.DoubleVar(value=0)
colorbar_high_var = tk.DoubleVar(value=100)
auto_limits_var = tk.BooleanVar(value=True)

# Store current colorbar range slider reference
_colorbar_range_slider = None
_current_imshow = None
_current_colorbar = None


def update_colorbar_sliders(data_min, data_max):
    """Update slider ranges based on data"""
    if auto_limits_var.get():
        colorbar_low_var.set(data_min)
        colorbar_high_var.set(data_max)

clear_selection_button = tk.Button(
    control_frame_heatmap,
    text="Clear Selection",
    command=lambda: clear_die_selection(),
    font=("Helvetica", 10),
)
clear_selection_button.pack(side=tk.LEFT, padx=2)

# Button to select image folder
select_image_folder_button = tk.Button(
    control_frame_heatmap,
    text="Image Folder",
    command=lambda: select_die_image_folder(),
    font=("Helvetica", 10),
    bg="#2196F3",
    fg="white",
)
select_image_folder_button.pack(side=tk.LEFT, padx=5)

image_folder_label = tk.Label(
    control_frame_heatmap,
    text="No image folder",
    font=("Helvetica", 8),
    fg="gray",
)
image_folder_label.pack(side=tk.LEFT, padx=2)

# Frame for heatmap display - now with left stats panel
heatmap_main_container = tk.Frame(tab6)
heatmap_main_container.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# Left panel for statistics (boxplot and probability distribution)
stats_panel = tk.Frame(heatmap_main_container, width=320, bg="#f0f0f0")
stats_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
stats_panel.pack_propagate(False)  # Keep fixed width

# Stats panel title
stats_title_label = tk.Label(
    stats_panel,
    text="Statistics",
    font=("Helvetica", 12, "bold"),
    bg="#f0f0f0"
)
stats_title_label.pack(side=tk.TOP, pady=5)

# Frame for boxplot
boxplot_frame = tk.Frame(stats_panel, bg="#f0f0f0")
boxplot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

boxplot_label = tk.Label(
    boxplot_frame,
    text="Boxplot",
    font=("Helvetica", 10, "bold"),
    bg="#f0f0f0"
)
boxplot_label.pack(side=tk.TOP)

# Frame for probability distribution
prob_frame = tk.Frame(stats_panel, bg="#f0f0f0")
prob_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

prob_label = tk.Label(
    prob_frame,
    text="Probability Distribution",
    font=("Helvetica", 10, "bold"),
    bg="#f0f0f0"
)
prob_label.pack(side=tk.TOP)

# Right panel for heatmap display
heatmap_display_frame = tk.Frame(heatmap_main_container)
heatmap_display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


def update_stats_plots():
    """Update boxplot and probability distribution plots based on selected parameter"""
    global stats_boxplot_canvas, stats_prob_canvas, multiple_stdf_data, current_stdf_data

    # Clear existing canvases
    for widget in boxplot_frame.winfo_children():
        if widget != boxplot_label:
            widget.destroy()
    for widget in prob_frame.winfo_children():
        if widget != prob_label:
            widget.destroy()

    # Determine data source
    if multiple_stdf_data and len(multiple_stdf_data) > 0:
        data_sources = multiple_stdf_data
        wafer_labels = multiple_wafer_ids
    elif current_stdf_data is not None and not current_stdf_data.empty:
        data_sources = [current_stdf_data]
        wafer_labels = [current_wafer_id if current_wafer_id else "Wafer"]
    else:
        return

    # Get selected parameter
    selected = heatmap_param_combobox.get()
    if not selected:
        return

    if selected.startswith("BIN"):
        param_column = "bin"
        param_label_text = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label_text = selected.split(":")[-1].strip() if ":" in selected else selected

    # Collect data from all sources
    all_data = []
    labels = []

    for df, label in zip(data_sources, wafer_labels):
        if param_column in df.columns:
            values = df[param_column].dropna().values
            if len(values) > 0:
                all_data.append(values)
                # Truncate long labels
                short_label = label[:15] + "..." if len(str(label)) > 15 else str(label)
                labels.append(short_label)

    if not all_data:
        return

    # Create boxplot
    fig_box, ax_box = plt.subplots(figsize=(2.8, 2.5))
    fig_box.patch.set_facecolor('#f0f0f0')

    bp = ax_box.boxplot(
        all_data,
        tick_labels=labels if len(labels) <= 3 else [f"W{i+1}" for i in range(len(labels))],
        vert=True,
        patch_artist=True,
        showmeans=True,
        meanprops=dict(marker="D", markerfacecolor="red", markeredgecolor="red", markersize=4),
        medianprops=dict(color="blue", linewidth=1.5),
    )

    colors = plt.cm.Set3(np.linspace(0, 1, len(all_data)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax_box.set_title(param_label_text[:20], fontsize=8, fontweight="bold")
    ax_box.tick_params(axis='both', which='major', labelsize=6)
    ax_box.set_ylabel("Value", fontsize=7)

    fig_box.tight_layout()

    stats_boxplot_canvas = FigureCanvasTkAgg(fig_box, master=boxplot_frame)
    stats_boxplot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    stats_boxplot_canvas.draw()

    # Create probability distribution plot
    fig_prob, ax_prob = plt.subplots(figsize=(2.8, 2.5))
    fig_prob.patch.set_facecolor('#f0f0f0')

    for idx, (data, label) in enumerate(zip(all_data, labels)):
        sorted_data = np.sort(data)
        prob = np.linspace(0, 1, len(sorted_data), endpoint=False)
        ax_prob.plot(sorted_data, prob, label=label, linewidth=1.5, alpha=0.8)

    ax_prob.set_title("CDF", fontsize=8, fontweight="bold")
    ax_prob.set_xlabel("Value", fontsize=7)
    ax_prob.set_ylabel("Probability", fontsize=7)
    ax_prob.tick_params(axis='both', which='major', labelsize=6)
    ax_prob.grid(True, alpha=0.3, linewidth=0.5)

    if len(labels) <= 3:
        ax_prob.legend(fontsize=5, loc='lower right')

    fig_prob.tight_layout()

    stats_prob_canvas = FigureCanvasTkAgg(fig_prob, master=prob_frame)
    stats_prob_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    stats_prob_canvas.draw()


def load_multiple_stdf_files():
    """Load multiple STDF files for multi-plot heatmap display"""
    global multiple_stdf_data, multiple_wafer_ids, test_parameters

    stdf_paths = filedialog.askopenfilenames(
        title="Select multiple STDF files",
        filetypes=[("STDF files", "*.stdf"), ("All files", "*.*")],
    )

    if not stdf_paths:
        print("No files selected.")
        return

    multiple_stdf_data = []
    multiple_wafer_ids = []

    for stdf_path in stdf_paths:
        print(f"\nLoading: {stdf_path.split('/')[-1]}")
        df, wafer_id, test_params = read_wafermap_from_stdf(stdf_path)

        if not df.empty:
            multiple_stdf_data.append(df)
            multiple_wafer_ids.append(
                wafer_id if wafer_id else stdf_path.split("/")[-1]
            )

            if not test_parameters:
                test_parameters = test_params

    if not multiple_stdf_data:
        print("No valid STDF files loaded.")
        heatmap_info_label.config(text="No valid STDF files loaded")
        return

    param_options = ["BIN (Bin Number)"]
    for test_key, test_name in sorted(test_parameters.items()):
        param_options.append(f"{test_key}: {test_name}")

    heatmap_param_combobox["values"] = param_options
    if param_options:
        heatmap_param_combobox.current(0)

    heatmap_info_label.config(text=f"Loaded {len(multiple_stdf_data)} STDF files")
    print(f"\nSuccessfully loaded {len(multiple_stdf_data)} STDF files for multi-plot")

    update_multi_stdf_heatmap()


def load_project_folder():
    """Load entire project folder with standard subfolder structure"""
    global project_folder, die_image_directory, multiple_stdf_data, multiple_wafer_ids, test_parameters

    folder_path = filedialog.askdirectory(
        title="Select Project Folder (with STDDatalog, ImageCaptures, etc.)"
    )

    if not folder_path:
        print("No folder selected.")
        return

    project_folder = folder_path
    print(f"\n{'='*60}")
    print(f"Loading project folder: {folder_path}")
    print(f"{'='*60}")

    # Check for expected subfolders
    found_folders = {}
    for key, subfolder in project_subfolders.items():
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.exists(subfolder_path):
            found_folders[key] = subfolder_path
            print(f"  Found {subfolder}: {subfolder_path}")
        else:
            print(f"  Missing {subfolder}")

    # Load STDF files from STDDatalog
    if "stdf" in found_folders:
        stdf_folder = found_folders["stdf"]
        stdf_files = [f for f in os.listdir(stdf_folder)
                      if f.lower().endswith(('.stdf', '.std'))]

        if stdf_files:
            print(f"\nFound {len(stdf_files)} STDF file(s):")
            multiple_stdf_data = []
            multiple_wafer_ids = []

            for stdf_file in stdf_files:
                stdf_path = os.path.join(stdf_folder, stdf_file)
                print(f"  Loading: {stdf_file}")

                df, wafer_id, test_params = read_wafermap_from_stdf(stdf_path)

                if not df.empty:
                    multiple_stdf_data.append(df)
                    multiple_wafer_ids.append(wafer_id if wafer_id else stdf_file)

                    if not test_parameters:
                        test_parameters = test_params

            # Update parameter combobox
            if multiple_stdf_data:
                param_options = ["BIN (Bin Number)"]
                for test_key, test_name in sorted(test_parameters.items()):
                    param_options.append(f"{test_key}: {test_name}")

                heatmap_param_combobox["values"] = param_options
                if param_options:
                    heatmap_param_combobox.current(0)

                print(f"Loaded {len(multiple_stdf_data)} STDF file(s) with {len(param_options)} parameters")
        else:
            print("  No STDF files found in STDDatalog folder")

    # Set image folder from ImageCaptures
    if "images" in found_folders:
        die_image_directory = found_folders["images"]
        short_path = "ImageCaptures"
        image_folder_label.config(text=short_path, fg="green")

        # Count images
        image_count = len([f for f in os.listdir(die_image_directory)
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff'))])
        print(f"Set image folder: {die_image_directory} ({image_count} images)")

    # Update info label
    project_name = folder_path.split("/")[-1] if "/" in folder_path else folder_path.split("\\")[-1]
    info_parts = []

    if multiple_stdf_data:
        info_parts.append(f"{len(multiple_stdf_data)} STDF")
    if die_image_directory:
        info_parts.append("Images")
    if "csv" in found_folders:
        info_parts.append("CSV")
    if "txt" in found_folders:
        info_parts.append("TXT")

    heatmap_info_label.config(text=f"Project: {project_name} ({', '.join(info_parts)})")

    # Update heatmap display
    if multiple_stdf_data:
        update_multi_stdf_heatmap()

    print(f"\n{'='*60}")
    print(f"Project loaded successfully!")
    print(f"{'='*60}\n")


def update_multi_stdf_heatmap():
    """Update multi-plot STDF heatmap display - OPTIMIZED VERSION with integrated stats"""
    global heatmap_canvas, multiple_stdf_data, multiple_wafer_ids

    if not multiple_stdf_data:
        print("No STDF data loaded for multi-plot")
        return

    selected = heatmap_param_combobox.get()

    if not selected:
        print("No parameter selected")
        return

    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label = selected

    num_files = len(multiple_stdf_data)
    cols = min(3, num_files)
    rows = (num_files + cols - 1) // cols

    fig, axes = plt.subplots(
        rows, cols, figsize=(10 * cols, 10 * rows), constrained_layout=True
    )

    if num_files == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if num_files > 1 else [axes]

    cmap = "tab20" if param_column == "bin" else "viridis"

    for idx, (df, wafer_id) in enumerate(zip(multiple_stdf_data, multiple_wafer_ids)):
        ax = axes[idx]

        if param_column not in df.columns:
            ax.set_title(f"Parameter '{param_column}' not found")
            continue

        # Use mask for faster filtering
        mask = df[param_column].notna()
        plot_data = df[mask]

        if len(plot_data) == 0:
            ax.set_title(f"No data for {wafer_id}")
            continue

        # Use vectorized grid computation
        grid, x_min, y_min, x_max, y_max, grid_width, grid_height = _compute_grid_fast(
            plot_data, param_column
        )

        im = ax.imshow(
            grid,
            cmap=cmap,
            aspect="equal",
            interpolation="nearest",
            origin="lower",
        )

        ax.set_title(f"{wafer_id}\n{param_label}", fontsize=12, fontweight="bold")
        ax.set_xlabel("X", fontsize=10)
        ax.set_ylabel("Y", fontsize=10)

        if show_grid_var.get():
            ax.set_xticks(np.arange(-0.5, grid_width, 1), minor=True)
            ax.set_yticks(np.arange(-0.5, grid_height, 1), minor=True)
            ax.grid(which="minor", color="black", linewidth=0.3)
            ax.tick_params(which="minor", size=0)

        # Add die selection highlight with brackets (only for first wafer plot for now)
        if selected_die_coords is not None and idx == 0:
            sel_x, sel_y = selected_die_coords
            x_idx = sel_x - x_min
            y_idx = sel_y - y_min

            # Check if the selected die is within this grid
            if 0 <= x_idx < grid_width and 0 <= y_idx < grid_height:
                from matplotlib.patches import Rectangle

                # Draw a prominent selection rectangle
                rect = Rectangle(
                    (x_idx - 0.5, y_idx - 0.5),
                    1,
                    1,
                    linewidth=2.0,
                    edgecolor="red",
                    facecolor="none",
                    linestyle="-",
                )
                ax.add_patch(rect)

                # Add corner brackets for better visibility
                bracket_size = 0.3
                bracket_color = "black"
                bracket_lw = 1.5

                # Top-left bracket
                ax.plot([x_idx - 0.5, x_idx - 0.5 + bracket_size], [y_idx + 0.5, y_idx + 0.5],
                        color=bracket_color, linewidth=bracket_lw)
                ax.plot([x_idx - 0.5, x_idx - 0.5], [y_idx + 0.5, y_idx + 0.5 - bracket_size],
                        color=bracket_color, linewidth=bracket_lw)

                # Top-right bracket
                ax.plot([x_idx + 0.5, x_idx + 0.5 - bracket_size], [y_idx + 0.5, y_idx + 0.5],
                        color=bracket_color, linewidth=bracket_lw)
                ax.plot([x_idx + 0.5, x_idx + 0.5], [y_idx + 0.5, y_idx + 0.5 - bracket_size],
                        color=bracket_color, linewidth=bracket_lw)

                # Bottom-left bracket
                ax.plot([x_idx - 0.5, x_idx - 0.5 + bracket_size], [y_idx - 0.5, y_idx - 0.5],
                        color=bracket_color, linewidth=bracket_lw)
                ax.plot([x_idx - 0.5, x_idx - 0.5], [y_idx - 0.5, y_idx - 0.5 + bracket_size],
                        color=bracket_color, linewidth=bracket_lw)

                # Bottom-right bracket
                ax.plot([x_idx + 0.5, x_idx + 0.5 - bracket_size], [y_idx - 0.5, y_idx - 0.5],
                        color=bracket_color, linewidth=bracket_lw)
                ax.plot([x_idx + 0.5, x_idx + 0.5], [y_idx - 0.5, y_idx - 0.5 + bracket_size],
                        color=bracket_color, linewidth=bracket_lw)

        # Create colorbar
        cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)

        # Store imshow reference for this axis
        if idx == 0:
            first_im = im
            first_cbar = cbar

    # Add interactive range slider handles directly ON the colorbar
    from matplotlib.widgets import RangeSlider

    if 'first_cbar' in dir() and first_cbar is not None:
        # Get data range from first valid dataset
        for df in multiple_stdf_data:
            if param_column in df.columns:
                mask = df[param_column].notna()
                values = df.loc[mask, param_column].values
                if len(values) > 0:
                    data_min = np.nanmin(values)
                    data_max = np.nanmax(values)

                    # Get colorbar position and create slider axes overlaid on colorbar
                    cbar_pos = first_cbar.ax.get_position()

                    # Create slider axes exactly on top of colorbar
                    slider_ax = fig.add_axes([cbar_pos.x0, cbar_pos.y0, cbar_pos.width, cbar_pos.height])
                    slider_ax.set_facecolor('none')  # Transparent background

                    # Hide slider axes frame
                    for spine in slider_ax.spines.values():
                        spine.set_visible(False)
                    slider_ax.set_xticks([])
                    slider_ax.set_yticks([])

                    # Create RangeSlider with round handles
                    range_slider = RangeSlider(
                        slider_ax,
                        "",  # No label
                        data_min,
                        data_max,
                        valinit=(data_min, data_max),
                        orientation="vertical",
                        track_color='none',  # Transparent track (colorbar shows through)
                        handle_style={'facecolor': 'white', 'edgecolor': 'black', 'size': 15}
                    )

                    # Hide the selection polygon (only show round handles)
                    range_slider.poly.set_visible(False)

                    # Get all imshow objects
                    imshow_list = []
                    for ax_item in fig.axes:
                        for child in ax_item.get_children():
                            if hasattr(child, 'set_clim'):
                                imshow_list.append(child)

                    def update_clim(val):
                        low, high = val
                        for img in imshow_list:
                            img.set_clim(vmin=low, vmax=high)
                        fig.canvas.draw_idle()

                    range_slider.on_changed(update_clim)

                    # Store reference
                    global _colorbar_range_slider
                    _colorbar_range_slider = range_slider

                    break

    for idx in range(num_files, len(axes)):
        fig.delaxes(axes[idx])

    if heatmap_canvas:
        heatmap_canvas.get_tk_widget().destroy()

    heatmap_canvas = FigureCanvasTkAgg(fig, master=heatmap_display_frame)
    heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)

    # Connect mouse events for zoom and click
    heatmap_canvas.mpl_connect("button_press_event", on_heatmap_click)
    heatmap_canvas.mpl_connect("scroll_event", on_heatmap_scroll)

    heatmap_canvas.draw()

    print(f"Multi-plot heatmap updated with {num_files} wafers")


def update_heatmap_parameter_list():
    """Update the heatmap parameter combobox when STDF data is loaded"""
    global current_stdf_data, test_parameters

    if current_stdf_data is None or current_stdf_data.empty:
        heatmap_param_combobox["values"] = []
        heatmap_info_label.config(
            text="No STDF data loaded. Load file in Wafermap tab first."
        )
        return

    param_options = ["BIN (Bin Number)"]
    for test_key, test_name in sorted(test_parameters.items()):
        param_options.append(f"{test_key}: {test_name}")

    heatmap_param_combobox["values"] = param_options
    if param_options:
        heatmap_param_combobox.current(0)

    heatmap_info_label.config(text=f"Loaded: {len(param_options)} parameters available")

    update_stdf_heatmap()


def _compute_grid_fast(plot_data, param_column):
    """
    Compute heatmap grid using vectorized numpy operations.
    This is 10-100x faster than iterrows() for large datasets.
    """
    x_vals = plot_data["x"].values
    y_vals = plot_data["y"].values
    param_vals = plot_data[param_column].values

    x_min, x_max = x_vals.min(), x_vals.max()
    y_min, y_max = y_vals.min(), y_vals.max()

    grid_width = int(x_max - x_min + 1)
    grid_height = int(y_max - y_min + 1)

    # Create grid filled with NaN
    grid = np.full((grid_height, grid_width), np.nan)

    # Vectorized index computation
    x_indices = (x_vals - x_min).astype(int)
    y_indices = (y_vals - y_min).astype(int)

    # Use advanced indexing for fast assignment
    grid[y_indices, x_indices] = param_vals

    return grid, x_min, y_min, x_max, y_max, grid_width, grid_height


def _get_cached_grid(data_id, param_column, plot_data):
    """
    Get grid from cache or compute and cache it.
    Cache key is based on data identity and parameter.
    """
    global _grid_cache

    cache_key = (data_id, param_column)

    if cache_key in _grid_cache:
        return _grid_cache[cache_key]

    # Compute grid
    result = _compute_grid_fast(plot_data, param_column)

    # Cache with size limit (keep last 10 grids)
    if len(_grid_cache) > 10:
        # Remove oldest entry
        oldest_key = next(iter(_grid_cache))
        del _grid_cache[oldest_key]

    _grid_cache[cache_key] = result
    return result


def update_stdf_heatmap():
    """Update STDF heatmap display based on selected parameter - OPTIMIZED VERSION"""
    global heatmap_canvas, current_stdf_data, current_wafer_id, _current_fig, _current_ax

    if current_stdf_data is None or current_stdf_data.empty:
        print("No STDF data loaded for heatmap")
        return

    selected = heatmap_param_combobox.get()

    if not selected:
        print("No parameter selected")
        return

    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label = selected

    if param_column not in current_stdf_data.columns:
        print(f"ERROR: Parameter '{param_column}' not found in data")
        return

    # Use mask instead of dropna for better performance
    mask = current_stdf_data[param_column].notna()
    plot_data = current_stdf_data[mask]

    if len(plot_data) == 0:
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_title(f"No valid data for parameter '{param_label}'")
        fig.tight_layout()

        if heatmap_canvas:
            heatmap_canvas.get_tk_widget().destroy()

        heatmap_canvas = FigureCanvasTkAgg(fig, master=heatmap_display_frame)
        heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
        heatmap_canvas.draw()
        return

    # Use cached grid computation (10-100x faster than iterrows)
    data_id = id(current_stdf_data)
    grid, x_min, y_min, x_max, y_max, grid_width, grid_height = _get_cached_grid(
        data_id, param_column, plot_data
    )

    # Create figure with optimized settings
    fig, ax = plt.subplots(figsize=(12, 10))

    # Use appropriate colormap
    cmap = "tab20" if param_column == "bin" else "viridis"

    # imshow is already fast, no changes needed here
    im = ax.imshow(
        grid,
        cmap=cmap,
        aspect="equal",
        interpolation="nearest",
        origin="lower",
    )

    cbar = fig.colorbar(im, ax=ax, label=param_label)
    cbar.ax.tick_params(labelsize=10)

    ax.set_xlabel("X Coordinate", fontsize=12)
    ax.set_ylabel("Y Coordinate", fontsize=12)
    ax.set_title(
        f"Heatmap: {param_label}\nWafer {current_wafer_id}",
        fontsize=14,
        fontweight="bold",
    )

    # Optimized tick computation
    num_x_ticks = min(10, grid_width)
    num_y_ticks = min(10, grid_height)
    x_tick_positions = np.linspace(0, grid_width - 1, num_x_ticks)
    y_tick_positions = np.linspace(0, grid_height - 1, num_y_ticks)

    ax.set_xticks(x_tick_positions)
    ax.set_yticks(y_tick_positions)
    ax.set_xticklabels([f"{int(x_min + pos)}" for pos in x_tick_positions])
    ax.set_yticklabels([f"{int(y_min + pos)}" for pos in y_tick_positions])

    # Grid lines - optimized: only draw if enabled
    if show_grid_var.get():
        # Use LineCollection for faster grid line rendering
        ax.set_xticks(np.arange(-0.5, grid_width, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, grid_height, 1), minor=True)
        ax.grid(which="minor", color="black", linewidth=0.5)
        ax.tick_params(which="minor", size=0)
    else:
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)

    # Selected die highlight - make it more visible
    if selected_die_coords is not None:
        sel_x, sel_y = selected_die_coords
        x_idx = sel_x - x_min
        y_idx = sel_y - y_min

        from matplotlib.patches import Rectangle

        # Draw a prominent selection rectangle
        rect = Rectangle(
            (x_idx - 0.5, y_idx - 0.5),
            1,
            1,
            linewidth=2.0,
            edgecolor="red",
            facecolor="none",
            linestyle="-",
        )
        ax.add_patch(rect)

        # Add corner brackets for better visibility
        bracket_size = 0.3
        bracket_color = "black"
        bracket_lw = 1.5

        # Top-left bracket
        ax.plot([x_idx - 0.5, x_idx - 0.5 + bracket_size], [y_idx + 0.5, y_idx + 0.5],
                color=bracket_color, linewidth=bracket_lw)
        ax.plot([x_idx - 0.5, x_idx - 0.5], [y_idx + 0.5, y_idx + 0.5 - bracket_size],
                color=bracket_color, linewidth=bracket_lw)

        # Top-right bracket
        ax.plot([x_idx + 0.5, x_idx + 0.5 - bracket_size], [y_idx + 0.5, y_idx + 0.5],
                color=bracket_color, linewidth=bracket_lw)
        ax.plot([x_idx + 0.5, x_idx + 0.5], [y_idx + 0.5, y_idx + 0.5 - bracket_size],
                color=bracket_color, linewidth=bracket_lw)

        # Bottom-left bracket
        ax.plot([x_idx - 0.5, x_idx - 0.5 + bracket_size], [y_idx - 0.5, y_idx - 0.5],
                color=bracket_color, linewidth=bracket_lw)
        ax.plot([x_idx - 0.5, x_idx - 0.5], [y_idx - 0.5, y_idx - 0.5 + bracket_size],
                color=bracket_color, linewidth=bracket_lw)

        # Bottom-right bracket
        ax.plot([x_idx + 0.5, x_idx + 0.5 - bracket_size], [y_idx - 0.5, y_idx - 0.5],
                color=bracket_color, linewidth=bracket_lw)
        ax.plot([x_idx + 0.5, x_idx + 0.5], [y_idx - 0.5, y_idx - 0.5 + bracket_size],
                color=bracket_color, linewidth=bracket_lw)

    # Pre-compute statistics using numpy for speed
    param_vals = plot_data[param_column].values
    stats_text = (
        f"Min: {np.nanmin(param_vals):.2f}\n"
        f"Max: {np.nanmax(param_vals):.2f}\n"
        f"Mean: {np.nanmean(param_vals):.2f}\n"
        f"Median: {np.nanmedian(param_vals):.2f}\n"
        f"Dies: {len(plot_data)}"
    )

    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    fig.tight_layout()

    # Destroy old canvas before creating new one
    if heatmap_canvas:
        heatmap_canvas.get_tk_widget().destroy()

    heatmap_canvas = FigureCanvasTkAgg(fig, master=heatmap_display_frame)
    canvas_widget = heatmap_canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True, pady=10)

    # Connect matplotlib events
    heatmap_canvas.mpl_connect("button_press_event", on_heatmap_click)
    heatmap_canvas.mpl_connect("scroll_event", on_heatmap_scroll)

    # Also bind tkinter native scroll events for Windows compatibility
    canvas_widget.bind("<MouseWheel>", on_tk_mousewheel)
    canvas_widget.bind("<Button-4>", lambda e: on_tk_mousewheel_linux(e, True))  # Linux scroll up
    canvas_widget.bind("<Button-5>", lambda e: on_tk_mousewheel_linux(e, False))  # Linux scroll down

    heatmap_canvas.draw()


def refresh_heatmap_display():
    """Refresh heatmap display - calls appropriate function based on loaded data"""
    global selected_die_coords
    if multiple_stdf_data:
        update_multi_stdf_heatmap()
    elif current_stdf_data is not None and not current_stdf_data.empty:
        update_stdf_heatmap()
    else:
        print("No STDF data loaded")

    # Update statistics plots (boxplot and probability distribution)
    update_stats_plots()


def zoom_heatmap(zoom_in):
    """Zoom in or out on the heatmap using buttons"""
    global heatmap_canvas

    if heatmap_canvas is None:
        print("No heatmap canvas available")
        return

    # Get the figure and axes from the canvas
    fig = heatmap_canvas.figure
    if not fig.axes:
        print("No axes found in figure")
        return

    ax = fig.axes[0]

    # Get current axis limits
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()

    # Zoom factor
    zoom_factor = 0.8 if zoom_in else 1.25

    # Calculate center of current view
    x_center = (cur_xlim[0] + cur_xlim[1]) / 2
    y_center = (cur_ylim[0] + cur_ylim[1]) / 2

    # Calculate current ranges
    x_range = cur_xlim[1] - cur_xlim[0]
    y_range = cur_ylim[1] - cur_ylim[0]

    # New ranges after zoom
    new_x_range = x_range * zoom_factor
    new_y_range = y_range * zoom_factor

    # New limits centered on current view center
    new_xlim = [x_center - new_x_range / 2, x_center + new_x_range / 2]
    new_ylim = [y_center - new_y_range / 2, y_center + new_y_range / 2]

    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)

    # Force redraw
    heatmap_canvas.draw()
    heatmap_canvas.flush_events()

    print(f"Zoom {'in' if zoom_in else 'out'}: xlim {cur_xlim} -> {new_xlim}")


def clear_die_selection():
    """Clear the selected die and refresh the heatmap"""
    global selected_die_coords
    selected_die_coords = None
    print("Die selection cleared")
    refresh_heatmap_display()


def on_heatmap_click(event):
    """Handle left-click on heatmap to display die value"""
    global current_stdf_data, selected_die_coords, heatmap_canvas, multiple_stdf_data, _die_info_window

    print(f"Click event: button={event.button}, inaxes={event.inaxes is not None}, dblclick={event.dblclick}")

    # Accept single click (button 1)
    if event.button != 1:
        return

    if event.inaxes is None:
        print("Click outside axes")
        return

    # Use multiple_stdf_data if available, otherwise use current_stdf_data
    if multiple_stdf_data and len(multiple_stdf_data) > 0:
        data_source = multiple_stdf_data[0]  # Use first file for now
    elif current_stdf_data is not None and not current_stdf_data.empty:
        data_source = current_stdf_data
    else:
        print("No STDF data available")
        return

    selected = heatmap_param_combobox.get()

    if not selected:
        print("No parameter selected")
        return

    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label = selected

    x_click = event.xdata
    y_click = event.ydata

    print(f"Click at grid position: ({x_click}, {y_click})")

    if x_click is None or y_click is None:
        return

    if param_column not in data_source.columns:
        print(f"Parameter {param_column} not in data")
        return

    mask = data_source[param_column].notna()
    plot_data = data_source[mask]

    if len(plot_data) == 0:
        return

    x_min = plot_data["x"].min()
    y_min = plot_data["y"].min()

    actual_x = int(round(x_click + x_min))
    actual_y = int(round(y_click + y_min))

    print(f"Actual die coordinates: ({actual_x}, {actual_y})")

    die_data = plot_data[(plot_data["x"] == actual_x) & (plot_data["y"] == actual_y)]

    if len(die_data) > 0:
        die_row = die_data.iloc[0]
        value = die_row[param_column]

        print(f"Found die with value: {value}")

        # Set selected coordinates
        selected_die_coords = (actual_x, actual_y)
        print(f"Set selected_die_coords to: {selected_die_coords}")

        # Close previous die info window if it exists
        if _die_info_window is not None:
            try:
                _die_info_window.destroy()
            except:
                pass  # Window may already be destroyed

        # Show info popup FIRST (before redraw which may take time)
        info_win = tk.Toplevel(main_win)
        info_win.title(f"Die Information - ({actual_x}, {actual_y})")
        info_win.geometry("400x300")

        # Store reference to current window
        _die_info_window = info_win

        text_frame = tk.Frame(info_win)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Courier", 10)
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_widget.yview)

        info_text = f"Die Coordinates: ({actual_x}, {actual_y})\n"
        info_text += f"{'='*40}\n\n"

        text_widget.insert("end", info_text)

        try:
            text_widget.insert("end", f"{param_label}: {value:.4f}\n\n", "selected")
        except (TypeError, ValueError):
            text_widget.insert("end", f"{param_label}: {value}\n\n", "selected")

        text_widget.insert("end", f"Additional Information:\n")
        text_widget.insert("end", f"{'-'*40}\n")

        if "bin" in die_row:
            if param_column == "bin":
                text_widget.insert("end", f"Bin: {die_row['bin']}\n", "selected")
            else:
                text_widget.insert("end", f"Bin: {die_row['bin']}\n")

        for col in die_row.index:
            if isinstance(col, int) and col != param_column:
                test_name = test_parameters.get(f"test_{col}", f"Test {col}")
                try:
                    text_widget.insert("end", f"{test_name}: {die_row[col]:.4f}\n")
                except (TypeError, ValueError):
                    text_widget.insert("end", f"{test_name}: {die_row[col]}\n")

        text_widget.tag_config(
            "selected", foreground="red", font=("Courier", 10, "bold")
        )

        text_widget.config(state=tk.DISABLED)

        # Clear reference when window is closed
        def on_info_close():
            global _die_info_window
            _die_info_window = None
            info_win.destroy()

        info_win.protocol("WM_DELETE_WINDOW", on_info_close)

        print(f"Clicked die at ({actual_x}, {actual_y}): {param_label} = {value}")

        # Display images for the selected die
        display_die_images(actual_x, actual_y)

        # Display PLM files for the selected die
        display_plm_files(actual_x, actual_y)

        # Now redraw with selection highlight
        refresh_heatmap_display()

    else:
        print(f"No die found at position ({actual_x}, {actual_y})")


def on_heatmap_scroll(event):
    """Handle mouse wheel scroll to zoom in/out on heatmap"""
    global heatmap_canvas

    print(f"Scroll event: step={getattr(event, 'step', 'N/A')}, button={getattr(event, 'button', 'N/A')}")

    if event.inaxes is None:
        print("Scroll outside axes")
        return

    ax = event.inaxes

    # Get current axis limits
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()

    x_data = event.xdata
    y_data = event.ydata

    if x_data is None or y_data is None:
        print("No valid scroll position")
        return

    # Determine zoom direction
    # On Windows TkAgg: event.step > 0 means scroll up (zoom in)
    # event.button can be 'up' or 'down'
    zoom_in = False

    if hasattr(event, 'step') and event.step is not None:
        zoom_in = event.step > 0
        print(f"Using step: {event.step}, zoom_in={zoom_in}")
    elif hasattr(event, 'button') and event.button in ['up', 'down']:
        zoom_in = (event.button == 'up')
        print(f"Using button: {event.button}, zoom_in={zoom_in}")
    else:
        print("Could not determine scroll direction")
        return

    # Zoom factor: 0.8 = zoom in (smaller view), 1.25 = zoom out (larger view)
    zoom_factor = 0.8 if zoom_in else 1.25

    # Calculate current ranges
    x_range = cur_xlim[1] - cur_xlim[0]
    y_range = cur_ylim[1] - cur_ylim[0]

    # New ranges after zoom
    new_x_range = x_range * zoom_factor
    new_y_range = y_range * zoom_factor

    # Calculate relative position of mouse in current view (0 to 1)
    rel_x = (x_data - cur_xlim[0]) / x_range
    rel_y = (y_data - cur_ylim[0]) / y_range

    # New limits keeping mouse position fixed
    new_xlim = [x_data - rel_x * new_x_range, x_data + (1 - rel_x) * new_x_range]
    new_ylim = [y_data - rel_y * new_y_range, y_data + (1 - rel_y) * new_y_range]

    print(f"Zoom {'in' if zoom_in else 'out'}: xlim {cur_xlim} -> {new_xlim}")

    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)

    # Force redraw
    if heatmap_canvas:
        heatmap_canvas.draw()
        heatmap_canvas.flush_events()


def on_tk_mousewheel(event):
    """Handle Windows native mouse wheel events for zoom"""
    global heatmap_canvas

    print(f"TK MouseWheel event: delta={event.delta}")

    if heatmap_canvas is None:
        return

    fig = heatmap_canvas.figure
    if not fig.axes:
        return

    ax = fig.axes[0]

    # Get current axis limits
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()

    # On Windows, event.delta is positive for scroll up, negative for scroll down
    zoom_in = event.delta > 0
    zoom_factor = 0.8 if zoom_in else 1.25

    # Calculate center of current view
    x_center = (cur_xlim[0] + cur_xlim[1]) / 2
    y_center = (cur_ylim[0] + cur_ylim[1]) / 2

    # Calculate current ranges
    x_range = cur_xlim[1] - cur_xlim[0]
    y_range = cur_ylim[1] - cur_ylim[0]

    # New ranges after zoom
    new_x_range = x_range * zoom_factor
    new_y_range = y_range * zoom_factor

    # New limits centered on current view center
    new_xlim = [x_center - new_x_range / 2, x_center + new_x_range / 2]
    new_ylim = [y_center - new_y_range / 2, y_center + new_y_range / 2]

    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)

    # Force redraw
    heatmap_canvas.draw()
    heatmap_canvas.flush_events()

    print(f"TK Zoom {'in' if zoom_in else 'out'}: xlim {cur_xlim} -> {new_xlim}")


def on_tk_mousewheel_linux(event, zoom_in):
    """Handle Linux native mouse wheel events for zoom"""
    global heatmap_canvas

    print(f"TK Linux MouseWheel event: zoom_in={zoom_in}")

    if heatmap_canvas is None:
        return

    fig = heatmap_canvas.figure
    if not fig.axes:
        return

    ax = fig.axes[0]

    # Get current axis limits
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()

    zoom_factor = 0.8 if zoom_in else 1.25

    # Calculate center of current view
    x_center = (cur_xlim[0] + cur_xlim[1]) / 2
    y_center = (cur_ylim[0] + cur_ylim[1]) / 2

    # Calculate current ranges
    x_range = cur_xlim[1] - cur_xlim[0]
    y_range = cur_ylim[1] - cur_ylim[0]

    # New ranges after zoom
    new_x_range = x_range * zoom_factor
    new_y_range = y_range * zoom_factor

    # New limits centered on current view center
    new_xlim = [x_center - new_x_range / 2, x_center + new_x_range / 2]
    new_ylim = [y_center - new_y_range / 2, y_center + new_y_range / 2]

    ax.set_xlim(new_xlim)
    ax.set_ylim(new_ylim)

    # Force redraw
    heatmap_canvas.draw()
    heatmap_canvas.flush_events()

    print(f"TK Linux Zoom {'in' if zoom_in else 'out'}: xlim {cur_xlim} -> {new_xlim}")


def select_die_image_folder():
    """Select the folder containing die images"""
    global die_image_directory

    folder_path = filedialog.askdirectory(
        title="Select Image Folder for Die Images"
    )

    if folder_path:
        die_image_directory = folder_path
        # Show short version of path
        short_path = folder_path.split("/")[-1] if "/" in folder_path else folder_path.split("\\")[-1]
        image_folder_label.config(text=short_path, fg="green")
        print(f"Die image folder set to: {folder_path}")


def find_die_images(x_coord, y_coord, image_type_filter=None):
    """Find images matching the given die coordinates and optional type filter"""
    global die_image_directory, available_image_types

    if not die_image_directory:
        return []

    matching_images = []
    found_types = set(["All"])  # Always include "All" option

    try:
        import re

        # List all files in the directory
        for filename in os.listdir(die_image_directory):
            # Check for image file extensions
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff')):
                continue

            # Look for coordinate patterns in filename
            # Patterns: X19_Y46, X19-Y46, _X19_Y46_, Die_X19_Y46
            # Pattern 1: X##_Y## or X##-Y##
            pattern1 = rf'[_\-]X{x_coord}[_\-]Y{y_coord}[_\-\.]'
            # Pattern 2: _X##_Y##_ (with underscores)
            pattern2 = rf'_X{x_coord}_Y{y_coord}_'
            # Pattern 3: -X##-Y##- (with dashes)
            pattern3 = rf'-X{x_coord}-Y{y_coord}-'

            if (re.search(pattern1, filename, re.IGNORECASE) or
                re.search(pattern2, filename, re.IGNORECASE) or
                re.search(pattern3, filename, re.IGNORECASE)):

                # Extract image type from filename
                # Pattern: VPG-XHAIR-12FRAME or VPG-ALLON-12FRAME
                type_match = re.search(r'VPG-([A-Z0-9]+)-', filename, re.IGNORECASE)
                if type_match:
                    img_type = type_match.group(1).upper()
                    found_types.add(img_type)

                    # Apply filter if specified
                    if image_type_filter and image_type_filter != "All":
                        if img_type != image_type_filter.upper():
                            continue

                full_path = os.path.join(die_image_directory, filename)
                matching_images.append(full_path)
                print(f"Found matching image: {filename}")

        # Update available types in combobox
        available_image_types = sorted(list(found_types))
        if "All" in available_image_types:
            available_image_types.remove("All")
            available_image_types.insert(0, "All")

        # Update combobox values
        current_selection = image_type_var.get()
        image_type_combobox["values"] = available_image_types
        if current_selection not in available_image_types:
            image_type_var.set("All")

    except Exception as e:
        print(f"Error searching for die images: {e}")

    return matching_images


def refresh_die_images():
    """Refresh die images based on current filter selection"""
    global current_selected_die

    if current_selected_die is not None:
        x_coord, y_coord = current_selected_die
        display_die_images(x_coord, y_coord)


# Right panel for die images and PLM files - NOW ON LEFT SIDE next to stats
die_image_panel = tk.Frame(heatmap_main_container, width=320, bg="#e8e8e8")
die_image_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
die_image_panel.pack_propagate(False)

# Die image panel title
die_image_title = tk.Label(
    die_image_panel,
    text="Die Images",
    font=("Helvetica", 10, "bold"),
    bg="#e8e8e8"
)
die_image_title.pack(side=tk.TOP, pady=3)

# Image type filter frame
image_filter_frame = tk.Frame(die_image_panel, bg="#e8e8e8")
image_filter_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)

image_type_label = tk.Label(
    image_filter_frame,
    text="Type:",
    font=("Helvetica", 8),
    bg="#e8e8e8"
)
image_type_label.pack(side=tk.LEFT, padx=2)

image_type_var = tk.StringVar(value="All")
image_type_combobox = ttk.Combobox(
    image_filter_frame,
    textvariable=image_type_var,
    values=["All"],
    state="readonly",
    width=12,
    font=("Helvetica", 8)
)
image_type_combobox.pack(side=tk.LEFT, padx=2)
image_type_combobox.bind("<<ComboboxSelected>>", lambda e: refresh_die_images())

# Frame for die images (same height as boxplot frame - using expand proportionally)
die_image_container = tk.Frame(die_image_panel, bg="#e8e8e8")
die_image_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=3)

# Scrollable frame for die images inside container
die_image_canvas = tk.Canvas(die_image_container, bg="#e8e8e8")
die_image_scrollbar = tk.Scrollbar(die_image_container, orient="vertical", command=die_image_canvas.yview)
die_image_scrollable_frame = tk.Frame(die_image_canvas, bg="#e8e8e8")

die_image_scrollable_frame.bind(
    "<Configure>",
    lambda e: die_image_canvas.configure(scrollregion=die_image_canvas.bbox("all"))
)

die_image_canvas.create_window((0, 0), window=die_image_scrollable_frame, anchor="nw")
die_image_canvas.configure(yscrollcommand=die_image_scrollbar.set)

die_image_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
die_image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Separator between images and PLM
plm_separator = ttk.Separator(die_image_panel, orient='horizontal')
plm_separator.pack(fill=tk.X, padx=5, pady=5)

# PLM Files section
plm_title = tk.Label(
    die_image_panel,
    text="PLM Files",
    font=("Helvetica", 10, "bold"),
    bg="#e8e8e8"
)
plm_title.pack(side=tk.TOP, pady=3)

# PLM file filter frame
plm_filter_frame = tk.Frame(die_image_panel, bg="#e8e8e8")
plm_filter_frame.pack(side=tk.TOP, fill=tk.X, padx=3, pady=3)

plm_type_label = tk.Label(
    plm_filter_frame,
    text="Type:",
    font=("Helvetica", 8),
    bg="#e8e8e8"
)
plm_type_label.pack(side=tk.LEFT, padx=2)

plm_type_var = tk.StringVar(value="All")
plm_type_combobox = ttk.Combobox(
    plm_filter_frame,
    textvariable=plm_type_var,
    values=["All"],
    state="readonly",
    width=12,
    font=("Helvetica", 8)
)
plm_type_combobox.pack(side=tk.LEFT, padx=2)
plm_type_combobox.bind("<<ComboboxSelected>>", lambda e: refresh_plm_files())

# Frame for PLM heatmaps (same height as CDF frame)
plm_container = tk.Frame(die_image_panel, bg="#e8e8e8")
plm_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=3)

# Scrollable frame for PLM files inside container
plm_canvas = tk.Canvas(plm_container, bg="#e8e8e8")
plm_scrollbar = tk.Scrollbar(plm_container, orient="vertical", command=plm_canvas.yview)
plm_scrollable_frame = tk.Frame(plm_canvas, bg="#e8e8e8")

plm_scrollable_frame.bind(
    "<Configure>",
    lambda e: plm_canvas.configure(scrollregion=plm_canvas.bbox("all"))
)

plm_canvas.create_window((0, 0), window=plm_scrollable_frame, anchor="nw")
plm_canvas.configure(yscrollcommand=plm_scrollbar.set)

plm_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
plm_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# PLM file references
plm_file_refs = []
available_plm_types = ["All"]
current_selected_die_plm = None


def find_plm_files(x_coord, y_coord, plm_type_filter=None):
    """Find PLM files matching the given die coordinates and optional type filter"""
    global available_plm_types

    plm_dir = config_dirs["plm"].get() if "plm" in config_dirs else None

    if not plm_dir or not os.path.exists(plm_dir):
        return []

    matching_files = []
    found_types = set(["All"])

    try:
        import re

        for filename in os.listdir(plm_dir):
            # Check for PLM file extensions (common ones)
            if not filename.lower().endswith(('.plm', '.txt', '.csv', '.dat', '.xml', '.json')):
                continue

            # Look for coordinate patterns in filename
            pattern1 = rf'[_\-]X{x_coord}[_\-]Y{y_coord}[_\-\.]'
            pattern2 = rf'_X{x_coord}_Y{y_coord}_'
            pattern3 = rf'-X{x_coord}-Y{y_coord}-'

            if (re.search(pattern1, filename, re.IGNORECASE) or
                re.search(pattern2, filename, re.IGNORECASE) or
                re.search(pattern3, filename, re.IGNORECASE)):

                # Extract PLM type from filename if present
                type_match = re.search(r'PLM-([A-Z0-9]+)-', filename, re.IGNORECASE)
                if type_match:
                    plm_type = type_match.group(1).upper()
                    found_types.add(plm_type)

                    if plm_type_filter and plm_type_filter != "All":
                        if plm_type != plm_type_filter.upper():
                            continue
                else:
                    # Try to extract type from file extension or other patterns
                    ext = os.path.splitext(filename)[1].upper().replace('.', '')
                    found_types.add(ext)

                    if plm_type_filter and plm_type_filter != "All":
                        if ext != plm_type_filter.upper():
                            continue

                full_path = os.path.join(plm_dir, filename)
                matching_files.append(full_path)
                print(f"Found matching PLM file: {filename}")

        # Update available types
        available_plm_types = sorted(list(found_types))
        if "All" in available_plm_types:
            available_plm_types.remove("All")
            available_plm_types.insert(0, "All")

        current_selection = plm_type_var.get()
        plm_type_combobox["values"] = available_plm_types
        if current_selection not in available_plm_types:
            plm_type_var.set("All")

    except Exception as e:
        print(f"Error searching for PLM files: {e}")

    return matching_files


def refresh_plm_files():
    """Refresh PLM files based on current filter selection"""
    global current_selected_die_plm

    if current_selected_die_plm is not None:
        x_coord, y_coord = current_selected_die_plm
        display_plm_files(x_coord, y_coord)


def display_plm_files(x_coord, y_coord):
    """Display PLM files for the selected die coordinates as heatmaps like Plot tab"""
    global plm_file_refs, current_selected_die_plm

    current_selected_die_plm = (x_coord, y_coord)

    # Clear existing content
    for widget in plm_scrollable_frame.winfo_children():
        widget.destroy()
    plm_file_refs.clear()

    # Get current filter
    current_filter = plm_type_var.get()

    # Find matching PLM files
    matching_files = find_plm_files(x_coord, y_coord, current_filter)

    if not matching_files:
        filter_text = f" (filter: {current_filter})" if current_filter != "All" else ""
        no_plm_label = tk.Label(
            plm_scrollable_frame,
            text=f"No PLM files\nfor die ({x_coord}, {y_coord}){filter_text}",
            font=("Helvetica", 9),
            bg="#e8e8e8",
            fg="gray"
        )
        no_plm_label.pack(pady=10)
        return

    # Display file count
    count_text = f"{len(matching_files)} PLM file(s)"
    if current_filter != "All":
        count_text += f" [{current_filter}]"
    count_label = tk.Label(
        plm_scrollable_frame,
        text=count_text,
        font=("Helvetica", 8),
        bg="#e8e8e8",
        fg="gray"
    )
    count_label.pack(pady=2)

    # Display each PLM file as a heatmap (like Plot tab)
    for plm_path in matching_files:
        try:
            file_frame = tk.Frame(plm_scrollable_frame, bg="#e8e8e8")
            file_frame.pack(pady=3, padx=3, fill=tk.X)

            # Try to load PLM file as measurement data
            plm_data = load_plm_as_matrix(plm_path)

            if plm_data is not None and plm_data.size > 0:
                # Create small heatmap figure
                fig_plm, ax_plm = plt.subplots(figsize=(2.6, 2.0))
                fig_plm.patch.set_facecolor('#e8e8e8')

                im = ax_plm.imshow(plm_data, cmap='viridis', aspect='auto')

                # Extract filename for title
                filename = os.path.basename(plm_path)
                short_name = filename[:20] + "..." if len(filename) > 20 else filename
                ax_plm.set_title(short_name, fontsize=7, fontweight="bold")
                ax_plm.tick_params(axis='both', which='major', labelsize=5)

                # Add small colorbar
                cbar = fig_plm.colorbar(im, ax=ax_plm, fraction=0.046, pad=0.04)
                cbar.ax.tick_params(labelsize=5)

                fig_plm.tight_layout()

                # Embed in tkinter
                plm_canvas = FigureCanvasTkAgg(fig_plm, master=file_frame)
                plm_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                plm_canvas.draw()

                # Keep reference to prevent garbage collection
                plm_file_refs.append(plm_canvas)

                # Make clickable to open zoomed view
                plm_canvas.get_tk_widget().bind("<Button-1>",
                    lambda e, path=plm_path, data=plm_data: show_zoomed_plm(path, data))
            else:
                # Fallback: show as text file link if can't parse as matrix
                ext = os.path.splitext(plm_path)[1].upper().replace('.', '')
                type_label = tk.Label(
                    file_frame,
                    text=f"[{ext}]",
                    font=("Helvetica", 8, "bold"),
                    bg="#e8e8e8",
                    fg="#9C27B0"
                )
                type_label.pack(side=tk.LEFT, padx=2)

                filename = os.path.basename(plm_path)
                if len(filename) > 25:
                    filename = filename[:22] + "..."

                file_label = tk.Label(
                    file_frame,
                    text=filename,
                    font=("Helvetica", 8),
                    bg="#e8e8e8",
                    fg="blue",
                    cursor="hand2"
                )
                file_label.pack(side=tk.LEFT, padx=2)
                file_label.bind("<Button-1>", lambda e, path=plm_path: open_plm_file(path))

        except Exception as e:
            print(f"Error displaying PLM file {plm_path}: {e}")

    print(f"Displayed {len(matching_files)} PLM files for die ({x_coord}, {y_coord})")


def load_plm_as_matrix(file_path):
    """Load PLM file as a numpy matrix for heatmap display"""
    try:
        # Try different parsing methods based on file extension
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ('.csv',):
            # CSV file - try to load as numeric data
            try:
                data = np.genfromtxt(file_path, delimiter=',', skip_header=0)
                if np.isnan(data).all():
                    data = np.genfromtxt(file_path, delimiter=',', skip_header=1)
                return data
            except:
                pass

        elif ext in ('.txt', '.dat'):
            # Text file - try common formats
            try:
                # Try comma-separated first
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                # Find where numeric data starts
                data_start = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped and (stripped[0].isdigit() or stripped[0] == '-'):
                        data_start = i
                        break

                raw_data = lines[data_start:]

                # Try comma-separated
                if ',' in raw_data[0]:
                    matrix = [list(map(float, row.strip().split(',')))
                              for row in raw_data if row.strip()]
                # Try tab-separated
                elif '\t' in raw_data[0]:
                    matrix = [list(map(float, row.strip().split('\t')))
                              for row in raw_data if row.strip()]
                # Try space-separated
                else:
                    matrix = [list(map(float, row.strip().split()))
                              for row in raw_data if row.strip()]

                return np.array(matrix)
            except:
                pass

        return None
    except Exception as e:
        print(f"Error loading PLM file as matrix: {e}")
        return None


def show_zoomed_plm(file_path, plm_data):
    """Show zoomed view of PLM heatmap"""
    zoom_win = tk.Toplevel(main_win)
    filename = os.path.basename(file_path)
    zoom_win.title(f"PLM Heatmap: {filename}")
    zoom_win.geometry("800x600")

    # Create larger heatmap
    fig_zoom, ax_zoom = plt.subplots(figsize=(10, 8))

    im = ax_zoom.imshow(plm_data, cmap='viridis', aspect='auto')
    ax_zoom.set_title(f"PLM: {filename}", fontsize=12, fontweight="bold")
    ax_zoom.set_xlabel("Column Index", fontsize=10)
    ax_zoom.set_ylabel("Row Index", fontsize=10)

    cbar = fig_zoom.colorbar(im, ax=ax_zoom)
    cbar.ax.tick_params(labelsize=9)

    # Add statistics
    stats_text = (
        f"Min: {np.nanmin(plm_data):.4f}\n"
        f"Max: {np.nanmax(plm_data):.4f}\n"
        f"Mean: {np.nanmean(plm_data):.4f}\n"
        f"Shape: {plm_data.shape}"
    )
    ax_zoom.text(
        0.02, 0.98, stats_text,
        transform=ax_zoom.transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    )

    fig_zoom.tight_layout()

    # Embed in window
    canvas_zoom = FigureCanvasTkAgg(fig_zoom, master=zoom_win)
    canvas_zoom.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Add toolbar
    toolbar = NavigationToolbar2Tk(canvas_zoom, zoom_win)
    toolbar.update()

    canvas_zoom.draw()

    # Button to open as text
    btn_frame = tk.Frame(zoom_win)
    btn_frame.pack(side=tk.BOTTOM, pady=5)

    tk.Button(
        btn_frame,
        text="View Raw Text",
        command=lambda: open_plm_file(file_path),
        font=("Helvetica", 10)
    ).pack(side=tk.LEFT, padx=5)

    def on_close():
        plt.close(fig_zoom)
        zoom_win.destroy()

    zoom_win.protocol("WM_DELETE_WINDOW", on_close)


def open_plm_file(file_path):
    """Open and display PLM file contents"""
    plm_win = tk.Toplevel(main_win)
    filename = os.path.basename(file_path)
    plm_win.title(f"PLM File: {filename}")
    plm_win.geometry("700x500")

    # Text widget with scrollbars
    text_frame = tk.Frame(plm_win)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
    h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)

    text_widget = tk.Text(
        text_frame,
        wrap=tk.NONE,
        xscrollcommand=h_scrollbar.set,
        yscrollcommand=v_scrollbar.set,
        font=("Courier", 9)
    )

    v_scrollbar.config(command=text_widget.yview)
    h_scrollbar.config(command=text_widget.xview)

    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        text_widget.insert("1.0", content)
    except Exception as e:
        text_widget.insert("1.0", f"Error reading file: {e}")

    text_widget.config(state=tk.DISABLED)

    # Info bar
    info_bar = tk.Label(
        plm_win,
        text=f"File: {file_path}",
        font=("Helvetica", 8),
        fg="gray",
        anchor="w"
    )
    info_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)


def display_die_images(x_coord, y_coord):
    """Display images for the selected die coordinates"""
    global die_image_refs, current_selected_die

    # Store current die coordinates for filter refresh
    current_selected_die = (x_coord, y_coord)

    # Clear existing images
    for widget in die_image_scrollable_frame.winfo_children():
        widget.destroy()
    die_image_refs.clear()

    # Get current filter selection
    current_filter = image_type_var.get()

    # Find matching images with filter
    matching_images = find_die_images(x_coord, y_coord, current_filter)

    if not matching_images:
        filter_text = f" (filter: {current_filter})" if current_filter != "All" else ""
        no_image_label = tk.Label(
            die_image_scrollable_frame,
            text=f"No images found\nfor die ({x_coord}, {y_coord}){filter_text}",
            font=("Helvetica", 10),
            bg="#e8e8e8",
            fg="gray"
        )
        no_image_label.pack(pady=20)
        return

    # Display coordinate label
    coord_label = tk.Label(
        die_image_scrollable_frame,
        text=f"Die ({x_coord}, {y_coord})",
        font=("Helvetica", 11, "bold"),
        bg="#e8e8e8"
    )
    coord_label.pack(pady=5)

    # Display image count
    count_text = f"{len(matching_images)} image(s)"
    if current_filter != "All":
        count_text += f" [{current_filter}]"
    count_label = tk.Label(
        die_image_scrollable_frame,
        text=count_text,
        font=("Helvetica", 9),
        bg="#e8e8e8",
        fg="gray"
    )
    count_label.pack(pady=2)

    # Display each image
    for img_path in matching_images:
        try:
            # Create frame for image and label
            img_frame = tk.Frame(die_image_scrollable_frame, bg="#e8e8e8")
            img_frame.pack(pady=5, padx=5, fill=tk.X)

            # Extract image type for label
            import re
            type_match = re.search(r'VPG-([A-Z0-9]+)-', os.path.basename(img_path), re.IGNORECASE)
            img_type = type_match.group(1).upper() if type_match else "Unknown"

            # Type label
            type_label = tk.Label(
                img_frame,
                text=f"[{img_type}]",
                font=("Helvetica", 9, "bold"),
                bg="#e8e8e8",
                fg="#2196F3"
            )
            type_label.pack()

            # Load and resize image - handle TIF files specially
            img = Image.open(img_path)

            # Convert TIF/TIFF to RGB if needed (handles various color modes)
            if img.mode in ('I;16', 'I;16B', 'I;16L', 'I;16N', 'I', 'F'):
                # 16-bit or float images - normalize to 8-bit
                img_array = np.array(img, dtype=np.float32)
                img_array = (img_array - img_array.min()) / (img_array.max() - img_array.min() + 1e-10) * 255
                img = Image.fromarray(img_array.astype(np.uint8))

            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Calculate thumbnail size maintaining aspect ratio
            max_width = 280
            max_height = 180
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            tk_img = ImageTk.PhotoImage(img, master=main_win)
            die_image_refs.append(tk_img)

            # Image label (clickable)
            img_label = tk.Label(img_frame, image=tk_img, bg="#e8e8e8", cursor="hand2")
            img_label.pack()
            img_label.bind("<Button-1>", lambda e, path=img_path: show_zoomed_image(path))

            # Filename label (truncated if too long)
            filename = os.path.basename(img_path)
            if len(filename) > 40:
                filename = filename[:37] + "..."
            name_label = tk.Label(
                img_frame,
                text=filename,
                font=("Helvetica", 8),
                bg="#e8e8e8",
                fg="gray"
            )
            name_label.pack()

        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            error_label = tk.Label(
                die_image_scrollable_frame,
                text=f"Error loading: {os.path.basename(img_path)}",
                font=("Helvetica", 8),
                bg="#e8e8e8",
                fg="red"
            )
            error_label.pack()

    print(f"Displayed {len(matching_images)} images for die ({x_coord}, {y_coord})")


# Configuration tab layout (already created above as tab7)

# Configuration variables
config_dirs = {
    "stdf": tk.StringVar(value=""),
    "images": tk.StringVar(value=""),
    "csv": tk.StringVar(value=""),
    "txt": tk.StringVar(value=""),
    "plm": tk.StringVar(value="")
}

# Configuration file path
import json
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".wafermap_config.json")


def load_config():
    """Load configuration from file"""
    global config_dirs
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)

            for key, value in saved_config.items():
                if key in config_dirs:
                    config_dirs[key].set(value)

            print(f"Configuration loaded from {CONFIG_FILE}")
            update_config_status()
    except Exception as e:
        print(f"Error loading configuration: {e}")


def save_config():
    """Save configuration to file"""
    global config_dirs
    try:
        config_data = {key: var.get() for key, var in config_dirs.items()}

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)

        print(f"Configuration saved to {CONFIG_FILE}")
        config_status_label.config(text="Configuration saved!", fg="green")
    except Exception as e:
        print(f"Error saving configuration: {e}")
        config_status_label.config(text=f"Error: {e}", fg="red")


def browse_directory(dir_type):
    """Browse for a directory and update the corresponding config"""
    folder_path = filedialog.askdirectory(
        title=f"Select {dir_type.upper()} Directory"
    )

    if folder_path:
        config_dirs[dir_type].set(folder_path)
        update_config_status()
        print(f"Set {dir_type} directory to: {folder_path}")


def update_config_status():
    """Update the status of configured directories"""
    configured = sum(1 for var in config_dirs.values() if var.get())
    config_status_label.config(
        text=f"{configured}/5 directories configured",
        fg="green" if configured == 5 else "orange" if configured > 0 else "gray"
    )


def apply_config_and_load():
    """Apply configuration and load data from configured directories"""
    global die_image_directory, multiple_stdf_data, multiple_wafer_ids, test_parameters

    print(f"\n{'='*60}")
    print("Applying configuration and loading data...")
    print(f"{'='*60}")

    # Set image directory
    images_dir = config_dirs["images"].get()
    if images_dir and os.path.exists(images_dir):
        die_image_directory = images_dir
        image_folder_label.config(text=os.path.basename(images_dir), fg="green")
        print(f"Set image directory: {images_dir}")

    # Load STDF files
    stdf_dir = config_dirs["stdf"].get()
    if stdf_dir and os.path.exists(stdf_dir):
        stdf_files = [f for f in os.listdir(stdf_dir)
                      if f.lower().endswith(('.stdf', '.std'))]

        if stdf_files:
            print(f"Found {len(stdf_files)} STDF file(s)")
            multiple_stdf_data = []
            multiple_wafer_ids = []

            for stdf_file in stdf_files:
                stdf_path = os.path.join(stdf_dir, stdf_file)
                print(f"  Loading: {stdf_file}")

                df, wafer_id, test_params = read_wafermap_from_stdf(stdf_path)

                if not df.empty:
                    multiple_stdf_data.append(df)
                    multiple_wafer_ids.append(wafer_id if wafer_id else stdf_file)

                    if not test_parameters:
                        test_parameters = test_params

            # Update parameter combobox
            if multiple_stdf_data:
                param_options = ["BIN (Bin Number)"]
                for test_key, test_name in sorted(test_parameters.items()):
                    param_options.append(f"{test_key}: {test_name}")

                heatmap_param_combobox["values"] = param_options
                if param_options:
                    heatmap_param_combobox.current(0)

                heatmap_info_label.config(text=f"Loaded {len(multiple_stdf_data)} STDF files")

                # Update heatmap display
                update_multi_stdf_heatmap()

    config_status_label.config(text="Configuration applied!", fg="green")
    print(f"\n{'='*60}")
    print("Configuration applied successfully!")
    print(f"{'='*60}\n")


# Configuration tab header
config_header = tk.Label(
    tab7,
    text="Directory Configuration",
    font=("Helvetica", 16, "bold")
)
config_header.pack(pady=20)

config_description = tk.Label(
    tab7,
    text="Configure directories for different file types. These can be local or network paths.",
    font=("Helvetica", 10),
    fg="gray"
)
config_description.pack(pady=5)

# Frame for directory settings
config_frame = tk.Frame(tab7)
config_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

# Directory configuration entries
dir_configs = [
    ("stdf", "STDF Files (STDDatalog)", "Binary STDF test data files (.stdf, .std)"),
    ("images", "Image Files (ImageCaptures)", "Die images (.jpg, .png, .tif, etc.)"),
    ("csv", "CSV Files", "Comma-separated value files (.csv)"),
    ("txt", "TXT Files (TXTDatalog)", "Text datalog files (.txt, .atdf)"),
    ("plm", "PLM Files", "PLM data files")
]

for idx, (key, label, description) in enumerate(dir_configs):
    # Create frame for each directory setting
    dir_frame = tk.Frame(config_frame)
    dir_frame.pack(fill=tk.X, pady=10)

    # Label
    dir_label = tk.Label(
        dir_frame,
        text=label,
        font=("Helvetica", 11, "bold"),
        width=25,
        anchor="w"
    )
    dir_label.pack(side=tk.LEFT, padx=5)

    # Entry for path
    dir_entry = tk.Entry(
        dir_frame,
        textvariable=config_dirs[key],
        width=60,
        font=("Helvetica", 10)
    )
    dir_entry.pack(side=tk.LEFT, padx=5)

    # Browse button
    browse_btn = tk.Button(
        dir_frame,
        text="Browse...",
        command=lambda k=key: browse_directory(k),
        font=("Helvetica", 9)
    )
    browse_btn.pack(side=tk.LEFT, padx=5)

    # Status indicator
    status_indicator = tk.Label(
        dir_frame,
        text="●",
        font=("Helvetica", 12),
        fg="gray"
    )
    status_indicator.pack(side=tk.LEFT, padx=5)

    # Description label
    desc_label = tk.Label(
        config_frame,
        text=f"    {description}",
        font=("Helvetica", 9),
        fg="gray",
        anchor="w"
    )
    desc_label.pack(fill=tk.X, padx=30)

# Separator
separator = ttk.Separator(tab7, orient='horizontal')
separator.pack(fill=tk.X, padx=40, pady=20)

# Buttons frame
buttons_frame = tk.Frame(tab7)
buttons_frame.pack(pady=10)

# Save Configuration button
save_config_btn = tk.Button(
    buttons_frame,
    text="Save Configuration",
    command=save_config,
    font=("Helvetica", 11),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=5
)
save_config_btn.pack(side=tk.LEFT, padx=10)

# Load Configuration button
load_config_btn = tk.Button(
    buttons_frame,
    text="Load Configuration",
    command=load_config,
    font=("Helvetica", 11),
    bg="#2196F3",
    fg="white",
    padx=20,
    pady=5
)
load_config_btn.pack(side=tk.LEFT, padx=10)

# Apply & Load Data button
apply_config_btn = tk.Button(
    buttons_frame,
    text="Apply & Load Data",
    command=apply_config_and_load,
    font=("Helvetica", 11),
    bg="#FF9800",
    fg="white",
    padx=20,
    pady=5
)
apply_config_btn.pack(side=tk.LEFT, padx=10)

# Status label
config_status_label = tk.Label(
    tab7,
    text="0/5 directories configured",
    font=("Helvetica", 10),
    fg="gray"
)
config_status_label.pack(pady=10)

# Quick Setup section
quick_setup_frame = tk.LabelFrame(tab7, text="Quick Setup", font=("Helvetica", 11, "bold"))
quick_setup_frame.pack(fill=tk.X, padx=40, pady=20)

quick_setup_description = tk.Label(
    quick_setup_frame,
    text="Select a project folder with standard subfolder structure (STDDatalog, ImageCaptures, CSVFiles, TXTDatalog, PLMFiles)",
    font=("Helvetica", 9),
    fg="gray"
)
quick_setup_description.pack(pady=5)


def quick_setup_from_project():
    """Auto-configure from project folder with standard structure"""
    folder_path = filedialog.askdirectory(
        title="Select Project Root Folder"
    )

    if not folder_path:
        return

    print(f"Auto-configuring from project folder: {folder_path}")

    # Map standard subfolders
    subfolder_map = {
        "stdf": "STDDatalog",
        "images": "ImageCaptures",
        "csv": "CSVFiles",
        "txt": "TXTDatalog",
        "plm": "PLMFiles"
    }

    found_count = 0
    for key, subfolder in subfolder_map.items():
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.exists(subfolder_path):
            config_dirs[key].set(subfolder_path)
            found_count += 1
            print(f"  Found {subfolder}: {subfolder_path}")
        else:
            print(f"  Missing {subfolder}")

    update_config_status()
    config_status_label.config(
        text=f"Found {found_count}/5 subfolders in project",
        fg="green" if found_count > 0 else "orange"
    )


quick_setup_btn = tk.Button(
    quick_setup_frame,
    text="Auto-Configure from Project Folder",
    command=quick_setup_from_project,
    font=("Helvetica", 10),
    bg="#9C27B0",
    fg="white",
    padx=15,
    pady=5
)
quick_setup_btn.pack(pady=10)

# Load saved configuration on startup
load_config()


main_win.mainloop()
