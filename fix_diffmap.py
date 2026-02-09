#!/usr/bin/env python3
"""Add Slide Tabs system to Diffmap Report Tab"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the Diffmap section
diffmap_start = '''# RIGHT SIDE: Interactive Layout Preview for Diffmap
diffmap_preview_outer_frame = tk.LabelFrame(diffmap_split_frame, text="📐 Slide Layout Preview", font=("Helvetica", 10, "bold"))'''

diffmap_end = '''# Initial draw
draw_diffmap_preview()

# Select All checkbox for Diffmap'''

start_idx = content.find(diffmap_start)
end_idx = content.find(diffmap_end)

if start_idx == -1:
    print("Could not find Diffmap start marker")
    exit(1)
if end_idx == -1:
    print("Could not find Diffmap end marker")
    exit(1)

new_diffmap = '''# RIGHT SIDE: Interactive Layout Preview for Diffmap with Slide Tabs
diffmap_preview_outer_frame = tk.LabelFrame(diffmap_split_frame, text="Slide Layout Preview (Drag & Resize)", font=("Helvetica", 10, "bold"))
diffmap_split_frame.add(diffmap_preview_outer_frame, minsize=350, width=500)

DIFFMAP_PREVIEW_SCALE = 45

# Layout boxes template for Diffmap
diffmap_layout_boxes_template = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "diffmap": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 6.0, "color": "#FF5722", "fill": "#FBE9E7", "enabled": True, "label": "Diffmap"},
    "histogram": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Histogram"},
    "reference": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 2.9, "color": "#2196F3", "fill": "#E3F2FD", "enabled": True, "label": "Reference"},
    "stats_table": {"x": 0.3, "y": 3.8, "width": 6.0, "height": 2.9, "color": "#009688", "fill": "#E0F2F1", "enabled": False, "label": "Statistics Table"},
    "summary": {"x": 0.3, "y": 6.8, "width": 12.733, "height": 0.5, "color": "#607D8B", "fill": "#ECEFF1", "enabled": False, "label": "Summary"},
}

diffmap_layout_boxes = {}
diffmap_box_enable_vars = {}
dm_slide_canvases = {}
dm_slide_frames = {}
diffmap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": 1}

dm_slides_control_frame = tk.Frame(diffmap_preview_outer_frame)
dm_slides_control_frame.pack(fill=tk.X, padx=5, pady=5)
tk.Label(dm_slides_control_frame, text="Number of Slides per Parameter:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
diffmap_slides_number_var = tk.IntVar(value=1)

dm_slides_notebook = ttk.Notebook(diffmap_preview_outer_frame)
dm_slides_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

def create_dm_slide_tab(slide_num):
    import copy
    slide_frame = tk.Frame(dm_slides_notebook)
    dm_slides_notebook.add(slide_frame, text=f"Slide {slide_num}")
    dm_slide_frames[slide_num] = slide_frame
    diffmap_layout_boxes[slide_num] = copy.deepcopy(diffmap_layout_boxes_template)
    diffmap_box_enable_vars[slide_num] = {}

    canvas_frame = tk.Frame(slide_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    canvas = tk.Canvas(canvas_frame, width=int(13.333*DIFFMAP_PREVIEW_SCALE), height=int(7.5*DIFFMAP_PREVIEW_SCALE), bg="white", relief="solid", bd=1)
    canvas.pack(fill=tk.BOTH, expand=True)
    dm_slide_canvases[slide_num] = canvas

    cb_frame = tk.LabelFrame(slide_frame, text="Elements (check to include)", font=("Helvetica", 9))
    cb_frame.pack(fill=tk.X, padx=5, pady=5)
    for box_name, box_data in diffmap_layout_boxes[slide_num].items():
        var = tk.BooleanVar(value=box_data["enabled"])
        diffmap_box_enable_vars[slide_num][box_name] = var
        cb = tk.Checkbutton(cb_frame, text=box_data["label"], variable=var, font=("Helvetica", 8), fg=box_data["color"], command=lambda sn=slide_num: draw_dm_slide_preview(sn))
        cb.pack(side=tk.LEFT, padx=3)

    canvas.bind("<ButtonPress-1>", lambda e, sn=slide_num: on_dm_preview_press(e, sn))
    canvas.bind("<B1-Motion>", lambda e, sn=slide_num: on_dm_preview_drag(e, sn))
    canvas.bind("<ButtonRelease-1>", lambda e, sn=slide_num: on_dm_preview_release(e, sn))
    draw_dm_slide_preview(slide_num)

def update_dm_slide_tabs():
    num_slides = diffmap_slides_number_var.get()
    current_tabs = len(dm_slides_notebook.tabs())
    while current_tabs > num_slides:
        if current_tabs in dm_slide_frames:
            dm_slides_notebook.forget(current_tabs - 1)
            del dm_slide_frames[current_tabs]
            del dm_slide_canvases[current_tabs]
            del diffmap_layout_boxes[current_tabs]
            del diffmap_box_enable_vars[current_tabs]
        current_tabs -= 1
    while current_tabs < num_slides:
        create_dm_slide_tab(current_tabs + 1)
        current_tabs += 1

def draw_dm_slide_preview(slide_num):
    if slide_num not in dm_slide_canvases: return
    canvas = dm_slide_canvases[slide_num]
    canvas.delete("all")
    scale = DIFFMAP_PREVIEW_SCALE
    slide_w, slide_h = int(13.333*scale), int(7.5*scale)
    canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2)
    for i in range(1, 13): canvas.create_line(i*scale, 0, i*scale, slide_h, fill="#EEEEEE", dash=(2,4))
    for i in range(1, 7): canvas.create_line(0, i*scale, slide_w, i*scale, fill="#EEEEEE", dash=(2,4))
    for box_name, box_data in diffmap_layout_boxes[slide_num].items():
        if not diffmap_box_enable_vars[slide_num].get(box_name, tk.BooleanVar(value=True)).get(): continue
        x, y = box_data["x"]*scale, box_data["y"]*scale
        w, h = box_data["width"]*scale, box_data["height"]*scale
        canvas.create_rectangle(x, y, x+w, y+h, fill=box_data["fill"], outline=box_data["color"], width=2, tags=(f"box_{box_name}", "box", "movable"))
        canvas.create_text(x+w/2, y+h/2, text=box_data["label"], font=("Helvetica", 8, "bold"), fill=box_data["color"])
        canvas.create_rectangle(x+w-12, y+h-12, x+w, y+h, fill=box_data["color"], outline="white", tags=(f"handle_{box_name}", "handle"))

def on_dm_preview_press(event, slide_num):
    global diffmap_preview_drag_data
    canvas = dm_slide_canvases[slide_num]
    items = canvas.find_overlapping(event.x-8, event.y-8, event.x+8, event.y+8)
    for item in items:
        for tag in canvas.gettags(item):
            if tag.startswith("handle_"):
                diffmap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": tag.replace("handle_", ""), "slide_num": slide_num}
                return
    for item in items:
        tags = canvas.gettags(item)
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_"):
                    diffmap_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": tag.replace("box_", ""), "slide_num": slide_num}
                    return

def on_dm_preview_drag(event, slide_num):
    global diffmap_preview_drag_data
    if diffmap_preview_drag_data["box_name"] is None or diffmap_preview_drag_data["slide_num"] != slide_num: return
    box_name = diffmap_preview_drag_data["box_name"]
    dx, dy = (event.x - diffmap_preview_drag_data["x"]) / DIFFMAP_PREVIEW_SCALE, (event.y - diffmap_preview_drag_data["y"]) / DIFFMAP_PREVIEW_SCALE
    if diffmap_preview_drag_data["mode"] == "move":
        diffmap_layout_boxes[slide_num][box_name]["x"] = max(0, diffmap_layout_boxes[slide_num][box_name]["x"] + dx)
        diffmap_layout_boxes[slide_num][box_name]["y"] = max(0, diffmap_layout_boxes[slide_num][box_name]["y"] + dy)
    elif diffmap_preview_drag_data["mode"] == "resize":
        diffmap_layout_boxes[slide_num][box_name]["width"] = max(1, diffmap_layout_boxes[slide_num][box_name]["width"] + dx)
        diffmap_layout_boxes[slide_num][box_name]["height"] = max(0.5, diffmap_layout_boxes[slide_num][box_name]["height"] + dy)
    diffmap_preview_drag_data["x"], diffmap_preview_drag_data["y"] = event.x, event.y
    draw_dm_slide_preview(slide_num)

def on_dm_preview_release(event, slide_num):
    global diffmap_preview_drag_data
    diffmap_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": slide_num}

create_dm_slide_tab(1)

def on_dm_slides_spinbox_change(): update_dm_slide_tabs()
diffmap_slides_spinbox = tk.Spinbox(dm_slides_control_frame, from_=1, to=4, textvariable=diffmap_slides_number_var, width=3, font=("Helvetica", 10), command=on_dm_slides_spinbox_change)
diffmap_slides_spinbox.pack(side=tk.LEFT, padx=5)

def draw_diffmap_preview(): draw_dm_slide_preview(1)
tk.Label(diffmap_preview_outer_frame, text="Drag boxes to move, corner to resize | Slide: 13.333 x 7.5 inches", font=("Helvetica", 8), fg="#666666").pack(pady=2)

'''

content = content[:start_idx] + new_diffmap + content[end_idx:]
print("Diffmap Tab updated with Slide Tabs")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
