"""
STDF Wafermap Analyzer - Web Application

A Streamlit-based web interface for analyzing semiconductor test data.

Usage:
    streamlit run app.py
"""

import os
import sys
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.stdf_analyzer.core.binning import BinningLookup
from src.stdf_analyzer.core.stdf_parser import parse_stdf_file, parse_csv_file, STDFData
from src.stdf_analyzer.core.wafermap import WafermapGenerator, create_multi_wafer_comparison

# Page configuration
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
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'loaded_files' not in st.session_state:
        st.session_state.loaded_files = {}
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'binning_lookup' not in st.session_state:
        st.session_state.binning_lookup = BinningLookup()


def load_file(uploaded_file) -> STDFData:
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
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        return data
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


def render_sidebar():
    """Render the sidebar with file upload and settings"""
    with st.sidebar:
        st.markdown("## 📁 Datei-Upload")
        
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
                        try:
                            data = load_file(uploaded_file)
                            st.session_state.loaded_files[uploaded_file.name] = data
                            st.success(f"✅ {uploaded_file.name} geladen")
                        except Exception as e:
                            st.error(f"❌ Fehler: {e}")
        
        if st.session_state.loaded_files:
            st.markdown("---")
            st.markdown("## 📋 Geladene Dateien")
            
            file_options = list(st.session_state.loaded_files.keys())
            selected_file = st.selectbox(
                "Aktive Datei wählen:",
                file_options,
                index=0 if st.session_state.current_file is None else file_options.index(st.session_state.current_file) if st.session_state.current_file in file_options else 0
            )
            st.session_state.current_file = selected_file
            
            if st.button("🗑️ Alle Dateien löschen"):
                st.session_state.loaded_files = {}
                st.session_state.current_file = None
                st.rerun()
        
        st.markdown("---")
        st.markdown("## ⚙️ Einstellungen")
        
        # Binning file upload
        binning_file = st.file_uploader(
            "Binning Excel-Datei (optional)",
            type=['xlsx', 'xls'],
            help="Excel-Datei mit Bin-Definitionen"
        )
        
        if binning_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(binning_file.getvalue())
                tmp_path = tmp.name
            
            if st.session_state.binning_lookup.load_from_excel(tmp_path):
                st.success("✅ Binning-Datei geladen")
            os.unlink(tmp_path)


def render_wafermap_tab():
    """Render the single wafermap view tab"""
    if not st.session_state.current_file:
        st.info("👆 Bitte laden Sie eine STDF oder CSV Datei im Seitenmenü hoch.")
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
            st.write(f"**Min:** {stats.get('min', 'N/A')}")
            st.write(f"**Max:** {stats.get('max', 'N/A')}")
            st.write(f"**Mean:** {stats.get('mean', 'N/A'):.4f}" if stats.get('mean') else "Mean: N/A")
            st.write(f"**Std:** {stats.get('std', 'N/A'):.4f}" if stats.get('std') else "Std: N/A")
    
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
        st.info("👆 Bitte laden Sie mindestens 2 Dateien für den Multi-Wafer-Vergleich hoch.")
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
        st.info("👆 Bitte laden Sie eine Datei hoch.")
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


def main():
    """Main application entry point"""
    init_session_state()
    
    # Header
    st.markdown('<p class="main-header">🔬 STDF Wafermap Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Halbleiter-Testdaten Analyse und Visualisierung</p>', unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📊 Wafermap", "📈 Multi-Wafer", "📋 Rohdaten"])
    
    with tab1:
        render_wafermap_tab()
    
    with tab2:
        render_multi_wafer_tab()
    
    with tab3:
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
