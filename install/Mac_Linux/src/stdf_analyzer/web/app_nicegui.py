"""
STDF Wafermap Analyzer - NiceGUI Web App (Wafer Tab)
Usage: py -3.13 app_nicegui.py -> http://localhost:8100
"""

import os, sys, tempfile, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from nicegui import ui, events
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

@dataclass
class STDFData:
    wafer_id: str = ""
    dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    parameters: Dict[str, str] = field(default_factory=dict)
    grouped_parameters: Dict[str, List] = field(default_factory=dict)
    test_limits: Dict = field(default_factory=dict)

BIN_COLORS = {1:'#00FF00',2:'#FF0000',3:'#0000FF',4:'#FFFF00',5:'#FF00FF',6:'#00FFFF',7:'#FFA500',8:'#800080',9:'#808080',10:'#A52A2A'}

def extract_group(col):
    c = str(col).upper()
    for p, g in [('DC_CONT','DC_CONT'),('DC_LKG','DC_LKG'),('ANLG_ADC','ANLG_ADC'),('OPTIC_','OPTIC'),('FUNC_','FUNC')]:
        if p in c: return g
    if '_' in c:
        parts = c.split('_')
        if parts[0] in ['DC','ANLG','OPTIC','FUNC','DIGITAL','POWER']: return parts[0]
    return "Other"

def simplify_name(name):
    if not name: return name
    n = re.sub(r'_\d{5,}$', '', str(name))
    parts = n.split('_')
    if len(parts) >= 3 and parts[0] in ['DC','ANLG','OPTIC','FUNC']:
        n = '_'.join(parts[2:])
    return n[:25] if len(n) > 25 else n

def parse_csv(path):
    try:
        df = pd.read_csv(path)
        xcols = ['x','X','x_coord','X_COORD','DIE_X']
        ycols = ['y','Y','y_coord','Y_COORD','DIE_Y']
        xc = next((c for c in xcols if c in df.columns), None)
        yc = next((c for c in ycols if c in df.columns), None)
        if not xc or not yc:
            nums = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(nums) >= 2: xc, yc = nums[0], nums[1]
        if not xc: return None
        df = df.rename(columns={xc:'x', yc:'y'})
        for bc in ['bin','BIN','HARD_BIN','HB']:
            if bc in df.columns: df = df.rename(columns={bc:'bin'}); break
        if 'bin' not in df.columns: df['bin'] = 1

        params, groups, limits = {}, {}, {}
        nums = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ['x','y','bin']]
        for i, col in enumerate(nums):
            m = re.search(r'_(\d{5,})$', str(col))
            tn = int(m.group(1)) if m else i+1000
            df = df.rename(columns={col: tn})
            params[f"test_{tn}"] = col
            g = extract_group(col)
            if g not in groups: groups[g] = []
            groups[g].append((tn, simplify_name(col), col))
            v = df[tn].dropna()
            if len(v): limits[tn] = {'lo': v.min(), 'hi': v.max()}

        return STDFData(wafer_id=os.path.basename(path).replace('.csv',''), dataframe=df, parameters=params, grouped_parameters=groups, test_limits=limits)
    except Exception as e:
        print(f"CSV Error: {e}")
        return None

def parse_stdf(path):
    try:
        import Semi_ATE.STDF as stdf
        recs = list(stdf.records_from_file(path))
        wid, dies, params, groups, limits = "", {}, {}, {}, {}
        for r in recs:
            rt = type(r).__name__
            if rt == 'WIR': wid = getattr(r,'WAFER_ID','')
            elif rt == 'PTR':
                tn, txt, res = getattr(r,'TEST_NUM',0), getattr(r,'TEST_TXT',''), getattr(r,'RESULT',np.nan)
                x, y = getattr(r,'X_COORD',0), getattr(r,'Y_COORD',0)
                k = (x,y)
                if k not in dies: dies[k] = {'x':x,'y':y}
                dies[k][tn] = res
                if tn not in params:
                    params[f"test_{tn}"] = txt
                    g = extract_group(txt)
                    if g not in groups: groups[g] = []
                    groups[g].append((tn, simplify_name(txt), txt))
                    limits[tn] = {'lo': getattr(r,'LO_LIMIT',None), 'hi': getattr(r,'HI_LIMIT',None)}
            elif rt == 'PRR':
                x, y, hb = getattr(r,'X_COORD',0), getattr(r,'Y_COORD',0), getattr(r,'HARD_BIN',0)
                k = (x,y)
                if k not in dies: dies[k] = {'x':x,'y':y}
                dies[k]['bin'] = hb
        if not dies: return parse_csv(path)
        df = pd.DataFrame(list(dies.values()))
        if 'bin' not in df.columns: df['bin'] = 1
        return STDFData(wafer_id=wid or os.path.basename(path), dataframe=df, parameters=params, grouped_parameters=groups, test_limits=limits)
    except: return parse_csv(path)

