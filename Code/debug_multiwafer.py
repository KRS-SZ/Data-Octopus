#!/usr/bin/env python3
"""Add debug to Multi-Wafer display to find the issue"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add debug at start of update_multi_wafer_display
old_code = '''def update_multi_wafer_display():
    """Update the multiple wafermaps display - only show selected wafers"""
    global multi_wafer_canvas, multi_wafer_stdf_data, multi_wafer_wafer_ids
    global multi_wafer_plot_data_cache  # Store data for click handler

    # Remove independent selector frame if it exists
    if hasattr(create_independent_param_selectors, 'selector_frame') and create_independent_param_selectors.selector_frame:
        create_independent_param_selectors.selector_frame.destroy()
        create_independent_param_selectors.selector_frame = None

    if not multi_wafer_stdf_data:
        print("No wafermap data loaded for Multiple Wafermaps tab")
        return

    # Get selected wafer indices
    selected_indices = get_selected_wafer_indices()

    if not selected_indices:
        print("No wafers selected for display")
        # Clear existing canvas
        if multi_wafer_canvas:
            if hasattr(multi_wafer_canvas, 'get_tk_widget'):
                multi_wafer_canvas.get_tk_widget().destroy()
            else:
                multi_wafer_canvas.destroy()
            multi_wafer_canvas = None
        return

    selected = multi_wafer_param_combobox.get()

    if not selected:
        print("No parameter selected")
        return'''

new_code = '''def update_multi_wafer_display():
    """Update the multiple wafermaps display - only show selected wafers"""
    global multi_wafer_canvas, multi_wafer_stdf_data, multi_wafer_wafer_ids
    global multi_wafer_plot_data_cache  # Store data for click handler

    print("=" * 50)
    print("DEBUG: update_multi_wafer_display() called")
    print(f"DEBUG: multi_wafer_stdf_data has {len(multi_wafer_stdf_data) if multi_wafer_stdf_data else 0} entries")

    # Remove independent selector frame if it exists
    if hasattr(create_independent_param_selectors, 'selector_frame') and create_independent_param_selectors.selector_frame:
        create_independent_param_selectors.selector_frame.destroy()
        create_independent_param_selectors.selector_frame = None

    if not multi_wafer_stdf_data:
        print("DEBUG: No wafermap data loaded for Multiple Wafermaps tab")
        return

    # Get selected wafer indices
    selected_indices = get_selected_wafer_indices()
    print(f"DEBUG: selected_indices = {selected_indices}")

    if not selected_indices:
        print("DEBUG: No wafers selected for display")
        # Clear existing canvas
        if multi_wafer_canvas:
            if hasattr(multi_wafer_canvas, 'get_tk_widget'):
                multi_wafer_canvas.get_tk_widget().destroy()
            else:
                multi_wafer_canvas.destroy()
            multi_wafer_canvas = None
        return

    selected = multi_wafer_param_combobox.get()
    print(f"DEBUG: selected parameter = '{selected}'")

    if not selected:
        print("DEBUG: No parameter selected")
        return'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Added debug to update_multi_wafer_display")
else:
    print("Could not find update_multi_wafer_display code")

# Also add debug to refresh_current_multi_wafer_tab
old_refresh = '''def refresh_current_multi_wafer_tab():
    """Refresh the currently visible sub-tab"""
    current_tab = multi_wafer_sub_notebook.index(multi_wafer_sub_notebook.select())
    if current_tab == 0:
        update_testheader_comparison()
    elif current_tab == 1:
        # Check if Independent mode is active
        if multi_wafer_compare_independent_var.get():
            update_multi_wafer_independent_display()
        else:
            update_multi_wafer_display()'''

new_refresh = '''def refresh_current_multi_wafer_tab():
    """Refresh the currently visible sub-tab"""
    current_tab = multi_wafer_sub_notebook.index(multi_wafer_sub_notebook.select())
    print(f"DEBUG: refresh_current_multi_wafer_tab() - current_tab = {current_tab}")
    if current_tab == 0:
        update_testheader_comparison()
    elif current_tab == 1:
        # Check if Independent mode is active
        if multi_wafer_compare_independent_var.get():
            print("DEBUG: Calling update_multi_wafer_independent_display()")
            update_multi_wafer_independent_display()
        else:
            print("DEBUG: Calling update_multi_wafer_display()")
            update_multi_wafer_display()'''

if old_refresh in content:
    content = content.replace(old_refresh, new_refresh)
    print("Added debug to refresh_current_multi_wafer_tab")
else:
    print("Could not find refresh_current_multi_wafer_tab code")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
