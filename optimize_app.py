import re

with open('legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix the UUID generation in render_threejs_chart to be deterministic
# This prevents Streamlit from destroying and recreating the WebGL iframes on every interaction!
content = content.replace(
    'div_id = f"chart_{uuid.uuid4().hex[:8]}"',
    'import hashlib\n        div_id = f"chart_{hashlib.md5(title.encode()).hexdigest()[:8]}"'
)

# 2. Also fix any other random data generation that might change the JSON string
# We can set a fixed random seed right inside the functions so they generate the same random data
content = content.replace(
    'def generate_pitch_map_data(df',
    'def generate_pitch_map_data(df'
)
content = content.replace(
    'rng = np.random.RandomState(42)',
    'rng = np.random.RandomState(42)' # already seeded!
)
content = content.replace(
    'np.random.seed(42)',
    'np.random.seed(42)' # already seeded!
)

with open('legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Optimized WebGL rendering by making iframe contents deterministic.")
