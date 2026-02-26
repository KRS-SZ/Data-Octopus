#!/usr/bin/env python3
"""Fix Diffmap heatmap display - add debug and fix parameter column matching"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: Add debug output to understand what's happening
old_code = '''def update_diffmap_heatmap_display():
    """Update the diffmap heatmap display - SAME style as Multi-Wafer tab"""
    global diffmap_canvas, diffmap_result_data, diffmap_boxplot_canvas, diffmap_hist_canvas

    if diffmap_result_data is None or diffmap_result_data.empty:
        return

    selected = diffmap_param_combobox.get()

    if not selected:
        return

    # Parse parameter selection
    if selected.startswith("BIN") or selected == "BIN (Bin Number)":
        param_column = "bin"
        param_label = "Bin Difference"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            try:
                param_column = int(test_key)
            except ValueError:
                param_column = test_key
        # Use simplified parameter name
        full_name = selected.split(":")[-1].strip() if ":" in selected else selected
        param_label = simplify_param_name(full_name)

    if param_column not in diffmap_result_data.columns:
        return'''

new_code = '''def update_diffmap_heatmap_display():
    """Update the diffmap heatmap display - SAME style as Multi-Wafer tab"""
    global diffmap_canvas, diffmap_result_data, diffmap_boxplot_canvas, diffmap_hist_canvas

    if diffmap_result_data is None or diffmap_result_data.empty:
        print("DEBUG: diffmap_result_data is None or empty")
        return

    selected = diffmap_param_combobox.get()
    print(f"DEBUG: Selected parameter: '{selected}'")

    if not selected:
        print("DEBUG: No parameter selected")
        return

    # Parse parameter selection
    if selected.startswith("BIN") or selected == "BIN (Bin Number)":
        param_column = "bin"
        param_label = "Bin Difference"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            try:
                param_column = int(test_key)
            except ValueError:
                param_column = test_key
        # Use simplified parameter name
        full_name = selected.split(":")[-1].strip() if ":" in selected else selected
        param_label = simplify_param_name(full_name)

    print(f"DEBUG: Parsed param_column: {param_column}, type: {type(param_column)}")
    print(f"DEBUG: Available columns (first 20): {list(diffmap_result_data.columns)[:20]}")

    # Check if column exists - try both int and string versions
    if param_column not in diffmap_result_data.columns:
        # Try string version
        str_col = str(param_column)
        if str_col in diffmap_result_data.columns:
            param_column = str_col
            print(f"DEBUG: Found as string column: {param_column}")
        else:
            print(f"DEBUG: Column {param_column} NOT found in data!")
            return'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Added debug output to update_diffmap_heatmap_display")
else:
    print("Could not find code to replace")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
