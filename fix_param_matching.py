# Fix parameter matching in Multi-Wafer Tab
# The issue is that param_column parsing doesn't match DataFrame columns correctly

import re

# Read the file
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the parameter matching code in update_multi_wafer_display
# The problem is around lines 13179-13209

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

new_code = '''    # Parse parameter selection
    if selected.startswith("BIN"):
        param_column = "bin"
        param_label = "Bin"
    else:
        test_key = selected.split(":")[0].strip()
        if test_key.startswith("test_"):
            test_num = int(test_key.replace("test_", ""))
        else:
            test_num = int(test_key)
        param_column = test_num  # Start with integer
        param_label = selected

    # Get selected data and IDs
    selected_data = [multi_wafer_stdf_data[i] for i in selected_indices]
    selected_ids = [multi_wafer_wafer_ids[i] for i in selected_indices]

    # Check and fix param_column type to match DataFrame columns
    if selected_data and len(selected_data) > 0 and not selected.startswith("BIN"):
        first_df = selected_data[0]
        print(f"DEBUG: Looking for test_num={test_num}, type={type(test_num)}")
        print(f"DEBUG: DataFrame columns (first 10): {list(first_df.columns)[:10]}")
        print(f"DEBUG: Column types: {[type(c) for c in list(first_df.columns)[:5]]}")

        # Try different ways to find the column
        found = False

        # 1. Direct integer match
        if test_num in first_df.columns:
            param_column = test_num
            found = True
            print(f"DEBUG: Found as integer: {param_column}")

        # 2. String version of integer
        elif str(test_num) in first_df.columns:
            param_column = str(test_num)
            found = True
            print(f"DEBUG: Found as string: {param_column}")

        # 3. test_N format
        elif f"test_{test_num}" in first_df.columns:
            param_column = f"test_{test_num}"
            found = True
            print(f"DEBUG: Found as test_ format: {param_column}")

        # 4. Look up in multi_wafer_test_params dict for CSV data
        elif f"test_{test_num}" in multi_wafer_test_params:
            original_col = multi_wafer_test_params[f"test_{test_num}"]
            if original_col in first_df.columns:
                param_column = original_col
                found = True
                print(f"DEBUG: Found via test_params lookup: {param_column}")

        # 5. Search for column ending with test number (CSV format)
        if not found:
            for col in first_df.columns:
                if str(col).endswith(f"_{test_num}"):
                    param_column = col
                    found = True
                    print(f"DEBUG: Found by suffix match: {param_column}")
                    break

        if not found:
            print(f"DEBUG: Column for test {test_num} NOT FOUND!")
            print(f"DEBUG: Available columns: {list(first_df.columns)[:20]}")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Fixed: update_multi_wafer_display parameter matching")
else:
    print("ERROR: Could not find the old code block!")
    print("Searching for similar patterns...")

    # Try to find the function
    if "def update_multi_wafer_display" in content:
        print("Found update_multi_wafer_display function")
        # Find line number
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "# Parse parameter selection" in line and i > 13000:
                print(f"Found '# Parse parameter selection' at line {i+1}")
                # Show surrounding lines
                for j in range(i, min(i+40, len(lines))):
                    print(f"{j+1}: {lines[j]}")
                break
    else:
        print("Function not found!")

# Write back
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone!")
