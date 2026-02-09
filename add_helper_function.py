# Add _find_param_column helper function
# This function is missing and needs to be added

# Read the file
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the helper function
helper_function = '''
def _find_param_column(df, test_num, test_params_dict):
    """Helper function to find the correct column in DataFrame for a given test number.
    Tries multiple formats to match the column name:
    1. Direct integer match (for STDF data)
    2. String version of integer
    3. test_N format
    4. Original column name from test_params dict (for CSV data)
    5. Column ending with _test_num (CSV format like _10020001)
    """
    # 1. Direct integer match
    if test_num in df.columns:
        print(f"DEBUG _find_param_column: Found as integer: {test_num}")
        return test_num

    # 2. String version of integer
    if str(test_num) in df.columns:
        print(f"DEBUG _find_param_column: Found as string: {str(test_num)}")
        return str(test_num)

    # 3. test_N format
    if f"test_{test_num}" in df.columns:
        print(f"DEBUG _find_param_column: Found as test_ format: test_{test_num}")
        return f"test_{test_num}"

    # 4. Look up in test_params dict (for CSV data with original column names)
    test_key = f"test_{test_num}"
    if test_params_dict and test_key in test_params_dict:
        original_col = test_params_dict[test_key]
        if original_col in df.columns:
            print(f"DEBUG _find_param_column: Found via test_params lookup: {original_col}")
            return original_col

    # 5. Search for column ending with test number (CSV format like _10020001)
    for col in df.columns:
        if str(col).endswith(f"_{test_num}"):
            print(f"DEBUG _find_param_column: Found by suffix match: {col}")
            return col

    # Nothing found, return original
    print(f"DEBUG _find_param_column: NOT FOUND - returning original: {test_num}")
    print(f"DEBUG _find_param_column: Available columns (first 10): {list(df.columns)[:10]}")
    return test_num


'''

# Check if function already exists
if "def _find_param_column(" in content:
    print("Function _find_param_column already exists!")
else:
    # Find a good place to insert it - before update_diffmap_display
    insert_marker = "def update_diffmap_display():"
    if insert_marker in content:
        content = content.replace(insert_marker, helper_function + insert_marker)
        print("Added: _find_param_column helper function before update_diffmap_display")
    else:
        print("WARNING: Could not find insertion point")

# Write back
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
