#!/usr/bin/env python3
"""Fix Multi-Wafer parameter column matching"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the parameter column matching - add check for both int and string
old_code = '''    # Parse parameter selection
    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label = selected

    # Get selected data and IDs
    selected_data = [multi_wafer_stdf_data[i] for i in selected_indices]
    selected_ids = [multi_wafer_wafer_ids[i] for i in selected_indices]'''

new_code = '''    # Parse parameter selection
    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            param_column = int(test_key)
        param_label = selected

    # Get selected data and IDs
    selected_data = [multi_wafer_stdf_data[i] for i in selected_indices]
    selected_ids = [multi_wafer_wafer_ids[i] for i in selected_indices]

    # Check and fix param_column type to match DataFrame columns
    if selected_data and len(selected_data) > 0:
        first_df = selected_data[0]
        if param_column not in first_df.columns:
            # Try string version
            if str(param_column) in first_df.columns:
                param_column = str(param_column)
                print(f"DEBUG: Converted param_column to string: {param_column}")
            # Try with test_ prefix
            elif f"test_{param_column}" in first_df.columns:
                param_column = f"test_{param_column}"
                print(f"DEBUG: Added test_ prefix: {param_column}")
            else:
                print(f"DEBUG: Column {param_column} not found in DataFrame!")
                print(f"DEBUG: Available columns: {list(first_df.columns)[:20]}")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Fixed Multi-Wafer parameter column matching")
else:
    print("Could not find old code - trying to find location...")
    # Show what we're looking for
    if "# Parse parameter selection" in content:
        print("Found '# Parse parameter selection' - checking format...")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
