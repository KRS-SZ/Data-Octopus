"""
Script to analyze DTR records and TEST NAMES in STDF file and find all group patterns
"""
import os
import re
from collections import defaultdict

# Try to import Semi_ATE.STDF
try:
    from Semi_ATE.STDF import records_from_file
    STDF_MODULE = True
    print("Using Semi_ATE.STDF")
except ImportError:
    STDF_MODULE = False
    print("Semi_ATE.STDF not available")

# Path to STDF file
stdf_dir = r"C:/Users/szenklarz/Downloads/TESTDATA/STDDatalog"
stdf_files = [f for f in os.listdir(stdf_dir) if f.endswith(('.stdf', '.std'))]

if not stdf_files:
    print("No STDF files found")
    exit(1)

stdf_path = os.path.join(stdf_dir, stdf_files[0])
print(f"Analyzing: {stdf_path}\n")

# Collect test names from PTR records
test_names = {}
test_name_prefixes = defaultdict(list)

with open(stdf_path, "rb") as f:
    records_gen = records_from_file(f)

    for i, record in enumerate(records_gen):
        rec_type = type(record).__name__

        if rec_type == "PTR":
            try:
                if hasattr(record, "TEST_NUM"):
                    test_num = record.TEST_NUM
                    test_name = record.TEST_TXT if hasattr(record, "TEST_TXT") else None
                else:
                    test_num = record.get_value("TEST_NUM")
                    test_name = record.get_value("TEST_TXT")

                if test_num is not None and test_name and test_num not in test_names:
                    test_names[test_num] = test_name

                    # Extract prefix (potential group) from test name
                    # Pattern: Look for common prefix before first underscore or specific patterns
                    parts = test_name.split('_')
                    if len(parts) >= 2:
                        prefix = parts[0]
                        test_name_prefixes[prefix].append((test_num, test_name))

            except Exception as e:
                pass

        if i > 500000:  # Process more records to get all test names
            break

print("=" * 60)
print(f"TOTAL UNIQUE TEST NAMES: {len(test_names)}")
print("=" * 60)

print("\n" + "=" * 60)
print("TEST NAME PREFIXES (potential groups)")
print("=" * 60)
for prefix, tests in sorted(test_name_prefixes.items(), key=lambda x: -len(x[1])):
    print(f"\n{prefix} ({len(tests)} tests):")
    for test_num, test_name in tests[:5]:  # Show first 5 tests per group
        print(f"  {test_num}: {test_name}")
    if len(tests) > 5:
        print(f"  ... and {len(tests) - 5} more")

print("\n" + "=" * 60)
print("FIRST 50 TEST NAMES")
print("=" * 60)
for i, (test_num, test_name) in enumerate(sorted(test_names.items())[:50]):
    print(f"  {test_num}: {test_name}")
