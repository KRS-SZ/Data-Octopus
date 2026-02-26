# Fix parameter matching in Boxplot and Distribution functions
# Apply the same fix as Multi-Wafer Display

# Read the file
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

fixes_applied = 0

# ============================================================
# FIX 1: update_multi_wafer_boxplot - Independent mode section
# ============================================================
old_boxplot_indep = '''            # Parse the parameter
            if selected_param.startswith("BIN"):
                param_column = "bin"
                param_name = "Bin"
            else:
                test_key = selected_param.split(":")[0].strip()
                if test_key.startswith("test_"):
                    param_column = int(test_key.replace("test_", ""))
                else:
                    try:
                        param_column = int(test_key)
                    except ValueError:
                        param_column = "bin"
                # Extract simplified parameter name (without group/number)
                full_name = selected_param.split(":")[-1].strip() if ":" in selected_param else selected_param
                param_name = simplify_param_name(full_name)

            if param_column in df.columns:'''

new_boxplot_indep = '''            # Parse the parameter
            if selected_param.startswith("BIN"):
                param_column = "bin"
                param_name = "Bin"
            else:
                test_key = selected_param.split(":")[0].strip()
                if test_key.startswith("test_"):
                    test_num = int(test_key.replace("test_", ""))
                else:
                    try:
                        test_num = int(test_key)
                    except ValueError:
                        test_num = None
                        param_column = "bin"

                if test_num is not None:
                    # Use helper function to find correct column
                    param_column = _find_param_column(df, test_num, multi_wafer_test_params)

                # Extract simplified parameter name (without group/number)
                full_name = selected_param.split(":")[-1].strip() if ":" in selected_param else selected_param
                param_name = simplify_param_name(full_name)

            if param_column in df.columns:'''

if old_boxplot_indep in content:
    content = content.replace(old_boxplot_indep, new_boxplot_indep)
    fixes_applied += 1
    print("Fixed 1: Boxplot independent mode")
else:
    print("WARNING: Could not find boxplot independent mode code")

# ============================================================
# FIX 2: update_multi_wafer_boxplot - Normal mode section
# ============================================================
old_boxplot_normal = '''        # Parse parameter selection
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

        for df, wafer_id in zip(selected_data, selected_ids):
            if param_column in df.columns:'''

new_boxplot_normal = '''        # Parse parameter selection
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

            # Find correct column using first dataframe as reference
            if selected_data:
                param_column = _find_param_column(selected_data[0], test_num, multi_wafer_test_params)
            else:
                param_column = test_num

        for df, wafer_id in zip(selected_data, selected_ids):
            if param_column in df.columns:'''

if old_boxplot_normal in content:
    content = content.replace(old_boxplot_normal, new_boxplot_normal)
    fixes_applied += 1
    print("Fixed 2: Boxplot normal mode")
else:
    print("WARNING: Could not find boxplot normal mode code")

# ============================================================
# FIX 3: update_multi_wafer_distribution - Independent mode
# ============================================================
old_dist_indep = '''            # Parse the parameter
            if selected_param.startswith("BIN"):
                param_column = "bin"
                param_name = "Bin"
            else:
                test_key = selected_param.split(":")[0].strip()
                if test_key.startswith("test_"):
                    param_column = int(test_key.replace("test_", ""))
                else:
                    try:
                        param_column = int(test_key)
                    except ValueError:
                        param_column = "bin"
                # Extract simplified parameter name (without group/number)
                full_name = selected_param.split(":")[-1].strip() if ":" in selected_param else selected_param
                param_name = simplify_param_name(full_name)

            if param_column not in df.columns:
                continue'''

new_dist_indep = '''            # Parse the parameter
            if selected_param.startswith("BIN"):
                param_column = "bin"
                param_name = "Bin"
            else:
                test_key = selected_param.split(":")[0].strip()
                if test_key.startswith("test_"):
                    test_num = int(test_key.replace("test_", ""))
                else:
                    try:
                        test_num = int(test_key)
                    except ValueError:
                        test_num = None
                        param_column = "bin"

                if test_num is not None:
                    # Use helper function to find correct column
                    param_column = _find_param_column(df, test_num, multi_wafer_test_params)

                # Extract simplified parameter name (without group/number)
                full_name = selected_param.split(":")[-1].strip() if ":" in selected_param else selected_param
                param_name = simplify_param_name(full_name)

            if param_column not in df.columns:
                continue'''

if old_dist_indep in content:
    content = content.replace(old_dist_indep, new_dist_indep)
    fixes_applied += 1
    print("Fixed 3: Distribution independent mode")
else:
    print("WARNING: Could not find distribution independent mode code")

# ============================================================
# FIX 4: update_multi_wafer_distribution - Normal mode
# ============================================================
# First, let me find the normal mode section in distribution
# Read current content to find the pattern

# Look for the normal mode in distribution function
old_dist_normal = '''        # Normal mode: all wafers use the same parameter
        selected = multi_wafer_param_combobox.get()

        if not selected:
            print("No parameter selected for distribution")
            if multi_wafer_distribution_canvas:
                multi_wafer_distribution_canvas.get_tk_widget().destroy()
                multi_wafer_distribution_canvas = None
            return

        # Parse parameter selection
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
            param_label = simplify_param_name(full_name)'''

new_dist_normal = '''        # Normal mode: all wafers use the same parameter
        selected = multi_wafer_param_combobox.get()

        if not selected:
            print("No parameter selected for distribution")
            if multi_wafer_distribution_canvas:
                multi_wafer_distribution_canvas.get_tk_widget().destroy()
                multi_wafer_distribution_canvas = None
            return

        # Parse parameter selection
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
                param_column = test_num'''

if old_dist_normal in content:
    content = content.replace(old_dist_normal, new_dist_normal)
    fixes_applied += 1
    print("Fixed 4: Distribution normal mode")
else:
    print("WARNING: Could not find distribution normal mode code")
    # Try to find it manually
    if "update_multi_wafer_distribution" in content:
        print("  Function exists, searching for pattern...")

# Write back
with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nTotal fixes applied: {fixes_applied}/4")
print("Done!")
