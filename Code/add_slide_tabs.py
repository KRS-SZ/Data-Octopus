#!/usr/bin/env python3
"""Add Slide Tabs system to Wafermap, Diffmap, and GRR Report Tabs"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================================
# WAFERMAP TAB - Replace old single canvas with Slide Tabs system
# ============================================================================

old_wafermap = '''# RIGHT SIDE: Interactive Layout Preview for Wafermap
wafermap_preview_outer_frame = tk.LabelFrame(wafermap_split_frame, text="📐 Slide Layout Preview", font=("Helvetica", 10, "bold"))
wafermap_split_frame.add(wafermap_preview_outer_frame, minsize=300, width=400)

# Layout boxes configuration for Wafermap tab (can be different from Multi-Wafermap)
wafermap_layout_boxes = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "wafermap": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 6.0, "color": "#4CAF50", "fill": "#E8F5E9", "enabled": True, "label": "Wafermap"},
    "boxplot": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#FF9800", "fill": "#FFF3E0", "enabled": True, "label": "Boxplot"},
    "histogram": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 2.9, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Histogram"},
    "stats": {"x": 0.3, "y": 6.8, "width": 12.733, "height": 0.5, "color": "#607D8B", "fill": "#ECEFF1", "enabled": False, "label": "Statistics"},
    "summary": {"x": 0.3, "y": 6.8, "width": 6.0, "height": 0.5, "color": "#E91E63", "fill": "#FCE4EC", "enabled": False, "label": "Summary"},
}

wafermap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None}

# Preview Canvas for Wafermap
wafermap_preview_canvas_frame = tk.Frame(wafermap_preview_outer_frame)
wafermap_preview_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

WAFERMAP_PREVIEW_SCALE = 45  # pixels per inch - larger preview, scales dynamically

wafermap_preview_canvas = tk.Canvas(
    wafermap_preview_canvas_frame,
    width=int(13.333 * WAFERMAP_PREVIEW_SCALE),
    height=int(7.5 * WAFERMAP_PREVIEW_SCALE),
    bg="white",
    relief="solid",
    bd=1
)
wafermap_preview_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

def on_wafermap_preview_resize(event=None):
    """Scale wafermap preview canvas when container resizes"""
    global WAFERMAP_PREVIEW_SCALE
    try:
        frame_w = wafermap_preview_canvas_frame.winfo_width()
        frame_h = wafermap_preview_canvas_frame.winfo_height()
        if frame_w > 100 and frame_h > 100:
            scale_w = (frame_w - 20) / 13.333
            scale_h = (frame_h - 20) / 7.5
            new_scale = min(scale_w, scale_h)
            if new_scale > 20 and abs(new_scale - WAFERMAP_PREVIEW_SCALE) > 3:
                WAFERMAP_PREVIEW_SCALE = new_scale
                wafermap_preview_canvas.config(
                    width=int(13.333 * WAFERMAP_PREVIEW_SCALE),
                    height=int(7.5 * WAFERMAP_PREVIEW_SCALE))
                draw_wafermap_preview()
    except: pass

wafermap_preview_canvas_frame.bind("<Configure>", on_wafermap_preview_resize)

# Slides Number option for Wafermap
wafermap_slides_frame = tk.Frame(wafermap_preview_outer_frame)
wafermap_slides_frame.pack(fill=tk.X, padx=5, pady=(5,0))

tk.Label(wafermap_slides_frame, text="Number of Slides:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
wafermap_slides_number_var = tk.IntVar(value=1)
wafermap_slides_spinbox = tk.Spinbox(wafermap_slides_frame, from_=1, to=4, textvariable=wafermap_slides_number_var,
                                      width=5, font=("Helvetica", 10))
wafermap_slides_spinbox.pack(side=tk.LEFT, padx=5)

# Checkbox frame for Wafermap
wafermap_box_enable_frame = tk.LabelFrame(wafermap_preview_outer_frame, text="Elements", font=("Helvetica", 9))
wafermap_box_enable_frame.pack(fill=tk.X, padx=5, pady=5)

wafermap_box_enable_vars = {}
for box_name, box_data in wafermap_layout_boxes.items():
    var = tk.BooleanVar(value=box_data["enabled"])
    wafermap_box_enable_vars[box_name] = var

def draw_wafermap_preview():
    """Draw the interactive preview for Wafermap tab"""
    wafermap_preview_canvas.delete("all")
    scale = WAFERMAP_PREVIEW_SCALE
    slide_w = int(13.333 * scale)
    slide_h = int(7.5 * scale)
    wafermap_preview_canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2)

    # Draw grid
    for i in range(1, 13):
        x = i * scale
        wafermap_preview_canvas.create_line(x, 0, x, slide_h, fill="#EEEEEE", dash=(2, 4))
    for i in range(1, 7):
        y = i * scale
        wafermap_preview_canvas.create_line(0, y, slide_w, y, fill="#EEEEEE", dash=(2, 4))

    for box_name, box_data in wafermap_layout_boxes.items():
        if not wafermap_box_enable_vars.get(box_name, tk.BooleanVar(value=True)).get():
            continue
        x = box_data["x"] * scale
        y = box_data["y"] * scale
        w = box_data["width"] * scale
        h = box_data["height"] * scale
        wafermap_preview_canvas.create_rectangle(x, y, x+w, y+h, fill=box_data["fill"], outline=box_data["color"], width=2, tags=(f"box_{box_name}", "box", "movable"))
        wafermap_preview_canvas.create_text(x+w/2, y+h/2, text=box_data["label"], font=("Helvetica", 8, "bold"), fill=box_data["color"], tags=(f"label_{box_name}",))
        # Resize handle
        handle_size = 16
        wafermap_preview_canvas.create_rectangle(x+w-handle_size, y+h-handle_size, x+w, y+h, fill=box_data["color"], outline="white", width=2, tags=(f"handle_{box_name}", "handle"))
        wafermap_preview_canvas.create_line(x+w-handle_size+4, y+h-4, x+w-4, y+h-handle_size+4, fill="white", width=2, tags=(f"handle_{box_name}",))
        # Dimensions
        wafermap_preview_canvas.create_text(x+w/2, y+h+10, text=f"{box_data['width']:.1f}\\" × {box_data['height']:.1f}\\"", font=("Helvetica", 6), fill="#888888")

def on_wafermap_preview_press(event):
    global wafermap_preview_drag_data
    handle_items = wafermap_preview_canvas.find_overlapping(event.x-10, event.y-10, event.x+10, event.y+10)
    for item in handle_items:
        tags = wafermap_preview_canvas.gettags(item)
        for tag in tags:
            if tag.startswith("handle_"):
                box_name = tag.replace("handle_", "")
                if box_name in wafermap_layout_boxes:
                    wafermap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": box_name}
                    wafermap_preview_canvas.config(cursor="bottom_right_corner")
                    return
    items = wafermap_preview_canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
    for item in items:
        tags = wafermap_preview_canvas.gettags(item)
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_") and not tag.startswith("box_name"):
                    box_name = tag.replace("box_", "")
                    if box_name in wafermap_layout_boxes:
                        wafermap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": box_name}
                        wafermap_preview_canvas.config(cursor="fleur")
                        return

def on_wafermap_preview_drag(event):
    global wafermap_preview_drag_data
    if wafermap_preview_drag_data["box_name"] is None:
        return
    box_name = wafermap_preview_drag_data["box_name"]
    dx = event.x - wafermap_preview_drag_data["x"]
    dy = event.y - wafermap_preview_drag_data["y"]
    dx_inches = dx / WAFERMAP_PREVIEW_SCALE
    dy_inches = dy / WAFERMAP_PREVIEW_SCALE
    if wafermap_preview_drag_data["mode"] == "move":
        new_x = max(0, min(13.333 - wafermap_layout_boxes[box_name]["width"], wafermap_layout_boxes[box_name]["x"] + dx_inches))
        new_y = max(0, min(7.5 - wafermap_layout_boxes[box_name]["height"], wafermap_layout_boxes[box_name]["y"] + dy_inches))
        wafermap_layout_boxes[box_name]["x"] = round(new_x, 2)
        wafermap_layout_boxes[box_name]["y"] = round(new_y, 2)
    elif wafermap_preview_drag_data["mode"] == "resize":
        new_w = max(0.5, min(13.333 - wafermap_layout_boxes[box_name]["x"], wafermap_layout_boxes[box_name]["width"] + dx_inches))
        new_h = max(0.3, min(7.5 - wafermap_layout_boxes[box_name]["y"], wafermap_layout_boxes[box_name]["height"] + dy_inches))
        wafermap_layout_boxes[box_name]["width"] = round(new_w, 2)
        wafermap_layout_boxes[box_name]["height"] = round(new_h, 2)
    wafermap_preview_drag_data["x"] = event.x
    wafermap_preview_drag_data["y"] = event.y
    draw_wafermap_preview()

def on_wafermap_preview_release(event):
    global wafermap_preview_drag_data
    wafermap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None}
    wafermap_preview_canvas.config(cursor="")

wafermap_preview_canvas.bind("<ButtonPress-1>", on_wafermap_preview_press)
wafermap_preview_canvas.bind("<B1-Motion>", on_wafermap_preview_drag)
wafermap_preview_canvas.bind("<ButtonRelease-1>", on_wafermap_preview_release)

# Create checkboxes for wafermap preview
for box_name, box_data in wafermap_layout_boxes.items():
    cb = tk.Checkbutton(
        wafermap_box_enable_frame,
        text=box_data["label"],
        variable=wafermap_box_enable_vars[box_name],
        font=("Helvetica", 8),
        fg=box_data["color"],
        command=draw_wafermap_preview
    )
    cb.pack(side=tk.LEFT, padx=3)

# Presets for Wafermap
wafermap_preset_frame = tk.Frame(wafermap_preview_outer_frame)
wafermap_preset_frame.pack(fill=tk.X, padx=5, pady=5)

def apply_wafermap_preset(preset):
    presets = {
        "Standard": {"title": (0.3, 0.15, 12.733, 0.5), "wafermap": (0.3, 0.7, 6.0, 6.0), "boxplot": (6.5, 0.7, 6.5, 3.0), "histogram": (6.5, 3.8, 6.5, 2.9), "stats": (0.3, 6.8, 12.733, 0.5)},
        "Full": {"title": (0.3, 0.15, 12.733, 0.5), "wafermap": (0.3, 0.7, 12.7, 6.5), "boxplot": (0.3, 0.7, 12.7, 6.5), "histogram": (0.3, 0.7, 12.7, 6.5), "stats": (0.3, 6.8, 12.733, 0.5)},
    }
    if preset in presets:
        for box_name, vals in presets[preset].items():
            if box_name in wafermap_layout_boxes:
                wafermap_layout_boxes[box_name]["x"], wafermap_layout_boxes[box_name]["y"] = vals[0], vals[1]
                wafermap_layout_boxes[box_name]["width"], wafermap_layout_boxes[box_name]["height"] = vals[2], vals[3]
        draw_wafermap_preview()

tk.Label(wafermap_preset_frame, text="Presets:", font=("Helvetica", 8, "bold")).pack(side=tk.LEFT, padx=2)
for preset in ["Standard", "Full"]:
    tk.Button(wafermap_preset_frame, text=preset, font=("Helvetica", 7), command=lambda p=preset: apply_wafermap_preset(p)).pack(side=tk.LEFT, padx=2)

# Info label for Wafermap
tk.Label(wafermap_preview_outer_frame, text="💡 Ziehen = Verschieben, Ecke = Größe ändern", font=("Helvetica", 7), fg="#666666").pack(pady=2)

# Initial draw
draw_wafermap_preview()'''

new_wafermap = '''# RIGHT SIDE: Interactive Layout Preview for Wafermap with Slide Tabs
wafermap_preview_outer_frame = tk.LabelFrame(wafermap_split_frame, text="📐 Slide Layout Preview (Drag & Resize)", font=("Helvetica", 10, "bold"))
wafermap_split_frame.add(wafermap_preview_outer_frame, minsize=350, width=500)

WAFERMAP_PREVIEW_SCALE = 45  # pixels per inch

# Layout boxes template for Wafermap tab
wafermap_layout_boxes_template = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "wafermap": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 6.0, "color": "#4CAF50", "fill": "#E8F5E9", "enabled": True, "label": "Wafermap"},
    "boxplot": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#FF9800", "fill": "#FFF3E0", "enabled": True, "label": "Boxplot"},
    "histogram": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 2.9, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Histogram"},
    "stats_table": {"x": 0.3, "y": 3.8, "width": 6.0, "height": 2.9, "color": "#009688", "fill": "#E0F2F1", "enabled": False, "label": "Statistics Table"},
    "summary": {"x": 0.3, "y": 6.8, "width": 12.733, "height": 0.5, "color": "#607D8B", "fill": "#ECEFF1", "enabled": False, "label": "Summary"},
}

# Storage for multiple slides - Wafermap
wafermap_layout_boxes = {}  # {1: {...}, 2: {...}, ...}
wafermap_box_enable_vars = {}  # {1: {...}, 2: {...}, ...}
wm_slide_canvases = {}
wm_slide_frames = {}
wafermap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": 1}

# Number of slides selection for Wafermap
wm_slides_control_frame = tk.Frame(wafermap_preview_outer_frame)
wm_slides_control_frame.pack(fill=tk.X, padx=5, pady=5)

tk.Label(wm_slides_control_frame, text="Number of Slides per Parameter:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
wafermap_slides_number_var = tk.IntVar(value=1)

# Notebook for slide tabs - Wafermap
wm_slides_notebook = ttk.Notebook(wafermap_preview_outer_frame)
wm_slides_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

def create_wm_slide_tab(slide_num):
    """Create a slide tab with canvas and checkboxes for Wafermap"""
    import copy

    slide_frame = tk.Frame(wm_slides_notebook)
    wm_slides_notebook.add(slide_frame, text=f"Slide {slide_num}")
    wm_slide_frames[slide_num] = slide_frame

    wafermap_layout_boxes[slide_num] = copy.deepcopy(wafermap_layout_boxes_template)
    wafermap_box_enable_vars[slide_num] = {}

    canvas_frame = tk.Frame(slide_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    canvas = tk.Canvas(canvas_frame, width=int(13.333 * WAFERMAP_PREVIEW_SCALE),
                       height=int(7.5 * WAFERMAP_PREVIEW_SCALE), bg="white", relief="solid", bd=1)
    canvas.pack(fill=tk.BOTH, expand=True)
    wm_slide_canvases[slide_num] = canvas

    cb_frame = tk.LabelFrame(slide_frame, text="Elements (check to include)", font=("Helvetica", 9))
    cb_frame.pack(fill=tk.X, padx=5, pady=5)

    for box_name, box_data in wafermap_layout_boxes[slide_num].items():
        var = tk.BooleanVar(value=box_data["enabled"])
        wafermap_box_enable_vars[slide_num][box_name] = var
        cb = tk.Checkbutton(cb_frame, text=box_data["label"], variable=var, font=("Helvetica", 8),
                           fg=box_data["color"], command=lambda sn=slide_num: draw_wm_slide_preview(sn))
        cb.pack(side=tk.LEFT, padx=3)

    canvas.bind("<ButtonPress-1>", lambda e, sn=slide_num: on_wm_preview_press(e, sn))
    canvas.bind("<B1-Motion>", lambda e, sn=slide_num: on_wm_preview_drag(e, sn))
    canvas.bind("<ButtonRelease-1>", lambda e, sn=slide_num: on_wm_preview_release(e, sn))

    draw_wm_slide_preview(slide_num)

def update_wm_slide_tabs():
    """Update slide tabs based on selected number for Wafermap"""
    num_slides = wafermap_slides_number_var.get()
    current_tabs = len(wm_slides_notebook.tabs())

    while current_tabs > num_slides:
        last_tab = current_tabs - 1
        if last_tab + 1 in wm_slide_frames:
            wm_slides_notebook.forget(last_tab)
            del wm_slide_frames[last_tab + 1]
            del wm_slide_canvases[last_tab + 1]
            del wafermap_layout_boxes[last_tab + 1]
            del wafermap_box_enable_vars[last_tab + 1]
        current_tabs -= 1

    while current_tabs < num_slides:
        create_wm_slide_tab(current_tabs + 1)
        current_tabs += 1

def draw_wm_slide_preview(slide_num):
    """Draw preview for a specific Wafermap slide"""
    if slide_num not in wm_slide_canvases:
        return

    canvas = wm_slide_canvases[slide_num]
    canvas.delete("all")

    scale = WAFERMAP_PREVIEW_SCALE
    slide_w = int(13.333 * scale)
    slide_h = int(7.5 * scale)

    canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2)

    for i in range(1, 13):
        x = i * scale
        canvas.create_line(x, 0, x, slide_h, fill="#EEEEEE", dash=(2, 4))
    for i in range(1, 7):
        y = i * scale
        canvas.create_line(0, y, slide_w, y, fill="#EEEEEE", dash=(2, 4))

    for box_name, box_data in wafermap_layout_boxes[slide_num].items():
        if not wafermap_box_enable_vars[slide_num].get(box_name, tk.BooleanVar(value=True)).get():
            continue

        x = box_data["x"] * scale
        y = box_data["y"] * scale
        w = box_data["width"] * scale
        h = box_data["height"] * scale

        canvas.create_rectangle(x, y, x+w, y+h, fill=box_data["fill"], outline=box_data["color"], width=2,
                               tags=(f"box_{box_name}", "box", "movable"))
        canvas.create_text(x+w/2, y+h/2, text=box_data["label"], font=("Helvetica", 8, "bold"), fill=box_data["color"])
        canvas.create_rectangle(x+w-12, y+h-12, x+w, y+h, fill=box_data["color"], outline="white",
                               tags=(f"handle_{box_name}", "handle"))

def on_wm_preview_press(event, slide_num):
    global wafermap_preview_drag_data
    canvas = wm_slide_canvases[slide_num]

    items = canvas.find_overlapping(event.x-8, event.y-8, event.x+8, event.y+8)
    for item in items:
        tags = canvas.gettags(item)
        for tag in tags:
            if tag.startswith("handle_"):
                box_name = tag.replace("handle_", "")
                wafermap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": box_name, "slide_num": slide_num}
                return

    for item in items:
        tags = canvas.gettags(item)
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_"):
                    box_name = tag.replace("box_", "")
                    wafermap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": box_name, "slide_num": slide_num}
                    return

def on_wm_preview_drag(event, slide_num):
    global wafermap_preview_drag_data
    if wafermap_preview_drag_data["box_name"] is None or wafermap_preview_drag_data["slide_num"] != slide_num:
        return

    box_name = wafermap_preview_drag_data["box_name"]
    dx = (event.x - wafermap_preview_drag_data["x"]) / WAFERMAP_PREVIEW_SCALE
    dy = (event.y - wafermap_preview_drag_data["y"]) / WAFERMAP_PREVIEW_SCALE

    if wafermap_preview_drag_data["mode"] == "move":
        wafermap_layout_boxes[slide_num][box_name]["x"] = max(0, wafermap_layout_boxes[slide_num][box_name]["x"] + dx)
        wafermap_layout_boxes[slide_num][box_name]["y"] = max(0, wafermap_layout_boxes[slide_num][box_name]["y"] + dy)
    elif wafermap_preview_drag_data["mode"] == "resize":
        wafermap_layout_boxes[slide_num][box_name]["width"] = max(1, wafermap_layout_boxes[slide_num][box_name]["width"] + dx)
        wafermap_layout_boxes[slide_num][box_name]["height"] = max(0.5, wafermap_layout_boxes[slide_num][box_name]["height"] + dy)

    wafermap_preview_drag_data["x"] = event.x
    wafermap_preview_drag_data["y"] = event.y
    draw_wm_slide_preview(slide_num)

def on_wm_preview_release(event, slide_num):
    global wafermap_preview_drag_data
    wafermap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": slide_num}

# Initialize first Wafermap slide tab
create_wm_slide_tab(1)

# Setup spinbox command for Wafermap
def on_wm_slides_spinbox_change():
    update_wm_slide_tabs()

wafermap_slides_spinbox = tk.Spinbox(wm_slides_control_frame, from_=1, to=4, textvariable=wafermap_slides_number_var,
                                      width=3, font=("Helvetica", 10), command=on_wm_slides_spinbox_change)
wafermap_slides_spinbox.pack(side=tk.LEFT, padx=5)

# For backward compatibility
def draw_wafermap_preview():
    draw_wm_slide_preview(1)

# Info label for Wafermap
tk.Label(wafermap_preview_outer_frame, text="💡 Drag boxes to move, corner to resize | Slide: 13.333\" × 7.5\"", font=("Helvetica", 8), fg="#666666").pack(pady=2)'''

if old_wafermap in content:
    content = content.replace(old_wafermap, new_wafermap)
    print("✓ Wafermap Tab updated with Slide Tabs")
else:
    print("✗ Could not find Wafermap Tab code to replace")

# ============================================================================
# DIFFMAP TAB - Replace old single canvas with Slide Tabs system
# ============================================================================

# Find and read the diffmap section
old_diffmap_start = '''# RIGHT SIDE: Interactive Layout Preview for Diffmap
diffmap_preview_outer_frame = tk.LabelFrame(diffmap_split_frame, text="📐 Slide Layout Preview", font=("Helvetica", 10, "bold"))
diffmap_split_frame.add(diffmap_preview_outer_frame, minsize=300, width=400)

# Layout boxes configuration for Diffmap
diffmap_layout_boxes = {'''

old_diffmap_end = '''tk.Label(diffmap_preview_outer_frame, text="💡 Ziehen = Verschieben, Ecke = Größe ändern", font=("Helvetica", 7), fg="#666666").pack(pady=2)

# Initial draw
draw_diffmap_preview()'''

# Find diffmap section boundaries
diffmap_start_idx = content.find(old_diffmap_start)
diffmap_end_marker = 'tk.Label(diffmap_preview_outer_frame, text="💡 Ziehen = Verschieben'
diffmap_end_idx = content.find(diffmap_end_marker)
if diffmap_end_idx != -1:
    # Find end of this line
    diffmap_end_idx = content.find('\n', diffmap_end_idx + len(diffmap_end_marker) + 50) + 1
    # Skip "# Initial draw" and "draw_diffmap_preview()"
    next_line = content.find('\n', diffmap_end_idx)
    if 'Initial draw' in content[diffmap_end_idx:diffmap_end_idx+50]:
        diffmap_end_idx = content.find('\n', next_line + 1) + 1
        next_line2 = content.find('\n', diffmap_end_idx)
        if 'draw_diffmap_preview()' in content[diffmap_end_idx:diffmap_end_idx+50]:
            diffmap_end_idx = next_line2 + 1

new_diffmap = '''# RIGHT SIDE: Interactive Layout Preview for Diffmap with Slide Tabs
diffmap_preview_outer_frame = tk.LabelFrame(diffmap_split_frame, text="📐 Slide Layout Preview (Drag & Resize)", font=("Helvetica", 10, "bold"))
diffmap_split_frame.add(diffmap_preview_outer_frame, minsize=350, width=500)

DIFFMAP_PREVIEW_SCALE = 45  # pixels per inch

# Layout boxes template for Diffmap tab
diffmap_layout_boxes_template = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "diffmap": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 6.0, "color": "#4CAF50", "fill": "#E8F5E9", "enabled": True, "label": "Diffmap"},
    "boxplot": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#FF9800", "fill": "#FFF3E0", "enabled": True, "label": "Boxplot"},
    "histogram": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 2.9, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Histogram"},
    "stats_table": {"x": 0.3, "y": 3.8, "width": 6.0, "height": 2.9, "color": "#009688", "fill": "#E0F2F1", "enabled": False, "label": "Statistics Table"},
    "summary": {"x": 0.3, "y": 6.8, "width": 12.733, "height": 0.5, "color": "#607D8B", "fill": "#ECEFF1", "enabled": False, "label": "Summary"},
}

# Storage for multiple slides - Diffmap
diffmap_layout_boxes = {}  # {1: {...}, 2: {...}, ...}
diffmap_box_enable_vars = {}  # {1: {...}, 2: {...}, ...}
dm_slide_canvases = {}
dm_slide_frames = {}
diffmap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": 1}

# Number of slides selection for Diffmap
dm_slides_control_frame = tk.Frame(diffmap_preview_outer_frame)
dm_slides_control_frame.pack(fill=tk.X, padx=5, pady=5)

tk.Label(dm_slides_control_frame, text="Number of Slides per Parameter:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
diffmap_slides_number_var = tk.IntVar(value=1)

# Notebook for slide tabs - Diffmap
dm_slides_notebook = ttk.Notebook(diffmap_preview_outer_frame)
dm_slides_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

def create_dm_slide_tab(slide_num):
    """Create a slide tab with canvas and checkboxes for Diffmap"""
    import copy

    slide_frame = tk.Frame(dm_slides_notebook)
    dm_slides_notebook.add(slide_frame, text=f"Slide {slide_num}")
    dm_slide_frames[slide_num] = slide_frame

    diffmap_layout_boxes[slide_num] = copy.deepcopy(diffmap_layout_boxes_template)
    diffmap_box_enable_vars[slide_num] = {}

    canvas_frame = tk.Frame(slide_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    canvas = tk.Canvas(canvas_frame, width=int(13.333 * DIFFMAP_PREVIEW_SCALE),
                       height=int(7.5 * DIFFMAP_PREVIEW_SCALE), bg="white", relief="solid", bd=1)
    canvas.pack(fill=tk.BOTH, expand=True)
    dm_slide_canvases[slide_num] = canvas

    cb_frame = tk.LabelFrame(slide_frame, text="Elements (check to include)", font=("Helvetica", 9))
    cb_frame.pack(fill=tk.X, padx=5, pady=5)

    for box_name, box_data in diffmap_layout_boxes[slide_num].items():
        var = tk.BooleanVar(value=box_data["enabled"])
        diffmap_box_enable_vars[slide_num][box_name] = var
        cb = tk.Checkbutton(cb_frame, text=box_data["label"], variable=var, font=("Helvetica", 8),
                           fg=box_data["color"], command=lambda sn=slide_num: draw_dm_slide_preview(sn))
        cb.pack(side=tk.LEFT, padx=3)

    canvas.bind("<ButtonPress-1>", lambda e, sn=slide_num: on_dm_preview_press(e, sn))
    canvas.bind("<B1-Motion>", lambda e, sn=slide_num: on_dm_preview_drag(e, sn))
    canvas.bind("<ButtonRelease-1>", lambda e, sn=slide_num: on_dm_preview_release(e, sn))

    draw_dm_slide_preview(slide_num)

def update_dm_slide_tabs():
    """Update slide tabs based on selected number for Diffmap"""
    num_slides = diffmap_slides_number_var.get()
    current_tabs = len(dm_slides_notebook.tabs())

    while current_tabs > num_slides:
        last_tab = current_tabs - 1
        if last_tab + 1 in dm_slide_frames:
            dm_slides_notebook.forget(last_tab)
            del dm_slide_frames[last_tab + 1]
            del dm_slide_canvases[last_tab + 1]
            del diffmap_layout_boxes[last_tab + 1]
            del diffmap_box_enable_vars[last_tab + 1]
        current_tabs -= 1

    while current_tabs < num_slides:
        create_dm_slide_tab(current_tabs + 1)
        current_tabs += 1

def draw_dm_slide_preview(slide_num):
    """Draw preview for a specific Diffmap slide"""
    if slide_num not in dm_slide_canvases:
        return

    canvas = dm_slide_canvases[slide_num]
    canvas.delete("all")

    scale = DIFFMAP_PREVIEW_SCALE
    slide_w = int(13.333 * scale)
    slide_h = int(7.5 * scale)

    canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2)

    for i in range(1, 13):
        x = i * scale
        canvas.create_line(x, 0, x, slide_h, fill="#EEEEEE", dash=(2, 4))
    for i in range(1, 7):
        y = i * scale
        canvas.create_line(0, y, slide_w, y, fill="#EEEEEE", dash=(2, 4))

    for box_name, box_data in diffmap_layout_boxes[slide_num].items():
        if not diffmap_box_enable_vars[slide_num].get(box_name, tk.BooleanVar(value=True)).get():
            continue

        x = box_data["x"] * scale
        y = box_data["y"] * scale
        w = box_data["width"] * scale
        h = box_data["height"] * scale

        canvas.create_rectangle(x, y, x+w, y+h, fill=box_data["fill"], outline=box_data["color"], width=2,
                               tags=(f"box_{box_name}", "box", "movable"))
        canvas.create_text(x+w/2, y+h/2, text=box_data["label"], font=("Helvetica", 8, "bold"), fill=box_data["color"])
        canvas.create_rectangle(x+w-12, y+h-12, x+w, y+h, fill=box_data["color"], outline="white",
                               tags=(f"handle_{box_name}", "handle"))

def on_dm_preview_press(event, slide_num):
    global diffmap_preview_drag_data
    canvas = dm_slide_canvases[slide_num]

    items = canvas.find_overlapping(event.x-8, event.y-8, event.x+8, event.y+8)
    for item in items:
        tags = canvas.gettags(item)
        for tag in tags:
            if tag.startswith("handle_"):
                box_name = tag.replace("handle_", "")
                diffmap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": box_name, "slide_num": slide_num}
                return

    for item in items:
        tags = canvas.gettags(item)
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_"):
                    box_name = tag.replace("box_", "")
                    diffmap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": box_name, "slide_num": slide_num}
                    return

def on_dm_preview_drag(event, slide_num):
    global diffmap_preview_drag_data
    if diffmap_preview_drag_data["box_name"] is None or diffmap_preview_drag_data["slide_num"] != slide_num:
        return

    box_name = diffmap_preview_drag_data["box_name"]
    dx = (event.x - diffmap_preview_drag_data["x"]) / DIFFMAP_PREVIEW_SCALE
    dy = (event.y - diffmap_preview_drag_data["y"]) / DIFFMAP_PREVIEW_SCALE

    if diffmap_preview_drag_data["mode"] == "move":
        diffmap_layout_boxes[slide_num][box_name]["x"] = max(0, diffmap_layout_boxes[slide_num][box_name]["x"] + dx)
        diffmap_layout_boxes[slide_num][box_name]["y"] = max(0, diffmap_layout_boxes[slide_num][box_name]["y"] + dy)
    elif diffmap_preview_drag_data["mode"] == "resize":
        diffmap_layout_boxes[slide_num][box_name]["width"] = max(1, diffmap_layout_boxes[slide_num][box_name]["width"] + dx)
        diffmap_layout_boxes[slide_num][box_name]["height"] = max(0.5, diffmap_layout_boxes[slide_num][box_name]["height"] + dy)

    diffmap_preview_drag_data["x"] = event.x
    diffmap_preview_drag_data["y"] = event.y
    draw_dm_slide_preview(slide_num)

def on_dm_preview_release(event, slide_num):
    global diffmap_preview_drag_data
    diffmap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": slide_num}

# Initialize first Diffmap slide tab
create_dm_slide_tab(1)

# Setup spinbox command for Diffmap
def on_dm_slides_spinbox_change():
    update_dm_slide_tabs()

diffmap_slides_spinbox = tk.Spinbox(dm_slides_control_frame, from_=1, to=4, textvariable=diffmap_slides_number_var,
                                     width=3, font=("Helvetica", 10), command=on_dm_slides_spinbox_change)
diffmap_slides_spinbox.pack(side=tk.LEFT, padx=5)

# For backward compatibility
def draw_diffmap_preview():
    draw_dm_slide_preview(1)

# Info label for Diffmap
tk.Label(diffmap_preview_outer_frame, text="💡 Drag boxes to move, corner to resize | Slide: 13.333\" × 7.5\"", font=("Helvetica", 8), fg="#666666").pack(pady=2)

'''

if diffmap_start_idx != -1 and diffmap_end_idx != -1:
    old_diffmap_content = content[diffmap_start_idx:diffmap_end_idx]
    content = content[:diffmap_start_idx] + new_diffmap + content[diffmap_end_idx:]
    print("✓ Diffmap Tab updated with Slide Tabs")
else:
    print(f"✗ Could not find Diffmap Tab code to replace (start: {diffmap_start_idx}, end: {diffmap_end_idx})")

# ============================================================================
# GRR TAB - Replace old single canvas with Slide Tabs system
# ============================================================================

grr_start_marker = '''# RIGHT SIDE: Interactive Layout Preview for GRR
grr_preview_outer_frame = tk.LabelFrame(grr_split_frame, text="📐 Slide Layout Preview", font=("Helvetica", 10, "bold"))
grr_split_frame.add(grr_preview_outer_frame, minsize=300, width=400)

# Layout boxes configuration for GRR'''

grr_end_marker = 'tk.Label(grr_preview_outer_frame, text="💡 Ziehen = Verschieben'

grr_start_idx = content.find(grr_start_marker)
grr_end_idx = content.find(grr_end_marker)
if grr_end_idx != -1:
    # Find end of this section
    grr_end_idx = content.find('\n', grr_end_idx + len(grr_end_marker) + 50) + 1
    next_line = content.find('\n', grr_end_idx)
    if 'Initial draw' in content[grr_end_idx:grr_end_idx+50]:
        grr_end_idx = content.find('\n', next_line + 1) + 1
        next_line2 = content.find('\n', grr_end_idx)
        if 'draw_grr_preview()' in content[grr_end_idx:grr_end_idx+50]:
            grr_end_idx = next_line2 + 1

new_grr = '''# RIGHT SIDE: Interactive Layout Preview for GRR with Slide Tabs
grr_preview_outer_frame = tk.LabelFrame(grr_split_frame, text="📐 Slide Layout Preview (Drag & Resize)", font=("Helvetica", 10, "bold"))
grr_split_frame.add(grr_preview_outer_frame, minsize=350, width=500)

GRR_PREVIEW_SCALE = 45  # pixels per inch

# Layout boxes template for GRR tab
grr_layout_boxes_template = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "grr_summary": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 3.0, "color": "#4CAF50", "fill": "#E8F5E9", "enabled": True, "label": "GRR Summary"},
    "variance": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#FF9800", "fill": "#FFF3E0", "enabled": True, "label": "Variance Chart"},
    "charts": {"x": 0.3, "y": 3.8, "width": 6.0, "height": 3.0, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Range/Mean Charts"},
    "anova": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 3.0, "color": "#009688", "fill": "#E0F2F1", "enabled": True, "label": "ANOVA Table"},
    "stats_table": {"x": 0.3,
