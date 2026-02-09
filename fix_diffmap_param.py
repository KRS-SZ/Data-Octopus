#!/usr/bin/env python3
"""Fix Diffmap parameter selection - after selecting group, auto-update display"""

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix the on_diffmap_group_selected function
old_code = '''    # Update the diffmap parameter combobox
    diffmap_param_combobox["values"] = param_options
    if param_options:
        diffmap_param_combobox.current(0)

def update_diffmap_group_and_param_combobox():'''

new_code = '''    # Update the diffmap parameter combobox
    diffmap_param_combobox["values"] = param_options
    if param_options:
        diffmap_param_combobox.current(0)

    # Trigger display update after parameter selection
    update_diffmap_display()

def update_diffmap_group_and_param_combobox():'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("Fixed on_diffmap_group_selected to call update_diffmap_display()")
else:
    print("Could not find old_code - trying alternative fix")

with open(r'C:\Users\szenklarz\Desktop\VS_Folder\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
