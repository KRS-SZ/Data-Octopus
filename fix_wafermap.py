#!/usr/bin/env python3
"""Add Slide Tabs system to Wafermap Report Tab"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the Wafermap section start
wafermap_start = '''# RIGHT SIDE: Interactive Layout Preview for Wafermap
wafermap_preview_outer_frame = tk.LabelFrame(wafermap_split_frame, text="📐 Slide Layout Preview", font=("Helvetica", 10, "bold"))'''

# Find the end marker
wafermap_end = '''# Initial draw
draw_wafermap_preview()

# Select All checkbox for Wafermap'''

start_idx = content.find(wafermap_start)
end_idx = content.find(wafermap_end)

if start_idx == -1:
    print("Could not find Wafermap start marker")
    exit(1)
if end_idx == -1:
    print("Could not find Wafermap end marker")
    exit(1)

new_wafermap = '''# RIGHT SIDE: Interactive Layout Preview for Wafermap with Slide Tabs
wafermap_preview_outer_frame = tk.LabelFrame(wafermap_split_frame, text="Slide Layout Preview (Drag & Resize)", font=("Helvetica", 10, "bold"))
wafermap_split_frame.add(wafermap_preview_outer_frame, minsize=350, width=500)

WAFERMAP_PREVIEW_SCALE = 45

# Layout boxes template for Wafermap
wafermap_layout_boxes_template = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "wafermap": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 6.0, "color": "#4CAF50", "fill": "#E8F5E9", "enabled": True, "label": "Wafermap"},
    "boxplot": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#FF9800", "fill": "#FFF3E0", "enabled": True, "label": "Boxplot"},
    "histogram": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 2.9, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Histogram"},
    "stats_table": {"x": 0.3, "y": 3.8, "width": 6.0, "height": 2.9, "color": "#009688", "fill": "#E0F2F1", "enabled": False, "label": "Statistics Table"},
    "summary": {"x": 0.3, "y": 6.8, "width": 12.733, "height": 0.5, "color": "#607D8B", "fill": "#ECEFF1", "enabled": False, "label": "Summary"},
}

wafermap_layout_boxes = {}
wafermap_box_enable_vars = {}
wm_slide_canvases = {}
wm_slide_frames = {}
wafermap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": 1}

wm_slides_control_frame = tk.Frame(wafermap_preview_outer_frame)
wm_slides_control_frame.pack(fill=tk.X, padx=5, pady=5)
tk.Label(wm_slides_control_frame, text="Number of Slides per Parameter:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
wafermap_slides_number_var = tk.IntVar(value=1)

wm_slides_notebook = ttk.Notebook(wafermap_preview_outer_frame)
wm_slides_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

def create_wm_slide_tab(slide_num):
    import copy
    slide_frame = tk.Frame(wm_slides_notebook)
    wm_slides_notebook.add(slide_frame, text=f"Slide {slide_num}")
    wm_slide_frames[slide_num] = slide_frame
    wafermap_layout_boxes[slide_num] = copy.deepcopy(wafermap_layout_boxes_template)
    wafermap_box_enable_vars[slide_num] = {}

    canvas_frame = tk.Frame(slide_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    canvas = tk.Canvas(canvas_frame, width=int(13.333*WAFERMAP_PREVIEW_SCALE), height=int(7.5*WAFERMAP_PREVIEW_SCALE), bg="white", relief="solid", bd=1)
    canvas.pack(fill=tk.BOTH, expand=True)
    wm_slide_canvases[slide_num] = canvas

    cb_frame = tk.LabelFrame(slide_frame, text="Elements (check to include)", font=("Helvetica", 9))
    cb_frame.pack(fill=tk.X, padx=5, pady=5)
    for box_name, box_data in wafermap_layout_boxes[slide_num].items():
        var = tk.BooleanVar(value=box_data["enabled"])
        wafermap_box_enable_vars[slide_num][box_name] = var
        cb = tk.Checkbutton(cb_frame, text=box_data["label"], variable=var, font=("Helvetica", 8), fg=box_data["color"], command=lambda sn=slide_num: draw_wm_slide_preview(sn))
        cb.pack(side=tk.LEFT, padx=3)

    canvas.bind("<ButtonPress-1>", lambda e, sn=slide_num: on_wm_preview_press(e, sn))
    canvas.bind("<B1-Motion>", lambda e, sn=slide_num: on_wm_preview_drag(e, sn))
    canvas.bind("<ButtonRelease-1>", lambda e, sn=slide_num: on_wm_preview_release(e, sn))
    draw_wm_slide_preview(slide_num)

def update_wm_slide_tabs():
    num_slides = wafermap_slides_number_var.get()
    current_tabs = len(wm_slides_notebook.tabs())
    while current_tabs > num_slides:
        if current_tabs in wm_slide_frames:
            wm_slides_notebook.forget(current_tabs - 1)
            del wm_slide_frames[current_tabs]
            del wm_slide_canvases[current_tabs]
            del wafermap_layout_boxes[current_tabs]
            del wafermap_box_enable_vars[current_tabs]
        current_tabs -= 1
    while current_tabs < num_slides:
        create_wm_slide_tab(current_tabs + 1)
        current_tabs += 1

def draw_wm_slide_preview(slide_num):
    if slide_num not in wm_slide_canvases: return
    canvas = wm_slide_canvases[slide_num]
    canvas.delete("all")
    scale = WAFERMAP_PREVIEW_SCALE
    slide_w, slide_h = int(13.333*scale), int(7.5*scale)
    canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2)
    for i in range(1, 13): canvas.create_line(i*scale, 0, i*scale, slide_h, fill="#EEEEEE", dash=(2,4))
    for i in range(1, 7): canvas.create_line(0, i*scale, slide_w, i*scale, fill="#EEEEEE", dash=(2,4))
    for box_name, box_data in wafermap_layout_boxes[slide_num].items():
        if not wafermap_box_enable_vars[slide_num].get(box_name, tk.BooleanVar(value=True)).get(): continue
        x, y = box_data["x"]*scale, box_data["y"]*scale
        w, h = box_data["width"]*scale, box_data["height"]*scale
        canvas.create_rectangle(x, y, x+w, y+h, fill=box_data["fill"], outline=box_data["color"], width=2, tags=(f"box_{box_name}", "box", "movable"))
        canvas.create_text(x+w/2, y+h/2, text=box_data["label"], font=("Helvetica", 8, "bold"), fill=box_data["color"])
        canvas.create_rectangle(x+w-12, y+h-12, x+w, y+h, fill=box_data["color"], outline="white", tags=(f"handle_{box_name}", "handle"))

def on_wm_preview_press(event, slide_num):
    global wafermap_preview_drag_data
    canvas = wm_slide_canvases[slide_num]
    items = canvas.find_overlapping(event.x-8, event.y-8, event.x+8, event.y+8)
    for item in items:
        for tag in canvas.gettags(item):
            if tag.startswith("handle_"):
                wafermap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": tag.replace("handle_", ""), "slide_num": slide_num}
                return
    for item in items:
        tags = canvas.gettags(item)
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_"):
                    wafermap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": tag.replace("box_", ""), "slide_num": slide_num}
                    return

def on_wm_preview_drag(event, slide_num):
    global wafermap_preview_drag_data
    if wafermap_preview_drag_data["box_name"] is None or wafermap_preview_drag_data["slide_num"] != slide_num: return
    box_name = wafermap_preview_drag_data["box_name"]
    dx, dy = (event.x - wafermap_preview_drag_data["x"]) / WAFERMAP_PREVIEW_SCALE, (event.y - wafermap_preview_drag_data["y"]) / WAFERMAP_PREVIEW_SCALE
    if wafermap_preview_drag_data["mode"] == "move":
        wafermap_layout_boxes[slide_num][box_name]["x"] = max(0, wafermap_layout_boxes[slide_num][box_name]["x"] + dx)
        wafermap_layout_boxes[slide_num][box_name]["y"] = max(0, wafermap_layout_boxes[slide_num][box_name]["y"] + dy)
    elif wafermap_preview_drag_data["mode"] == "resize":
        wafermap_layout_boxes[slide_num][box_name]["width"] = max(1, wafermap_layout_boxes[slide_num][box_name]["width"] + dx)
        wafermap_layout_boxes[slide_num][box_name]["height"] = max(0.5, wafermap_layout_boxes[slide_num][box_name]["height"] + dy)
    wafermap_preview_drag_data["x"], wafermap_preview_drag_data["y"] = event.x, event.y
    draw_wm_slide_preview(slide_num)

def on_wm_preview_release(event, slide_num):
    global wafermap_preview_drag_data
    wafermap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": slide_num}

create_wm_slide_tab(1)

def on_wm_slides_spinbox_change(): update_wm_slide_tabs()
wafermap_slides_spinbox = tk.Spinbox(wm_slides_control_frame, from_=1, to=4, textvariable=wafermap_slides_number_var, width=3, font=("Helvetica", 10), command=on_wm_slides_spinbox_change)
wafermap_slides_spinbox.pack(side=tk.LEFT, padx=5)

def draw_wafermap_preview(): draw_wm_slide_preview(1)
tk.Label(wafermap_preview_outer_frame, text="Drag boxes to move, corner to resize | Slide: 13.333 x 7.5 inches", font=("Helvetica", 8), fg="#666666").pack(pady=2)

'''

content = content[:start_idx] + new_wafermap + content[end_idx:]
print("Wafermap Tab updated with Slide Tabs")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
