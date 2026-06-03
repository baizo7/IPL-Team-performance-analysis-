import os
import textwrap

with open('legacy_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# lines 84 to 216 (0-indexed: 83 to 216)
block_start = 83 # @st.cache_data
block_end = 217 # return df + empty line

extracted_block = lines[block_start:block_end]
dedented_block = []
for line in extracted_block:
    if line.startswith("    "):
        dedented_block.append(line[4:])
    else:
        dedented_block.append(line)

# remove from original
new_lines = lines[:block_start] + lines[block_end:]

# insert before def render_legacy(): (which is at line 13, 0-indexed 12)
insert_idx = 12

final_lines = new_lines[:insert_idx] + dedented_block + ["\n"] + new_lines[insert_idx:]

with open('legacy_app.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("Fixed legacy_app.py")
