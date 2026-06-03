import hashlib
import re

with open('legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all uuid.uuid4().hex[:8] patterns with deterministic hashes based on nearby context
# Pattern: div_id = f"something_{uuid.uuid4().hex[:8]}"
# Replace with: div_id = f"something_{hashlib.md5(title.encode()).hexdigest()[:8]}"

# For each line with uuid.uuid4, we need to figure out what variable to hash.
# The render functions all have a 'title' parameter, so we can use that.

replacements = [
    # render_pitch_map - line 1656
    ('div_id = f"pitch_{uuid.uuid4().hex[:8]}"',
     'div_id = f"pitch_{hashlib.md5(title.encode()).hexdigest()[:8]}"'),
    
    # render_wagon_wheel - line 2197-2198
    ('div_id = f"wagon_wheel_{uuid.uuid4().hex[:8]}"\n        unique_id = uuid.uuid4().hex[:8]',
     'div_id = f"wagon_wheel_{hashlib.md5(title.encode()).hexdigest()[:8]}"\n        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]'),
    
    # render_stumps_view - line 3878-3879
    ('div_id = f"stumps_view_{uuid.uuid4().hex[:8]}"\n        unique_id = uuid.uuid4().hex[:8]',
     'div_id = f"stumps_view_{hashlib.md5(title.encode()).hexdigest()[:8]}"\n        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]'),
    
    # render_advanced_pitch_viz - line 4451
    ('div_id = f"advanced_pitch_{uuid.uuid4().hex[:8]}"',
     'div_id = f"advanced_pitch_{hashlib.md5(title.encode()).hexdigest()[:8]}"'),
    
    # render_player_stats_cards - line 4704
    ('div_id = f"player_stats_{uuid.uuid4().hex[:8]}"',
     'div_id = f"player_stats_{hashlib.md5(team_name.encode()).hexdigest()[:8]}"'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f"Replaced: {old[:50]}...")
    else:
        # Try with \r\n
        old_crlf = old.replace('\n', '\r\n')
        if old_crlf in content:
            new_crlf = new.replace('\n', '\r\n')
            content = content.replace(old_crlf, new_crlf)
            count += 1
            print(f"Replaced (CRLF): {old[:50]}...")
        else:
            print(f"NOT FOUND: {old[:50]}...")

# Add hashlib import at the top if not already there
if 'import hashlib' not in content:
    content = content.replace('import uuid', 'import uuid\nimport hashlib', 1)
    print("Added hashlib import")

with open('legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone! Fixed {count} UUID locations.")