def load_file(p): return parse_csv(p) if p.lower().endswith('.csv') else parse_stdf(p)

class State:
    def __init__(self):
        self.files: Dict[str, STDFData] = {}
        self.current: str = None
        self.group: str = "All"
        self.param: str = "BIN (Bin Number)"
        self.custom_tests: Dict = {}
        self.selected_die: Tuple[int, int] = None
        self.image_dir: str = ""
        self.plm_dir: str = ""

st = State()

def make_wafermap(data, param='bin', width=900, height=750):
    """Create wafermap heatmap - larger size for better visibility"""
    df = data.dataframe
    col = 'bin'
    if param != 'bin' and param != 'BIN (Bin Number)':
        m = re.search(r'test_(\d+)', str(param))
        col = int(m.group(1)) if m else param
    if col not in df.columns: col = 'bin'

    mask = df[col].notna() & df['x'].notna()
    p = df[mask].copy()
    if len(p) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No data", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return fig

    x, y = p['x'].astype(int), p['y'].astype(int)
    xn, xx, yn, yx = x.min(), x.max(), y.min(), y.max()
    gw, gh = xx-xn+1, yx-yn+1
    grid = np.full((gh, gw), np.nan)
    for i in range(len(p)):
        grid[int(p['y'].iloc[i])-yn, int(p['x'].iloc[i])-xn] = p[col].iloc[i]

    # Custom data for click events (die coordinates)
    custom_x = [[xn+xi for xi in range(gw)] for _ in range(gh)]
    custom_y = [[yn+yi for _ in range(gw)] for yi in range(gh)]
    
    hover = [[f"Die({xn+xi},{yn+yi})<br>{'Bin:'+str(int(grid[yi,xi])) if col=='bin' else 'Val:'+f'{grid[yi,xi]:.4f}'}" if not np.isnan(grid[yi,xi]) else f"({xn+xi},{yn+yi}) No data" for xi in range(gw)] for yi in range(gh)]

    if col == 'bin':
        bins = sorted(p[col].dropna().unique())
        cols = [BIN_COLORS.get(int(b),'#808080') for b in bins]
        cs = [[i/max(1,len(bins)-1),c] for i,c in enumerate(cols)] if len(bins)>1 else [[0,cols[0]],[1,cols[0]]]
        fig = go.Figure(go.Heatmap(
            z=grid, colorscale=cs, zmin=min(bins), zmax=max(bins), 
            hovertext=hover, hoverinfo='text', 
            colorbar=dict(title='Bin', thickness=15), 
            xgap=1, ygap=1,
            customdata=np.dstack([custom_x, custom_y])
        ))
    else:
        fig = go.Figure(go.Heatmap(
            z=grid, colorscale='Viridis', 
            hovertext=hover, hoverinfo='text', 
            colorbar=dict(title=simplify_name(str(col)), thickness=15), 
            xgap=1, ygap=1,
            customdata=np.dstack([custom_x, custom_y])
        ))

    v = p[col].dropna()
    fig.update_layout(
        title=dict(text=f"{data.wafer_id} - {simplify_name(str(col))}", font=dict(size=16)),
        xaxis=dict(title='X', side='top', scaleanchor='y', constrain='domain'),
        yaxis=dict(title='Y', autorange='reversed', constrain='domain'),
        width=width, height=height,
        margin=dict(l=60, r=30, t=80, b=60),
        dragmode='zoom'
    )
    fig.add_annotation(
        text=f"N:{len(v)} | Min:{v.min():.3f} | Max:{v.max():.3f} | Mean:{v.mean():.3f} | Std:{v.std():.3f}", 
        x=0.5, y=-0.06, xref="paper", yref="paper", showarrow=False, font=dict(size=11)
    )
    return fig

