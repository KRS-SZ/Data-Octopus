"""
Script to analyze DC Test groups and subgroups in STDF file
"""
import os
import sys
from collections import defaultdict
import re

# Try to import Semi_ATE.STDF
try:
    from Semi_ATE.STDF import records_from_file
    STDF_MODULE = True
    print("Using Semi_ATE.STDF")
except ImportError:
    STDF_MODULE = False
    print("Semi_ATE.STDF not available")

# Create log file
log_file = r"c:\Users\szenklarz\Desktop\VS_Folder\dc_test_groups.log"
log = open(log_file, 'w', encoding='utf-8')

def print_log(msg=""):
    """Print to console and log file"""
    print(msg)
    log.write(msg + "\n")
    log.flush()

# Get file path from command line or use default
if len(sys.argv) > 1:
    stdf_path = sys.argv[1]
else:
    # Look for STDF files
    possible_dirs = [
        r"C:/Users/szenklarz/Downloads/TESTDATA/STDDatalog",
        r"C:/Users/szenklarz/Downloads",
        r"C:/Users/szenklarz/Desktop",
    ]

    stdf_path = None
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith(('.stdf', '.std'))]
            if files:
                stdf_path = os.path.join(dir_path, files[0])
                break

if not stdf_path:
    print_log("No STDF file found.")
    log.close()
    exit(1)

print_log(f"Analyzing STDF file: {stdf_path}\n")

if not STDF_MODULE:
    print_log("Error: Semi_ATE.STDF module not available. Cannot parse STDF file.")
    log.close()
    exit(1)

# Collect DC Test information
dc_tests = defaultdict(lambda: defaultdict(list))
all_tests = defaultdict(list)
test_by_num = {}
dc_test_records = []

print_log("Reading STDF records...\n")

record_count = 0
with open(stdf_path, "rb") as f:
    records_gen = records_from_file(f)

    for i, record in enumerate(records_gen):
        record_count += 1
        rec_type = type(record).__name__

        # Extract test information from PTR (Parametric Test Record)
        if rec_type == "PTR":
            try:
                test_num = record.TEST_NUM if hasattr(record, "TEST_NUM") else record.get_value("TEST_NUM")
                test_name = record.TEST_TXT if hasattr(record, "TEST_TXT") else record.get_value("TEST_TXT")

                if test_num is not None and test_name:
                    test_by_num[test_num] = test_name

                    # Look for DC Test entries
                    if test_name and "DC" in test_name.upper():
                        dc_test_records.append({
                            'test_num': test_num,
                            'test_name': test_name,
                            'record': record
                        })

                        # Extract subgroups from test name
                        # Common patterns: GROUP_SUBGROUP or GROUP-SUBGROUP or GROUP::SUBGROUP
                        parts = test_name.split('_')
                        if len(parts) >= 2:
                            group = parts[0]
                            subgroup = '_'.join(parts[1:])
                            dc_tests[group][subgroup].append((test_num, test_name))
                        else:
                            dc_tests['UNGROUPED'][test_name].append((test_num, test_name))

                    all_tests[test_name].append(test_num)

            except Exception as e:
                pass

        if i > 1000000:  # Process large number of records
            break

print_log(f"Total records processed: {record_count}\n")
print_log("=" * 80)
print_log(f"DC TEST RECORDS FOUND: {len(dc_test_records)}\n")
print_log("=" * 80)

# Display DC Test groups and subgroups
print_log("\nDC TEST GROUPS AND SUBGROUPS:")
print_log("=" * 80)

for group, subgroups in sorted(dc_tests.items()):
    print_log(f"\nGroup '{group}': {sum(len(v) for v in subgroups.values())} tests total")
    print_log("-" * 40)

    for subgroup, tests in sorted(subgroups.items(), key=lambda x: -len(x[1])):
        print_log(f"\n  Subgroup '{subgroup}': {len(tests)} tests")
        for test_num, test_name in sorted(tests):
            print_log(f"    [{test_num}] {test_name}")

# Detailed analysis of DC Test structure
print_log("\n" + "=" * 80)
print_log("DETAILED DC TEST ANALYSIS")
print_log("=" * 80)

dc_test_names = [rec['test_name'] for rec in dc_test_records]
print_log(f"\nTotal unique DC Tests: {len(set(dc_test_names))}")

# Extract all unique prefixes from DC tests
prefixes = set()
for test_name in dc_test_names:
    # Try different separators
    for sep in ['_', '-', '::']:
        if sep in test_name:
            prefix = test_name.split(sep)[0]
            prefixes.add(prefix)
            break

print_log(f"\nUnique prefixes in DC Tests: {sorted(prefixes)}\n")

# Group by prefix
prefix_groups = defaultdict(list)
for test_name in dc_test_names:
    for sep in ['_', '-', '::']:
        if sep in test_name:
            prefix = test_name.split(sep)[0]
            prefix_groups[prefix].append(test_name)
            break
    else:
        prefix_groups['NO_SEPARATOR'].append(test_name)

print_log("DC Tests grouped by prefix:")
print_log("-" * 40)
for prefix in sorted(prefix_groups.keys(), key=lambda x: -len(prefix_groups[x])):
    tests = prefix_groups[prefix]
    print_log(f"\nPrefix '{prefix}': {len(tests)} tests")
    for test in sorted(set(tests))[:10]:
        print_log(f"  - {test}")
    if len(set(tests)) > 10:
        print_log(f"  ... and {len(set(tests)) - 10} more")

# Summary
print_log("\n" + "=" * 80)
print_log("SUMMARY")
print_log("=" * 80)
print_log(f"Total DC Test records found: {len(dc_test_records)}")
print_log(f"Unique DC Test names: {len(set(dc_test_names))}")
print_log(f"Main groups found: {len(dc_tests)}")
print_log(f"Total subgroups: {sum(len(subgroups) for subgroups in dc_tests.values())}")

log.close()
print_log(f"\nAnalysis complete. Results saved to: {log_file}")
