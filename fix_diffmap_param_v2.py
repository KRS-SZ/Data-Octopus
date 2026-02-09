# Fix parameter matching in Diffmap Tab
# Apply the same fix as Multi-Wafer Tab

import re

# Read the file
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: update_correlation_plot_display
old_code1 = '''    # Parse parameter selection
    if selected.startswith("BIN") or selected == "BIN (Bin Number)":
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            param_column = int(test_key.replace("test_", ""))
        else:
            try:
                param_column = int(test_key)
            except ValueError:
                print(f"Could not parse parameter: {selected}")
                return
        param_label = selected.split(":")[-1].strip() if ":" in selected else selected

    # Check if parameter exists in both datasets
    if param_column not in diffmap_reference_data.columns:
        print(f"Parameter {param_column} not found in reference data")
        return
    if param_column not in diffmap_compare_data.columns:
        print(f"Parameter {param_column} not found in comparison data")
        return'''

new_code1 = '''    # Parse parameter selection
    if selected.startswith("BIN") or selected == "BIN (Bin Number)":
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            test_num = int(test_key.replace("test_", ""))
        else:
            try:
                test_num = int(test_key)
            except ValueError:
                print(f"Could not parse parameter: {selected}")
                return
        param_column = test_num  # Start with integer
        param_label = selected.split(":")[-1].strip() if ":" in selected else selected

        # Find the correct column in reference data
        param_column = _find_param_column(diffmap_reference_data, test_num, diffmap_test_params)

    # Check if parameter exists in both datasets
    if param_column not in diffmap_reference_data.columns:
        print(f"Parameter {param_column} not found in reference data")
        print(f"Available columns: {list(diffmap_reference_data.columns)[:15]}")
        return
    if param_column not in diffmap_compare_data.columns:
        print(f"Parameter {param_column} not found in comparison data")
        return'''

if old_code1 in content:
    content = content.replace(old_code1, new_code1)
    print("Fixed: update_correlation_plot_display parameter matching")
else:
    print("WARNING: Could not find update_correlation_plot_display code block")

# Fix 2: update_diffmap_heatmap_display
old_code2 = '''    # Parse parameter selection
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

new_code2 = '''    # Parse parameter selection
    if selected.startswith("BIN") or selected == "BIN (Bin Number)":
        param_column = "bin"
        param_label = "Bin Difference"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            test_num = int(test_key.replace("test_", ""))
        else:
            try:
                test_num = int(test_key)
            except ValueError:
                test_num = None
                param_column = test_key

        if test_num is not None:
            # Find the correct column using helper function
            param_column = _find_param_column(diffmap_result_data, test_num, diffmap_test_params)

        # Use simplified parameter name
        full_name = selected.split(":")[-1].strip() if ":" in selected else selected
        param_label = simplify_param_name(full_name)

    if param_column not in diffmap_result_data.columns:
        print(f"DEBUG: Column {param_column} not in diffmap_result_data")
        print(f"DEBUG: Available columns: {list(diffmap_result_data.columns)[:15]}")
        return'''

if old_code2 in content:
    content = content.replace(old_code2, new_code2)
    print("Fixed: update_diffmap_heatmap_display parameter matching")
else:
    print("WARNING: Could not find update_diffmap_heatmap_display code block")

# Now we need to add the helper function _find_param_column if it doesn't exist
helper_function = '''
def _find_param_column(df, test_num, test_params_dict):
    """Helper function to find the correct column in DataFrame for a given test number"""
    # 1. Direct integer match
    if test_num in df.columns:
        return test_num

    # 2. String version of integer
    if str(test_num) in df.columns:
        return str(test_num)

    # 3. test_N format
    if f"test_{test_num}" in df.columns:
        return f"test_{test_num}"

    # 4. Look up in test_params dict (for CSV data with original column names)
    test_key = f"test_{test_num}"
    if test_key in test_params_dict:
        original_col = test_params_dict[test_key]
        if original_col in df.columns:
            return original_col

    # 5. Search for column ending with test number (CSV format like _10020001)
    for col in df.columns:
        if str(col).endswith(f"_{test_num}"):
            return col

    # Nothing found, return original
    return test_num

'''

# Check if helper function exists
if "_find_param_column" not in content:
    # Find a good place to insert it - before update_diffmap_display
    insert_marker = "def update_diffmap_display():"
    if insert_marker in content:
        content = content.replace(insert_marker, helper_function + insert_marker)
        print("Added: _find_param_column helper function")
    else:
        print("WARNING: Could not find insertion point for helper function")
else:
    print("Helper function _find_param_column already exists")

# Write back
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone! Diffmap parameter matching fixed.")
