#!/usr/bin/env python3
"""Remove old duplicate functions that reference non-existent pptx_preview_canvas"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old duplicate draw_interactive_preview and related functions
old_code_to_remove = '''def draw_interactive_preview():
    """Draw the interactive preview with draggable boxes"""
    pptx_preview_canvas.delete("all")

    # Draw slide background
    slide_w = int(PPTX_SLIDE_WIDTH * PREVIEW_SCALE)
    slide_h = int(PPTX_SLIDE_HEIGHT * PREVIEW_SCALE)
    pptx_preview_canvas.create_rectangle(2, 2, slide_w-2, slide_h-2, fill="#F5F5F5", outline="#CCCCCC", width=2, tags="background")

    # Draw grid lines for guidance
    for i in range(1, 13):
        x = i * PREVIEW_SCALE
        pptx_preview_canvas.create_line(x, 0, x, slide_h, fill="#EEEEEE", dash=(2, 4), tags="grid")
    for i in range(1, 7):
        y = i * PREVIEW_SCALE
        pptx_preview_canvas.create_line(0, y, slide_w, y, fill="#EEEEEE", dash=(2, 4), tags="grid")

    # Draw each enabled box
    for box_name, box_data in pptx_layout_boxes.items():
        if not box_enable_vars.get(box_name, tk.BooleanVar(value=True)).get():
            continue

        x = box_data["x"] * PREVIEW_SCALE
        y = box_data["y"] * PREVIEW_SCALE
        w = box_data["width"] * PREVIEW_SCALE
        h = box_data["height"] * PREVIEW_SCALE

        # Draw the box
        rect_id = pptx_preview_canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=box_data["fill"], outline=box_data["color"], width=2,
            tags=(f"box_{box_name}", "box", "movable")
        )

        # Draw the label
        label_id = pptx_preview_canvas.create_text(
            x + w/2, y + h/2,
            text=box_data["label"], font=("Helvetica", 9, "bold"), fill=box_data["color"],
            tags=(f"label_{box_name}", f"box_{box_name}", "movable")
        )

        # Draw resize handle (bottom-right corner) - MUCH LARGER for easier clicking
        handle_size = 20
        handle_id = pptx_preview_canvas.create_rectangle(
            x + w - handle_size, y + h - handle_size, x + w, y + h,
            fill=box_data["color"], outline="white", width=2,
            tags=(f"handle_{box_name}", "handle")
        )

        # Draw resize indicator (diagonal lines in handle)
        pptx_preview_canvas.create_line(
            x + w - handle_size + 4, y + h - 4,
            x + w - 4, y + h - handle_size + 4,
            fill="white", width=2, tags=(f"handle_{box_name}", "handle")
        )
        pptx_preview_canvas.create_line(
            x + w - handle_size + 10, y + h - 4,
            x + w - 4, y + h - handle_size + 10,
            fill="white", width=2, tags=(f"handle_{box_name}", "handle")
        )

        # Draw dimensions text
        dim_text = f"{box_data['width']:.1f}\\" × {box_data['height']:.1f}\\""
        pptx_preview_canvas.create_text(
            x + w/2, y + h + 10,
            text=dim_text, font=("Helvetica", 7), fill="#888888",
            tags=(f"dim_{box_name}",)
        )

def on_preview_press(event):
    """Handle mouse press on preview canvas"""
    global preview_drag_data

    # Find what was clicked - use larger area for handles
    # First check handles with bigger tolerance
    handle_items = pptx_preview_canvas.find_overlapping(event.x-10, event.y-10, event.x+10, event.y+10)

    for item in handle_items:
        tags = pptx_preview_canvas.gettags(item)
        for tag in tags:
            if tag.startswith("handle_"):
                box_name = tag.replace("handle_", "")
                if box_name in pptx_layout_boxes:
                    preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "resize", "box_name": box_name}
                    pptx_preview_canvas.config(cursor="bottom_right_corner")
                    print(f"RESIZE mode for {box_name}")
                    return

    # Then check movable boxes with normal tolerance
    items = pptx_preview_canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)

    for item in items:
        tags = pptx_preview_canvas.gettags(item)

        # Check if it's a movable box
        if "movable" in tags:
            for tag in tags:
                if tag.startswith("box_") and not tag.startswith("box_name"):
                    box_name = tag.replace("box_", "")
                    if box_name in pptx_layout_boxes:
                        preview_drag_data = {"item": item, "x": event.x, "y": event.y, "mode": "move", "box_name": box_name}
                        pptx_preview_canvas.config(cursor="fleur")
                        print(f"MOVE mode for {box_name}")
                        return

def on_preview_drag(event):
    """Handle mouse drag on preview canvas"""
    global preview_drag_data

    if preview_drag_data["box_name"] is None:
        return

    box_name = preview_drag_data["box_name"]
    dx = event.x - preview_drag_data["x"]
    dy = event.y - preview_drag_data["y"]

    # Convert to inches
    dx_inches = dx / PREVIEW_SCALE
    dy_inches = dy / PREVIEW_SCALE

    if preview_drag_data["mode"] == "move":
        # Move the box
        new_x = max(0, min(PPTX_SLIDE_WIDTH - pptx_layout_boxes[box_name]["width"],
                          pptx_layout_boxes[box_name]["x"] + dx_inches))
        new_y = max(0, min(PPTX_SLIDE_HEIGHT - pptx_layout_boxes[box_name]["height"],
                          pptx_layout_boxes[box_name]["y"] + dy_inches))
        pptx_layout_boxes[box_name]["x"] = round(new_x, 2)
        pptx_layout_boxes[box_name]["y"] = round(new_y, 2)

    elif preview_drag_data["mode"] == "resize":
        # Resize the box
        new_w = max(0.5, min(PPTX_SLIDE_WIDTH - pptx_layout_boxes[box_name]["x"],
                            pptx_layout_boxes[box_name]["width"] + dx_inches))
        new_h = max(0.3, min(PPTX_SLIDE_HEIGHT - pptx_layout_boxes[box_name]["y"],
                            pptx_layout_boxes[box_name]["height"] + dy_inches))
        pptx_layout_boxes[box_name]["width"] = round(new_w, 2)
        pptx_layout_boxes[box_name]["height"] = round(new_h, 2)

    preview_drag_data["x"] = event.x
    preview_drag_data["y"] = event.y

    draw_interactive_preview()
    update_position_display()

def on_preview_release(event):
    """Handle mouse release on preview canvas"""
    global preview_drag_data
    preview_drag_data = {"item": None, "x": 0, "y": 0, "mode": None, "box_name": None}
    pptx_preview_canvas.config(cursor="")

# Bind mouse events
pptx_preview_canvas.bind("<ButtonPress-1>", on_preview_press)
pptx_preview_canvas.bind("<B1-Motion>", on_preview_drag)
pptx_preview_canvas.bind("<ButtonRelease-1>", on_preview_release)

# Position display frame
position_display_frame = tk.LabelFrame(preview_outer_frame, text="Position & Größe (inches)", font=("Helvetica", 9))
position_display_frame.pack(fill=tk.X, padx=5, pady=5)

position_labels = {}
for box_name, box_data in pptx_layout_boxes.items():
    row_frame = tk.Frame(position_display_frame)
    row_frame.pack(fill=tk.X, pady=1)'''

# New simplified code that uses the slide tabs
new_code = '''# Position display frame
position_display_frame = tk.LabelFrame(preview_outer_frame, text="Position & Size (inches)", font=("Helvetica", 9))
position_display_frame.pack(fill=tk.X, padx=5, pady=5)

def update_position_display():
    """Update position display for current slide"""
    pass  # Position is shown in the canvas already

position_labels = {}
# Create position labels for slide 1 initially
if 1 in pptx_layout_boxes:
    for box_name, box_data in pptx_layout_boxes[1].items():
        row_frame = tk.Frame(position_display_frame)
        row_frame.pack(fill=tk.X, pady=1)'''

if old_code_to_remove in content:
    content = content.replace(old_code_to_remove, new_code)
    print("Removed old duplicate functions and bindings")
else:
    print("Could not find old code to remove - trying partial match")
    # Try to find and remove just the bindings
    if 'pptx_preview_canvas.bind("<ButtonPress-1>"' in content:
        # Find position of this line and remove the three bind lines
        lines = content.split('\n')
        new_lines = []
        skip_next = 0
        for i, line in enumerate(lines):
            if skip_next > 0:
                skip_next -= 1
                continue
            if 'pptx_preview_canvas.bind("<ButtonPress-1>"' in line:
                skip_next = 2  # Skip this and next 2 lines
                continue
            new_lines.append(line)
        content = '\n'.join(new_lines)
        print("Removed pptx_preview_canvas.bind lines")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