def make_dist(data, param='bin'):
    df = data.dataframe
    col = 'bin'
    if param != 'bin' and param != 'BIN (Bin Number)':
        m = re.search(r'test_(\d+)', str(param))
        col = int(m.group(1)) if m else param
    if col not in df.columns: return go.Figure()
    v = df[col].dropna()
    if len(v) == 0: return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=v, nbinsx=50, opacity=0.7, name='Histogram'))
    mu, sig = v.mean(), v.std()
    if sig > 0:
        xr = np.linspace(v.min(), v.max(), 100)
        fig.add_trace(go.Scatter(x=xr, y=stats.norm.pdf(xr,mu,sig)*len(v)*(v.max()-v.min())/50, mode='lines', line=dict(color='red'), name='Normal'))
    fig.add_vline(x=mu, line_dash="dash", line_color="green")
    fig.update_layout(title=f"Distribution - {simplify_name(str(col))}", width=850, height=350, showlegend=True)
    return fig

@ui.page('/')
def main():
    ui.dark_mode(False)

    def data(): return st.files.get(st.current)

    def get_groups():
        d = data()
        return ['All'] + sorted(d.grouped_parameters.keys()) if d else ['All']

    def get_params():
        d = data()
        opts = ['BIN (Bin Number)']
        if not d: return opts
        if st.group == 'All':
            for k, n in sorted(d.parameters.items()): opts.append(f"{k}: {simplify_name(n)}")
        elif st.group in d.grouped_parameters:
            for tn, sn, fn in d.grouped_parameters[st.group]: opts.append(f"test_{tn}: {sn}")
        for n in st.custom_tests: opts.append(f"CUSTOM: {n}")
        return opts

    def get_die_params(x, y):
        """Get all parameter values for a specific die"""
        d = data()
        if not d: return []
        df = d.dataframe
        die_row = df[(df['x'] == x) & (df['y'] == y)]
        if len(die_row) == 0: return []
        row = die_row.iloc[0]
        params = []
        params.append(('Bin', int(row.get('bin', 0))))
        for k, name in sorted(d.parameters.items()):
            m = re.search(r'test_(\d+)', k)
            if m:
                tn = int(m.group(1))
                if tn in row.index:
                    val = row[tn]
                    if pd.notna(val):
                        params.append((simplify_name(name), f"{val:.4f}"))
        return params

    @ui.refreshable
    def controls_bar():
        with ui.row().classes('w-full items-center gap-3 p-3 bg-blue-50 border-b'):
            ui.upload(on_upload=upload, auto_upload=True).props('accept=".stdf,.csv" label="📂 Upload" color=primary').classes('w-36')
            ui.button('📁 Browse', on_click=browse).props('dense color=secondary')
            ui.label('|').classes('text-gray-300')
            ui.label('Group:')
            ui.select(get_groups(), value=st.group, on_change=lambda e: on_group(e.value)).classes('w-36').props('dense outlined')
            ui.label('Param:')
            ui.select(get_params(), value=st.param, on_change=lambda e: on_param(e.value)).classes('w-64').props('dense outlined')
            ui.button('🔄', on_click=refresh_all).props('dense flat')
            ui.space()
            n = len(st.files)
            ui.label(f'{n} files | {sum(len(d.dataframe) for d in st.files.values())} dies' if n else 'No files').classes('text-gray-600')

    @ui.refreshable
    def files_panel():
        if not st.files:
            ui.label('No files loaded').classes('text-gray-500 p-2')
            return
        for fn, d in st.files.items():
            cur = fn == st.current
            with ui.row().classes('items-center w-full'):
                ui.button(f"{'▶' if cur else '○'} {fn[:20]}", on_click=lambda f=fn: sel(f)).props(f"flat dense {'color=primary' if cur else ''}").classes('text-left')
                ui.label(f"({len(d.dataframe)})").classes('text-xs text-gray-500')

    @ui.refreshable
    def stats_panel():
        d = data()
        if not d:
            ui.label('Load file first').classes('text-gray-500 p-2')
            return
        df = d.dataframe
        col = 'bin'
        if st.param and st.param != 'BIN (Bin Number)':
            m = re.search(r'test_(\d+)', st.param)
            col = int(m.group(1)) if m else 'bin'
        if col not in df.columns: col = 'bin'
        v = df[col].dropna()
        
        ui.label(f'📊 {simplify_name(str(col))}').classes('font-bold text-sm')
        with ui.element('div').classes('text-xs space-y-1'):
            for l, val in [('N',len(v)),('Min',f'{v.min():.4f}'),('Max',f'{v.max():.4f}'),('Mean',f'{v.mean():.4f}'),('Std',f'{v.std():.4f}')]:
                with ui.row().classes('justify-between w-full'):
                    ui.label(l)
                    ui.label(str(val)).classes('font-mono')
        if col == 'bin':
            ui.separator()
            tot, ps = len(df), len(df[df['bin']==1])
            yld = ps/tot*100 if tot else 0
            ui.label(f'Yield: {yld:.1f}%').classes('font-bold text-sm ' + ('text-green-600' if yld>90 else 'text-red-600'))

    @ui.refreshable
    def die_info_panel():
        """Show all parameters for the selected die"""
        if not st.selected_die:
            ui.label('Click on a die in the wafermap').classes('text-gray-500 p-2 text-sm')
            return
        x, y = st.selected_die
        ui.label(f'🎯 Die ({x}, {y})').classes('font-bold text-blue-600')
        params = get_die_params(x, y)
        if not params:
            ui.label('No data for this die').classes('text-gray-500')
            return
        with ui.scroll_area().classes('h-48'):
            with ui.element('div').classes('text-xs space-y-0.5'):
                for name, val in params:
                    with ui.row().classes('justify-between w-full hover:bg-gray-100 px-1'):
                        ui.label(name).classes('truncate max-w-24')
                        ui.label(str(val)).classes('font-mono text-right')

    @ui.refreshable
    def images_panel():
        """Show die images section"""
        ui.label('📷 Images').classes('font-bold text-sm')
        if not st.image_dir:
            with ui.row().classes('gap-1 items-center'):
                ui.button('Set Folder', on_click=set_image_dir).props('flat dense size=sm')
        else:
            ui.label(f'📁 {os.path.basename(st.image_dir)}').classes('text-xs text-gray-500 truncate')
            if st.selected_die:
                x, y = st.selected_die
                ui.label(f'Die ({x},{y}) images...').classes('text-xs text-gray-400')
            else:
                ui.label('Select a die').classes('text-xs text-gray-400')

    @ui.refreshable
    def plm_panel():
        """Show PLM files section"""
        ui.label('📊 PLM Files').classes('font-bold text-sm')
        if not st.plm_dir:
            with ui.row().classes('gap-1 items-center'):
                ui.button('Set Folder', on_click=set_plm_dir).props('flat dense size=sm')
        else:
            ui.label(f'📁 {os.path.basename(st.plm_dir)}').classes('text-xs text-gray-500 truncate')
            if st.selected_die:
                x, y = st.selected_die
                ui.label(f'Die ({x},{y}) PLM...').classes('text-xs text-gray-400')
            else:
                ui.label('Select a die').classes('text-xs text-gray-400')

    @ui.refreshable
    def wafermap_plot():
        d = data()
        if d:
            fig = make_wafermap(d, st.param)
            plot = ui.plotly(fig).classes('w-full h-full')
            # Die click handler
            plot.on('plotly_click', lambda e: on_die_click(e))
        else:
            with ui.column().classes('items-center justify-center h-96'):
                ui.icon('upload_file', size='xl').classes('text-gray-300')
                ui.label('📊 Load a file to see wafermap').classes('text-gray-400 text-xl')

    @ui.refreshable
    def dist_plot():
        d = data()
        if d:
            fig = make_dist(d, st.param)
            ui.plotly(fig).classes('w-full')
        else:
            ui.label('📊 Load a file to see distribution').classes('text-gray-400 p-4')

    def on_die_click(e):
        """Handle click on die in wafermap"""
        try:
            if e.args and 'points' in e.args and len(e.args['points']) > 0:
                pt = e.args['points'][0]
                if 'customdata' in pt:
                    x, y = int(pt['customdata'][0]), int(pt['customdata'][1])
                    st.selected_die = (x, y)
                    die_info_panel.refresh()
                    images_panel.refresh()
                    plm_panel.refresh()
                    ui.notify(f'Selected Die ({x}, {y})', type='info')
        except Exception as ex:
            print(f"Click error: {ex}")

    def refresh_all():
        controls_bar.refresh()
        files_panel.refresh()
        stats_panel.refresh()
        wafermap_plot.refresh()
        dist_plot.refresh()
        die_info_panel.refresh()

    def on_group(val):
        st.group = val
        st.param = 'BIN (Bin Number)'
        refresh_all()

    def on_param(val):
        st.param = val
        stats_panel.refresh()
        wafermap_plot.refresh()
        dist_plot.refresh()

    def sel(f):
        st.current = f
        st.group = 'All'
        st.param = 'BIN (Bin Number)'
        st.selected_die = None
        refresh_all()

    async def upload(e: events.UploadEventArguments):
        try:
            fname = e.file.name if hasattr(e.file, 'name') else 'uploaded_file.csv'
            print(f"Upload: {fname}")
            content = await e.file.read()
            print(f"Size: {len(content)} bytes")
            ext = os.path.splitext(fname)[1] if fname else '.csv'
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode='wb') as f:
                f.write(content)
                tmp = f.name
            d = load_file(tmp)
            os.unlink(tmp)
            if d:
                st.files[fname] = d
                st.current = fname
                st.group = 'All'
                st.param = 'BIN (Bin Number)'
                st.selected_die = None
                print(f"Loaded: {fname} - {len(d.dataframe)} dies, groups: {list(d.grouped_parameters.keys())}")
                ui.notify(f'✅ {fname} ({len(d.dataframe)} dies)', type='positive')
                refresh_all()
            else:
                ui.notify('❌ Parse failed', type='negative')
        except Exception as ex:
            print(f"Error: {ex}")
            import traceback; traceback.print_exc()
            ui.notify(f'❌ {ex}', type='negative')

    async def browse():
        with ui.dialog() as dlg, ui.card().classes('w-[500px]'):
            ui.label('📁 Load Path').classes('text-xl font-bold')
            inp = ui.input('Path', value=r'C:\Users\szenklarz\Desktop\VS_Folder\AM Data').classes('w-full')
            for p in [r'C:\Users\szenklarz\Desktop\VS_Folder\AM Data', r'C:\Users\szenklarz\Desktop\VS_Folder\Tooltest']:
                ui.button(os.path.basename(p), on_click=lambda p=p: inp.set_value(p)).props('flat dense size=sm')
            async def go():
                path = inp.value
                cnt = 0
                if os.path.isfile(path):
                    d = load_file(path)
                    if d: st.files[os.path.basename(path)] = d; st.current = os.path.basename(path); cnt = 1
                elif os.path.isdir(path):
                    for f in os.listdir(path):
                        if f.lower().endswith(('.stdf','.csv')):
                            d = load_file(os.path.join(path,f))
                            if d: st.files[f] = d; st.current = f; cnt += 1
                if cnt:
                    st.group = 'All'
                    st.param = 'BIN (Bin Number)'
                    st.selected_die = None
                    ui.notify(f'✅ {cnt} file(s)', type='positive')
                    refresh_all()
                dlg.close()
            with ui.row(): ui.button('Load', on_click=go).props('color=primary'); ui.button('Cancel', on_click=dlg.close).props('flat')
        dlg.open()

    async def set_image_dir():
        with ui.dialog() as dlg, ui.card().classes('w-[400px]'):
            ui.label('📷 Set Image Directory').classes('font-bold')
            inp = ui.input('Path', value=st.image_dir or r'C:\Users\szenklarz\Desktop\VS_Folder\Images').classes('w-full')
            def save():
                st.image_dir = inp.value
                images_panel.refresh()
                dlg.close()
            with ui.row(): ui.button('Set', on_click=save).props('color=primary'); ui.button('Cancel', on_click=dlg.close).props('flat')
        dlg.open()

    async def set_plm_dir():
        with ui.dialog() as dlg, ui.card().classes('w-[400px]'):
            ui.label('📊 Set PLM Directory').classes('font-bold')
            inp = ui.input('Path', value=st.plm_dir or r'C:\Users\szenklarz\Desktop\VS_Folder\PLM').classes('w-full')
            def save():
                st.plm_dir = inp.value
                plm_panel.refresh()
                dlg.close()
            with ui.row(): ui.button('Set', on_click=save).props('color=primary'); ui.button('Cancel', on_click=dlg.close).props('flat')
        dlg.open()

    async def custom_test():
        d = data()
        if not d: ui.notify('Load file first', type='warning'); return
        with ui.dialog() as dlg, ui.card().classes('w-[600px]'):
            ui.label('🧮 Custom Test').classes('text-xl font-bold')
            nm = ui.input('Name', placeholder='DELTA_VDD').classes('w-full')
            ui.label('Available Params:').classes('font-medium')
            with ui.scroll_area().classes('h-24 border'):
                for k, n in list(d.parameters.items())[:15]: ui.label(f'{k}').classes('text-xs font-mono')
            fm = ui.textarea('Formula', placeholder='test_1001 - test_1002').classes('w-full')
            def save():
                if nm.value and fm.value:
                    st.custom_tests[nm.value] = fm.value
                    df = d.dataframe
                    try:
                        expr = fm.value
                        for m in re.finditer(r'test_(\d+)', expr):
                            tn = int(m.group(1))
                            if tn in df.columns: expr = expr.replace(f'test_{tn}', f'df[{tn}]')
                        df[f'CUSTOM_{nm.value}'] = eval(expr)
                        ui.notify(f'✅ Created {nm.value}', type='positive')
                        refresh_all()
                    except Exception as ex: ui.notify(f'Error: {ex}', type='negative')
                dlg.close()
            with ui.row(): ui.button('Create', on_click=save).props('color=primary'); ui.button('Cancel', on_click=dlg.close).props('flat')
        dlg.open()

    async def save_data():
        d = data()
        if not d: ui.notify('No data', type='warning'); return
        path = os.path.join(tempfile.gettempdir(), f'{d.wafer_id}_export.csv')
        d.dataframe.to_csv(path, index=False)
        ui.notify(f'💾 Saved: {path}', type='positive')

    # ==================== LAYOUT ====================
    
    # HEADER
    with ui.header().classes('bg-blue-700 text-white'):
        ui.label('🔬 STDF Wafermap Analyzer').classes('text-2xl font-bold')
        ui.space()
        ui.label('Wafer Tab').classes('opacity-80')

    # CONTROLS BAR
    controls_bar()

    # TOOLS ROW
    with ui.row().classes('w-full items-center gap-2 p-2 bg-gray-100 border-b'):
        ui.button('🧮 Custom Test', on_click=custom_test).props('dense color=purple')
        ui.button('💾 Save Data', on_click=save_data).props('dense color=blue')
        ui.button('📊 Export Stats', on_click=lambda: ui.notify('Stats exported')).props('dense')

    # MAIN CONTENT - 3 columns
    with ui.row().classes('w-full flex-nowrap gap-2 p-2').style('height: calc(100vh - 160px)'):
        
        # LEFT PANEL - Wafer Selection & Statistics (narrower)
        with ui.card().classes('h-full flex-shrink-0').style('width: 200px'):
            # Wafer Selection
            with ui.expansion('📋 Wafers', value=True).classes('w-full'):
                with ui.column().classes('w-full max-h-32 overflow-auto'):
                    files_panel()
            
            ui.separator()
            
            # Statistics
            with ui.expansion('📊 Statistics', value=True).classes('w-full'):
                with ui.column().classes('w-full'):
                    stats_panel()

        # CENTER - Wafermap & Distribution (takes most space)
        with ui.card().classes('flex-grow h-full'):
            with ui.tabs().classes('w-full') as tabs:
                t1 = ui.tab('Wafermap')
                t2 = ui.tab('Distribution')
            with ui.tab_panels(tabs, value=t1).classes('w-full h-full'):
                with ui.tab_panel(t1).classes('h-full p-0'):
                    wafermap_plot()
                with ui.tab_panel(t2).classes('p-2'):
                    dist_plot()

        # RIGHT PANEL - Die Info, Images & PLM (narrower)
        with ui.card().classes('h-full flex-shrink-0').style('width: 220px'):
            # Die Info
            with ui.expansion('🎯 Selected Die', value=True).classes('w-full'):
                with ui.column().classes('w-full'):
                    die_info_panel()
            
            ui.separator()
            
            # Images Section
            with ui.expansion('📷 Images', value=True).classes('w-full'):
                with ui.column().classes('w-full'):
                    images_panel()
            
            ui.separator()
            
            # PLM Section
            with ui.expansion('📊 PLM Files', value=True).classes('w-full'):
                with ui.column().classes('w-full'):
                    plm_panel()

    # FOOTER
    with ui.footer().classes('bg-gray-200'):
        ui.label('© 2026 Krzysztof Szenklarz').classes('text-sm text-gray-600')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='STDF Wafermap Analyzer', port=8200, reload=False, show=True)
