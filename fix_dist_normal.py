# Fix the distribution normal mode - last remaining fix

# Read the file
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''        # Parse parameter selection
        if selected.startswith("BIN"):
            param_column = "bin"
            param_label = "Bin"
        else:
            test_key = selected.split(":")[0].strip()
            if test_key.startswith("test_"):
                param_column = int(test_key.replace("test_", ""))
            else:
                param_column = int(test_key)
            # Use simplified parameter label
            full_name = selected.split(":")[-1].strip() if ":" in selected else selected
            param_label = simplify_param_name(full_name)

        # Get selected data and IDs
        selected_data = [multi_wafer_stdf_data[i] for i in selected_indices]
        selected_ids = [multi_wafer_wafer_ids[i] for i in selected_indices]

        for idx, (df, wafer_id, color) in enumerate(zip(selected_data, selected_ids, colors)):
            if param_column not in df.columns:'''

new_code = '''        # Parse parameter selection
        if selected.startswith("BIN"):
            param_column = "bin"
            param_label = "Bin"
        else:
            test_key = selected.split(":")[0].strip()
            if test_key.startswith("test_"):
                test_num = int(test_key.replace("test_", ""))
            else:
                test_num = int(test_key)
            # Use simplified parameter label
            full_name = selected.split(":")[-1].strip() if ":" in selected else selected
            param_label = simplify_param_name(full_name)

            # Find correct column using first available dataframe
            first_df = multi_wafer_stdf_data[selected_indices[0]] if selected_indices else None
            if first_df is not None:
                param_column = _find_param_column(first_df, test_num, multi_wafer_test_params)
            else:
                param_column = test_num

        # Get selected data and IDs
        selected_data = [multi_wafer_stdf_data[i] for i in selected_indices]
        selected_ids = [multi_wafer_wafer_ids[i] for i in selected_indices]

        for idx, (df, wafer_id, color) in enumerate(zip(selected_data, selected_ids, colors)):
            if param_column not in df.columns:'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Fixed: Distribution normal mode")
else:
    print("Pattern not found. Searching for similar code...")
    # Find the line numbers
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "# Parse parameter selection" in line and "for distribution" not in line and i > 14650:
            print(f"Found at line {i+1}")
            for j in range(i, min(i+20, len(lines))):
                print(f"{j+1}: {repr(lines[j])}")
            break

# Write back
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
