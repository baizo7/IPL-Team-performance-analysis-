import sys

with open('legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('width="stretch"', 'use_container_width=True')

with open('legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done reverting.")
