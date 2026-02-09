#!/usr/bin/env python3
"""Add Slide Tabs system to GRR Report Tab"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the GRR section
grr_start = '''# RIGHT SIDE: Interactive Layout Preview for Gage R&R
grr_preview_outer_frame = tk.LabelFrame(grr_split_frame, text="📐 Slide Layout Preview", font=("Helvetica", 10, "bold"))'''

grr_end = '''# Initial draw
draw_grr_preview()

# Select All checkbox for Gage R&R'''

start_idx = content.find(grr_start)
end_idx = content.find(grr_end)

if start_idx == -1:
    print("Could not find GRR start marker")
    exit(1)
if end_idx == -1:
    print("Could not find GRR end marker")
    exit(1)

new_grr = '''# RIGHT SIDE: Interactive Layout Preview for GRR with Slide Tabs
grr_preview_outer_frame = tk.LabelFrame(grr_split_frame, text="Slide Layout Preview (Drag & Resize)", font=("Helvetica", 10, "bold"))
grr_split_frame.add(grr_preview_outer_frame, minsize=350, width=500)

GRR_PREVIEW_SCALE = 45

# Layout boxes template for GRR
grr_layout_boxes_template = {
    "title": {"x": 0.3, "y": 0.15, "width": 12.733, "height": 0.5, "color": "#1976D2", "fill": "#E3F2FD", "enabled": True, "label": "Title"},
    "grr_summary": {"x": 0.3, "y": 0.7, "width": 6.0, "height": 3.0, "color": "#4CAF50", "fill": "#E8F5E9", "enabled": True, "label": "GRR Summary"},
    "variance": {"x": 6.5, "y": 0.7, "width": 6.5, "height": 3.0, "color": "#FF9800", "fill": "#FFF3E0", "enabled": True, "label": "Variance Chart"},
    "charts": {"x": 0.3, "y": 3.8, "width": 6.0, "height": 3.0, "color": "#9C27B0", "fill": "#F3E5F5", "enabled": True, "label": "Range/Mean Charts"},
    "anova": {"x": 6.5, "y": 3.8, "width": 6.5, "height": 3.0, "color": "#2196F3", "fill": "#E3F2FD", "enabled": True, "label": "ANOVA Table"},
    "stats_table": {"x": 0.3, "y": 6.8, "width": 12.733, "height": 0.5, "color": "#009688", "fill": "#E0F2F1", "enabled": False, "label": "Statistics Table"},
}

grr_layout_boxes = {}
grr_box_enable_vars = {}
grr_slide_canvases = {}
grr_slide_frames = {}
grr_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": 1}

grr_slides_control_frame = tk.Frame(grr_preview_outer_frame)
grr_slides_control_frame.pack(fill=tk.X, padx=5, pady=5)
tk.Label(grr_slides_control_frame, text="Number of Slides per Parameter:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
grr_slides_number_var = tk.IntVar(value=1)

grr_slides_notebook = ttk.Notebook(grr_preview_outer_frame)
grr_slides_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

def create_grr_slide_tab(slide_num):
    import copy
    slide_frame = tk.Frame(grr_slides_notebook)
    grr_slides_notebook.add(slide_frame, text=f"Slide {slide_num}")
    grr_slide_frames[slide_num] = slide_frame
    grr_layout_boxes[slide_num] = copy.deepcopy(grr_layout_boxes_template)
    grr_box_enable_vars[slide_num] = {}

    canvas_frame = tk.Frame(slide_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    canvas = tk.Canvas(canvas_frame, width=int(13.333*GRR_PREVIEW_SCALE), height=int(7.5*GRR_PREVIEW_SCALE), bg="white", relief="solid", bd=1)
    canvas.pack(fill=tk.BOTH, expand=True)
    grr_slide_canvases[slide_num] = canvas

    cb_frame = tk.LabelFrame(slide_frame, text="Elements (check to include)", font=("Helvetica", 9))
    cb_frame.pack(fill=tk.X, padx=5, pady=5)
    for box_name, box_data in grr_layout_boxes[slide_num].items():
        var = tk.BooleanVar(value=box_data["enabled"])
        grr_box_enable_vars[slide_num][box_name] = var
        cb = tk.Checkbutton(cb_frame, text=box_data["label"], variable=var, font=("Helvetica", 8), fg=box_data["color"], command=lambda sn=slide_num: draw_grr_slide_preview(sn))
        cb.pack(side=tk.LEFT, padx=3)

    canvas.bind("<ButtonPress-1>", lambda e, sn=slide_num: on_grr_preview_press(e, sn))
    canvas.bind("<B1-Motion>", lambda e, sn=slide_num: on_grr_preview_drag(e, sn))
    canvas.bind("<ButtonRelease-1>", lambda e, sn=slide_num: on_grr_preview_release(e, sn))
    draw_grr_slide_preview(slide_num)

def update_grr_slide_tabs():
    num_slides = grr_slides_number_var.get()
    current_tabs = len(grr_slides_notebook.tabs())
    while current_tabs > num_slides:
        if current_tabs in grr_slide_frames:
            grr_slides_notebook.forget(current_tabs - 1)
            del grr_slide_frames[current_tabs]
            del grr_slide_canvases[current_tabs]
            del grr_layout_boxes[current_tabs]
            del grr_box_enable_vars[current_tabs]
        current_tabs -= 1
    while current_tabs < num_slides:
        create_grr_slide_tab(current_tabs + 1)
        current_tabs += 1

def draw_grr_slide_preview(slide_num):
    if slide_num not in grr_slide_canvases: return
    canvas = grr_slide_canvases[slide_num]
    canvas.delete("all")
    scale = GRR_PREVIEW_SCALE
    slide_w, slide_h = int(13.333*scale), int(7.5*scale)
    canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2)
    for i in range(1, 13): canvas.create_line(i*scale, 0, i*scale, slide_h, fill="#EEEEEE", dash=(2,4))
    for i in range(1, 7): canvas.create_line(0, i*scale, slide_w, i*scale, fill="#EEEEEE", dash=(2,4))
    for box_name, box_data in grr_layout_boxes[slide_num].items():
        if not grr_box_enable_vars[slide_num].get(box_name, tk.BooleanVar(value=True)).get(): continue
        x, y = box_data["x"]*scale, box_data["y"]*scale
        w, h = box_data["width"]*scale, box_data["height"]*scale
        canvas.create_rectangle(x, y, x+w, y+h, fill=box_data["fill"], outline=box_data["color"], width=2, tags=(f"box_{box_name}", "box", "movable"))
        canvas.create_text(x+w/2, y+h/2, text=box_data["label"], font=("Helvetica", 8, "bold"), fill=box_data["color"])
        canvas.create_rectangle(x+w-12, y+h-12, x+w, y+h, fill=box_data["color"], outline="white", tags=(f"handle_{box_name}", "handle"))

def on_grr_preview_press(event, slide_num):
    global grr_preview_drag_data
    canvas = grr_slide_canvases[slide_num]
    items = canvas.find_overlapping(event.x-8, event.y-8, event.x+8, event.y+8)
    for item in items:
        for tag in canvas.gettags(item):
            if tag.startswith("handle_"):
                grr_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": tag.replace("handle_", ""), "slide_num": slide_num}
                return
    for item in items:
        tags = canvas.gettags(item)
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_"):
                    grr_preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": tag.replace("box_", ""), "slide_num": slide_num}
                    return

def on_grr_preview_drag(event, slide_num):
    global grr_preview_drag_data
    if grr_preview_drag_data["box_name"] is None or grr_preview_drag_data["slide_num"] != slide_num: return
    box_name = grr_preview_drag_data["box_name"]
    dx, dy = (event.x - grr_preview_drag_data["x"]) / GRR_PREVIEW_SCALE, (event.y - grr_preview_drag_data["y"]) / GRR_PREVIEW_SCALE
    if grr_preview_drag_data["mode"] == "move":
        grr_layout_boxes[slide_num][box_name]["x"] = max(0, grr_layout_boxes[slide_num][box_name]["x"] + dx)
        grr_layout_boxes[slide_num][box_name]["y"] = max(0, grr_layout_boxes[slide_num][box_name]["y"] + dy)
    elif grr_preview_drag_data["mode"] == "resize":
        grr_layout_boxes[slide_num][box_name]["width"] = max(1, grr_layout_boxes[slide_num][box_name]["width"] + dx)
        grr_layout_boxes[slide_num][box_name]["height"] = max(0.5, grr_layout_boxes[slide_num][box_name]["height"] + dy)
    grr_preview_drag_data["x"], grr_preview_drag_data["y"] = event.x, event.y
    draw_grr_slide_preview(slide_num)

def on_grr_preview_release(event, slide_num):
    global grr_preview_drag_data
    grr_preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None, "slide_num": slide_num}

create_grr_slide_tab(1)

def on_grr_slides_spinbox_change(): update_grr_slide_tabs()
grr_slides_spinbox = tk.Spinbox(grr_slides_control_frame, from_=1, to=4, textvariable=grr_slides_number_var, width=3, font=("Helvetica", 10), command=on_grr_slides_spinbox_change)
grr_slides_spinbox.pack(side=tk.LEFT, padx=5)

def draw_grr_preview(): draw_grr_slide_preview(1)
tk.Label(grr_preview_outer_frame, text="Drag boxes to move, corner to resize | Slide: 13.333 x 7.5 inches", font=("Helvetica", 8), fg="#666666").pack(pady=2)

'''

content = content[:start_idx] + new_grr + content[end_idx:]
print("GRR Tab updated with Slide Tabs")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
