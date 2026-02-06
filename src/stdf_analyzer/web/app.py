"""
STDF Wafermap Analyzer - Web Application

A Streamlit-based web interface for analyzing semiconductor test data.
Supports both file upload and network share browsing.

Usage:
    streamlit run app.py
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

import streamlit as st
import pandas as pd

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.stdf_analyzer.core.binning import BinningLookup
from src.stdf_analyzer.core.stdf_parser import parse_stdf_file, parse_csv_file, STDFData
from src.stdf_analyzer.core.wafermap import WafermapGenerator, create_multi_wafer_comparison

# ============================================================================
# Configuration
# ============================================================================

# Default network share paths (can be customized)
DEFAULT_SHARE_PATHS = [
    r"C:\Users\szenklarz\Desktop\VS_Folder\AM Data",  # Local test path
    r"C:\Users\szenklarz\Desktop\VS_Folder\Tooltest",  # Local test path
    # Add your network shares here:
    # r"\\server\stdf_data",
    # r"\\nas\semiconductor\wafer_tests",
]

SUPPORTED_EXTENSIONS = ['.stdf', '.csv']

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="STDF Wafermap Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
    }
    .file-browser {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    .folder-item {
        padding: 5px 10px;
        margin: 2px 0;
        border-radius: 4px;
        cursor: pointer;
    }
    .folder-item:hover {
        background-color: #e9ecef;
    }
    .breadcrumb {
        background-color: #e9ecef;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 10px;
        font-family: monospace;
    }
    .file-info {
        font-size: 0.85rem;
        color: #666;
    }
    .stdf-file {
        color: #28a745;
        font-weight: bold;
    }
    .csv-file {
        color: #007bff;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'loaded_files' not in st.session_state:
        st.session_state.loaded_files = {}
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'binning_lookup' not in st.session_state:
        st.session_state.binning_lookup = BinningLookup()
    if 'current_path' not in st.session_state:
        st.session_state.current_path = None
    if 'favorite_paths' not in st.session_state:
        st.session_state.favorite_paths = []
    if 'recent_files' not in st.session_state:
        st.session_state.recent_files = []
    if 'data_source' not in st.session_state:
        st.session_state.data_source = "network"  # "upload" or "network"
    if 'custom_share_path' not in st.session_state:
        st.session_state.custom_share_path = ""


# ============================================================================
# File System Utilities
# ============================================================================

def is_valid_path(path: str) -> bool:
    """Check if a path exists and is accessible"""
    try:
        return os.path.exists(path)
    except (OSError, PermissionError):
        return False


def get_folder_contents(path: str) -> Tuple[List[str], List[dict]]:
    """
    Get contents of a folder.
    
    Returns:
        Tuple of (folder_names, file_info_list)
        where file_info_list contains dicts with name, size, modified, extension
    """
    folders = []
    files = []
    
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isdir(item_path):
                    folders.append(item)
                elif os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        stat = os.stat(item_path)
                        files.append({
                            'name': item,
                            'path': item_path,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime),
                            'extension': ext
                        })
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError) as e:
        st.error(f"Zugriffsfehler: {e}")
    
    return sorted(folders), sorted(files, key=lambda x: x['name'])


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_path_parts(path: str) -> List[Tuple[str, str]]:
    """
    Split path into parts for breadcrumb navigation.
    Returns list of (name, full_path) tuples.
    """
    parts = []
    current = path
    
    while current:
        parent = os.path.dirname(current)
        name = os.path.basename(current)
        
        if not name:  # Root of drive or UNC path
            parts.insert(0, (current, current))
            break
        
        parts.insert(0, (name, current))
        
        if parent == current:  # Reached root
            break
        current = parent
    
    return parts


def add_to_recent_files(file_path: str, wafer_id: str):
    """Add a file to recent files list"""
    recent = st.session_state.recent_files
    
    # Remove if already exists
    recent = [f for f in recent if f['path'] != file_path]
    
    # Add to front
    recent.insert(0, {
        'path': file_path,
        'name': os.path.basename(file_path),
        'wafer_id': wafer_id,
        'accessed': datetime.now()
    })
    
    # Keep only last 10
    st.session_state.recent_files = recent[:10]


# ============================================================================
# File Loading Functions
# ============================================================================

def load_file_from_path(file_path: str) -> Optional[STDFData]:
    """Load a file from a path (network or local)"""
    if not os.path.exists(file_path):
        st.error(f"Datei nicht gefunden: {file_path}")
        return None
    
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.stdf':
            data = parse_stdf_file(file_path, verbose=False)
        elif ext == '.csv':
            data = parse_csv_file(file_path)
        else:
            st.error(f"Nicht unterstütztes Format: {ext}")
            return None
        
        return data
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return None


def load_uploaded_file(uploaded_file) -> Optional[STDFData]:
    """Load an uploaded file (STDF or CSV)"""
    file_name = uploaded_file.name
    file_ext = Path(file_name).suffix.lower()
    
    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    try:
        if file_ext == '.stdf':
            data = parse_stdf_file(tmp_path, verbose=False)
        elif file_ext == '.csv':
            data = parse_csv_file(tmp_path)
        else:
            st.error(f"Nicht unterstütztes Format: {file_ext}")
            return None
        
        return data
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return None
    finally:
        os.unlink(tmp_path)


# ============================================================================
# UI Components
# ============================================================================

def render_breadcrumb(path: str):
    """Render breadcrumb navigation for current path"""
    if not path:
        return
    
    parts = get_path_parts(path)
    
    cols = st.columns(len(parts) + 1)
    
    with cols[0]:
        if st.button("🏠", key="home_btn", help="Zurück zur Übersicht"):
            st.session_state.current_path = None
            st.rerun()
    
    for i, (name, full_path) in enumerate(parts):
        with cols[i + 1]:
            display_name = name[:15] + "..." if len(name) > 15 else name
            if st.button(f"📁 {display_name}", key=f"bread_{i}", help=full_path):
                st.session_state.current_path = full_path
                st.rerun()


def render_file_browser():
    """Render the network share file browser"""
    
    # Path selection
    st.markdown("### 📂 Netzwerk-Share Browser")
    
    # Show available shares or custom path input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Combine default paths with custom path if set
        available_paths = DEFAULT_SHARE_PATHS.copy()
        if st.session_state.custom_share_path and st.session_state.custom_share_path not in available_paths:
            available_paths.insert(0, st.session_state.custom_share_path)
        
        # Filter to only valid paths
        valid_paths = [p for p in available_paths if is_valid_path(p)]
        
        if not valid_paths:
            st.warning("Keine gültigen Pfade verfügbar. Bitte einen Pfad eingeben:")
            custom_path = st.text_input(
                "Netzwerk-Pfad",
                placeholder=r"\\server\share oder C:\Daten",
                key="new_custom_path"
            )
            if custom_path and st.button("Pfad hinzufügen"):
                if is_valid_path(custom_path):
                    st.session_state.custom_share_path = custom_path
                    st.session_state.current_path = custom_path
                    st.rerun()
                else:
                    st.error("Pfad nicht erreichbar!")
            return
        
        if st.session_state.current_path is None:
            selected_root = st.selectbox(
                "Basis-Pfad wählen",
                valid_paths,
                format_func=lambda x: f"📁 {x}"
            )
        else:
            selected_root = st.session_state.current_path
    
    with col2:
        custom_path = st.text_input(
            "Eigener Pfad",
            placeholder=r"\\server\share",
            key="custom_path_input",
            label_visibility="collapsed"
        )
        if custom_path:
            if st.button("➡️ Öffnen"):
                if is_valid_path(custom_path):
                    st.session_state.current_path = custom_path
                    st.session_state.custom_share_path = custom_path
                    st.rerun()
                else:
                    st.error("Pfad nicht erreichbar!")
    
    # Set current path if not set
    if st.session_state.current_path is None:
        st.session_state.current_path = selected_root
    
    current_path = st.session_state.current_path
    
    # Breadcrumb navigation
    st.markdown("---")
    render_breadcrumb(current_path)
    
    # Get folder contents
    folders, files = get_folder_contents(current_path)
    
    # Layout: Folders and Files
    col_folders, col_files = st.columns([1, 2])
    
    with col_folders:
        st.markdown("#### 📁 Ordner")
        
        # Parent folder button
        parent = os.path.dirname(current_path)
        if parent and parent != current_path:
            if st.button("⬆️ .. (Übergeordnet)", key="parent_folder", use_container_width=True):
                st.session_state.current_path = parent
                st.rerun()
        
        # Folder list
        if folders:
            for folder in folders:
                if st.button(f"📁 {folder}", key=f"folder_{folder}", use_container_width=True):
                    st.session_state.current_path = os.path.join(current_path, folder)
                    st.rerun()
        else:
            st.info("Keine Unterordner")
    
    with col_files:
        st.markdown("#### 📄 Dateien")
        
        if files:
            # File filter
            filter_text = st.text_input("🔍 Filter", placeholder="Dateinamen filtern...", key="file_filter")
            
            filtered_files = files
            if filter_text:
                filtered_files = [f for f in files if filter_text.lower() in f['name'].lower()]
            
            st.markdown(f"*{len(filtered_files)} Datei(en) gefunden*")
            
            # File list
            for file_info in filtered_files:
                col_name, col_size, col_action = st.columns([3, 1, 1])
                
                with col_name:
                    icon = "📊" if file_info['extension'] == '.stdf' else "📋"
                    st.markdown(f"{icon} **{file_info['name']}**")
                    st.caption(f"Geändert: {file_info['modified'].strftime('%d.%m.%Y %H:%M')}")
                
                with col_size:
                    st.markdown(f"<br>{format_file_size(file_info['size'])}", unsafe_allow_html=True)
                
                with col_action:
                    if st.button("📥 Laden", key=f"load_{file_info['name']}", use_container_width=True):
                        with st.spinner(f"Lade {file_info['name']}..."):
                            data = load_file_from_path(file_info['path'])
                            if data:
                                st.session_state.loaded_files[file_info['name']] = data
                                st.session_state.current_file = file_info['name']
                                add_to_recent_files(file_info['path'], data.wafer_id)
                                st.success(f"✅ {file_info['name']} geladen!")
                                st.rerun()
                
                st.markdown("---")
        else:
            st.info("Keine STDF/CSV Dateien in diesem Ordner")
    
    # Recent files section
    if st.session_state.recent_files:
        st.markdown("---")
        st.markdown("#### 🕒 Zuletzt geöffnet")
        
        cols = st.columns(min(5, len(st.session_state.recent_files)))
        for i, recent in enumerate(st.session_state.recent_files[:5]):
            with cols[i]:
                if st.button(
                    f"📄 {recent['name'][:12]}...\n{recent['wafer_id'] or 'N/A'}", 
                    key=f"recent_{i}",
                    use_container_width=True
                ):
                    if is_valid_path(recent['path']):
                        with st.spinner(f"Lade {recent['name']}..."):
                            data = load_file_from_path(recent['path'])
                            if data:
                                st.session_state.loaded_files[recent['name']] = data
                                st.session_state.current_file = recent['name']
                                st.rerun()
                    else:
                        st.error("Datei nicht mehr verfügbar")


def render_upload_section():
    """Render the file upload section"""
    st.markdown("### 📤 Datei-Upload")
    
    uploaded_files = st.file_uploader(
        "STDF oder CSV Dateien hochladen",
        type=['stdf', 'csv'],
        accept_multiple_files=True,
        help="Unterstützt STDF und CSV Formate"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.loaded_files:
                with st.spinner(f"Lade {uploaded_file.name}..."):
                    data = load_uploaded_file(uploaded_file)
                    if data:
                        st.session_state.loaded_files[uploaded_file.name] = data
                        st.session_state.current_file = uploaded_file.name
                        st.success(f"✅ {uploaded_file.name} geladen")


def render_sidebar():
    """Render the sidebar with data source selection and loaded files"""
    with st.sidebar:
        st.markdown("## 📊 Datenquelle")
        
        # Data source toggle
        source = st.radio(
            "Daten laden von:",
            ["🌐 Netzwerk-Share", "📤 Datei-Upload"],
            index=0 if st.session_state.data_source == "network" else 1,
            horizontal=True
        )
        st.session_state.data_source = "network" if "Netzwerk" in source else "upload"
        
        st.markdown("---")
        
        # Loaded files section
        if st.session_state.loaded_files:
            st.markdown("## 📋 Geladene Dateien")
            
            file_options = list(st.session_state.loaded_files.keys())
            
            for fname in file_options:
                data = st.session_state.loaded_files[fname]
                is_selected = fname == st.session_state.current_file
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    btn_style = "primary" if is_selected else "secondary"
                    if st.button(
                        f"{'▶' if is_selected else '○'} {fname[:20]}...",
                        key=f"select_{fname}",
                        use_container_width=True,
                        type=btn_style
                    ):
                        st.session_state.current_file = fname
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{fname}", help="Entfernen"):
                        del st.session_state.loaded_files[fname]
                        if st.session_state.current_file == fname:
                            st.session_state.current_file = None
                        st.rerun()
            
            st.markdown("---")
            if st.button("🗑️ Alle entfernen", use_container_width=True):
                st.session_state.loaded_files = {}
                st.session_state.current_file = None
                st.rerun()
        
        st.markdown("---")
        
        # Binning file upload
        st.markdown("## ⚙️ Einstellungen")
        binning_file = st.file_uploader(
            "Binning Excel-Datei",
            type=['xlsx', 'xls'],
            help="Excel-Datei mit Bin-Definitionen"
        )
        
        if binning_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(binning_file.getvalue())
                tmp_path = tmp.name
            
            if st.session_state.binning_lookup.load_from_excel(tmp_path):
                st.success("✅ Binning geladen")
            os.unlink(tmp_path)


def render_wafermap_tab():
    """Render the single wafermap view tab"""
    if not st.session_state.current_file:
        st.info("👆 Bitte laden Sie eine STDF oder CSV Datei.")
        return
    
    data = st.session_state.loaded_files[st.session_state.current_file]
    generator = WafermapGenerator(data.dataframe, data.wafer_id)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Wafer ID", data.wafer_id or "N/A")
    with col2:
        st.metric("Anzahl Dies", f"{generator.die_count:,}")
    with col3:
        yield_val = generator.get_yield()
        st.metric("Yield", f"{yield_val:.2f}%")
    with col4:
        st.metric("Parameter", data.parameter_count)
    
    st.markdown("---")
    
    # Parameter selection
    col_param, col_display = st.columns([1, 3])
    
    with col_param:
        st.markdown("### Parameter")
        
        # Create parameter options
        param_options = ["bin (Bin Number)"]
        for key, name in sorted(data.test_parameters.items()):
            param_options.append(f"{key}: {name}")
        
        selected_param = st.selectbox(
            "Parameter wählen:",
            param_options,
            index=0
        )
        
        # Extract actual parameter name
        if selected_param.startswith("bin"):
            param_column = "bin"
        else:
            param_column = selected_param.split(":")[0].strip()
        
        st.markdown("### Anzeige-Optionen")
        marker_size = st.slider("Marker-Größe", 5, 30, 12)
        
        st.markdown("### Statistiken")
        stats = generator.get_statistics(param_column)
        if stats:
            st.write(f"**Count:** {stats.get('count', 'N/A')}")
            st.write(f"**Min:** {stats.get('min', 'N/A')}")
            st.write(f"**Max:** {stats.get('max', 'N/A')}")
            if stats.get('mean') is not None:
                st.write(f"**Mean:** {stats.get('mean'):.4f}")
            if stats.get('std') is not None:
                st.write(f"**Std:** {stats.get('std'):.4f}")
    
    with col_display:
        st.markdown("### Wafermap")
        
        try:
            fig = generator.create_plotly_figure(
                parameter=param_column,
                title=f"Wafermap - {data.wafer_id or 'Unknown'}<br><sub>{selected_param}</sub>",
                width=700,
                height=700,
                marker_size=marker_size
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen der Wafermap: {e}")
    
    # Bin Summary
    if param_column == "bin":
        st.markdown("### Bin-Verteilung")
        bin_summary = generator.get_bin_summary()
        if not bin_summary.empty:
            col_table, col_chart = st.columns(2)
            with col_table:
                st.dataframe(bin_summary, use_container_width=True)
            with col_chart:
                import plotly.express as px
                fig_pie = px.pie(
                    bin_summary,
                    values='Count',
                    names='Bin',
                    title='Bin-Verteilung'
                )
                st.plotly_chart(fig_pie, use_container_width=True)


def render_multi_wafer_tab():
    """Render the multi-wafer comparison tab"""
    if len(st.session_state.loaded_files) < 2:
        st.info("👆 Bitte laden Sie mindestens 2 Dateien für den Multi-Wafer-Vergleich.")
        return
    
    st.markdown("### Multi-Wafer Vergleich")
    
    # File selection
    selected_files = st.multiselect(
        "Wafer für Vergleich auswählen:",
        list(st.session_state.loaded_files.keys()),
        default=list(st.session_state.loaded_files.keys())[:4]
    )
    
    if not selected_files:
        st.warning("Bitte wählen Sie mindestens einen Wafer aus.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        cols = st.slider("Spalten", 1, 4, min(3, len(selected_files)))
    with col2:
        # Get common parameters
        all_params = set()
        for fname in selected_files:
            data = st.session_state.loaded_files[fname]
            all_params.update(['bin'] + list(data.test_parameters.keys()))
        
        param = st.selectbox("Parameter", sorted(all_params))
    
    # Create comparison data
    data_list = []
    for fname in selected_files:
        data = st.session_state.loaded_files[fname]
        data_list.append((data.dataframe, data.wafer_id or fname))
    
    # Generate comparison figure
    with st.spinner("Erstelle Vergleichs-Ansicht..."):
        try:
            fig = create_multi_wafer_comparison(
                data_list,
                parameter=param,
                backend="plotly",
                cols=cols
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Erstellen des Vergleichs: {e}")
    
    # Yield comparison table
    st.markdown("### Yield-Vergleich")
    yield_data = []
    for fname in selected_files:
        data = st.session_state.loaded_files[fname]
        gen = WafermapGenerator(data.dataframe, data.wafer_id)
        yield_data.append({
            'Datei': fname,
            'Wafer ID': data.wafer_id or 'N/A',
            'Dies': gen.die_count,
            'Yield (%)': f"{gen.get_yield():.2f}"
        })
    
    st.dataframe(pd.DataFrame(yield_data), use_container_width=True)


def render_data_tab():
    """Render the raw data view tab"""
    if not st.session_state.current_file:
        st.info("👆 Bitte laden Sie eine Datei.")
        return
    
    data = st.session_state.loaded_files[st.session_state.current_file]
    
    st.markdown(f"### Rohdaten: {st.session_state.current_file}")
    st.markdown(f"**Wafer ID:** {data.wafer_id} | **Zeilen:** {len(data.dataframe):,} | **Spalten:** {len(data.dataframe.columns)}")
    
    # Column filter
    cols_to_show = st.multiselect(
        "Spalten auswählen:",
        data.dataframe.columns.tolist(),
        default=['x', 'y', 'bin'] if 'bin' in data.dataframe.columns else data.dataframe.columns.tolist()[:5]
    )
    
    if cols_to_show:
        st.dataframe(data.dataframe[cols_to_show], use_container_width=True, height=500)
    
    # Download button
    csv = data.dataframe.to_csv(index=False)
    st.download_button(
        "📥 Als CSV herunterladen",
        csv,
        f"{data.wafer_id or 'wafer_data'}.csv",
        "text/csv"
    )


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point"""
    init_session_state()
    
    # Header
    st.markdown('<p class="main-header">🔬 STDF Wafermap Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Halbleiter-Testdaten Analyse und Visualisierung</p>', unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content area
    if st.session_state.data_source == "network":
        # Show file browser first if no files loaded
        if not st.session_state.loaded_files:
            render_file_browser()
        else:
            # Show tabs with file browser as option
            tab_browser, tab_wafer, tab_multi, tab_data = st.tabs([
                "📂 Dateien", "📊 Wafermap", "📈 Multi-Wafer", "📋 Rohdaten"
            ])
            
            with tab_browser:
                render_file_browser()
            
            with tab_wafer:
                render_wafermap_tab()
            
            with tab_multi:
                render_multi_wafer_tab()
            
            with tab_data:
                render_data_tab()
    else:
        # Upload mode
        if not st.session_state.loaded_files:
            render_upload_section()
        else:
            tab_upload, tab_wafer, tab_multi, tab_data = st.tabs([
                "📤 Upload", "📊 Wafermap", "📈 Multi-Wafer", "📋 Rohdaten"
            ])
            
            with tab_upload:
                render_upload_section()
            
            with tab_wafer:
                render_wafermap_tab()
            
            with tab_multi:
                render_multi_wafer_tab()
            
            with tab_data:
                render_data_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888;'>"
        "STDF Wafermap Analyzer v1.0.0 | "
        "Entwickelt von Krzysztof Szenklarz"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
