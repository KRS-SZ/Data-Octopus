"""
Script to analyze datafile and identify all groups for measurement values
"""
import os
import sys
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Create a log file to capture output
log_file = r"c:\Users\szenklarz\Desktop\VS_Folder\analysis_output.log"
log = open(log_file, 'w', encoding='utf-8')

def print_log(msg=""):
    """Print to both console and log file"""
    print(msg)
    log.write(msg + "\n")
    log.flush()

# Get file path from command line argument or use default
if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    # Look for any CSV or Excel files in common locations
    possible_paths = [
        r"C:/Users/szenklarz/Downloads/TESTDATA/STDDatalog",
        r"C:/Users/szenklarz/Downloads",
        r"C:/Users/szenklarz/Desktop",
    ]

    file_path = None
    for dir_path in possible_paths:
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith(('.csv', '.xlsx', '.xls', '.parquet'))]
            if files:
                file_path = os.path.join(dir_path, files[0])
                break

    if not file_path:
        print_log("No file found and no file path provided.")
        print_log("Usage: python analyze_groups.py <path_to_file>")
        log.close()
        exit(1)

print_log(f"Analyzing file: {file_path}\n")

print_log(f"Loading file: {file_path}\n")

# Load the datafile
try:
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.parquet'):
        df = pd.read_parquet(file_path)
    else:
        df = pd.read_csv(file_path)  # Try CSV by default
except Exception as e:
    print_log(f"Error loading file: {e}")
    log.close()
    exit(1)

print_log("=" * 80)
print_log(f"DATAFILE SHAPE: {df.shape} (rows, columns)")
print_log("=" * 80)
print_log(f"\nColumn names:\n{df.columns.tolist()}\n")

# Display first few rows
print_log("=" * 80)
print_log("FIRST 5 ROWS:")
print_log("=" * 80)
print_log(df.head().to_string())

# Look for potential group columns (common naming patterns)
print_log("\n" + "=" * 80)
print_log("ANALYZING FOR GROUP COLUMNS")
print_log("=" * 80)

group_columns = []
potential_group_cols = ['group', 'Group', 'GROUP', 'test_group', 'TEST_GROUP',
                        'category', 'Category', 'CATEGORY', 'type', 'Type', 'TYPE',
                        'prefix', 'Prefix', 'PREFIX', 'name', 'Name', 'NAME',
                        'test_name', 'TEST_NAME', 'TEST_TXT', 'test_txt']

for col in potential_group_cols:
    if col in df.columns:
        group_columns.append(col)
        print_log(f"\nFound potential group column: '{col}'")
        print_log(f"  Unique values: {df[col].nunique()}")
        print_log(f"  Values: {df[col].unique()[:20].tolist()}")

# Analyze all string columns for groups
print_log("\n" + "=" * 80)
print_log("ALL STRING COLUMNS (potential groups):")
print_log("=" * 80)

for col in df.columns:
    if df[col].dtype == 'object':  # String columns
        unique_count = df[col].nunique()
        if unique_count > 1 and unique_count < 1000:  # Reasonable group size
            print_log(f"\n'{col}':")
            print_log(f"  Unique values: {unique_count}")
            if unique_count <= 50:
                print_log(f"  Values: {df[col].unique().tolist()}")
            else:
                print_log(f"  Sample values: {df[col].unique()[:20].tolist()}")

# Try to extract groups from test names if available
print_log("\n" + "=" * 80)
print_log("EXTRACTING GROUPS FROM TEST NAMES")
print_log("=" * 80)

test_name_cols = [col for col in df.columns if 'test' in col.lower() or 'name' in col.lower()]

for col in test_name_cols:
    if df[col].dtype == 'object':
        print_log(f"\nAnalyzing column: '{col}'")
        groups_found = defaultdict(list)

        for test_name in df[col].dropna().unique():
            test_name_str = str(test_name)
            # Try different separators
            for sep in ['_', '-', '.', '::']:
                if sep in test_name_str:
                    prefix = test_name_str.split(sep)[0]
                    groups_found[prefix].append(test_name_str)
                    break
            else:
                # If no separator found, use first character
                groups_found[test_name_str[0]].append(test_name_str)

        print_log(f"\nGroups extracted (by prefix):")
        for prefix, tests in sorted(groups_found.items(), key=lambda x: -len(x[1])):
            print_log(f"\n  Group '{prefix}': {len(tests)} tests")
            for test in tests[:5]:
                print_log(f"    - {test}")
            if len(tests) > 5:
                print_log(f"    ... and {len(tests) - 5} more")

# Print measurement columns
print_log("\n" + "=" * 80)
print_log("MEASUREMENT VALUE COLUMNS (numeric):")
print_log("=" * 80)

numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
print_log(f"\nNumeric columns ({len(numeric_cols)}):")
for col in numeric_cols[:30]:
    print_log(f"  - {col}")
if len(numeric_cols) > 30:
    print_log(f"  ... and {len(numeric_cols) - 30} more")

# Summary
print_log("\n" + "=" * 80)
print_log("SUMMARY")
print_log("=" * 80)
print_log(f"Total rows: {len(df)}")
print_log(f"Total columns: {len(df.columns)}")
print_log(f"Group-like columns found: {group_columns}")
print_log(f"Numeric columns: {len(numeric_cols)}")
print_log(f"String columns: {len([col for col in df.columns if df[col].dtype == 'object'])}")

log.close()
