import codecs
import re

with codecs.open('legacy_app.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Disable Shadows
content = content.replace('renderer.shadowMap.enabled = true;', 'renderer.shadowMap.enabled = false;')
content = content.replace('renderer.shadowMap.type = THREE.PCFSoftShadowMap;', '// renderer.shadowMap.type = THREE.PCFSoftShadowMap;')
content = content.replace('sunLight.castShadow = true;', 'sunLight.castShadow = false;')
content = content.replace('marker.castShadow = true;', 'marker.castShadow = false;')
content = content.replace('pole.castShadow = true;', 'pole.castShadow = false;')

# 2. Reduce Grass Iterations
content = content.replace('for (let i = 0; i < 5000; i++) {', 'for (let i = 0; i < 500; i++) {')

# 3. Reduce Torus Segments
# Matches: new THREE.TorusGeometry(..., ..., 16, 100) or 64 etc
content = re.sub(r'new THREE\.TorusGeometry\(([^,]+),\s*([^,]+),\s*16,\s*(100|64)\)', r'new THREE.TorusGeometry(\1, \2, 8, 32)', content)

# 4. Reduce Cylinder Segments
content = re.sub(r'new THREE\.CylinderGeometry\(([^,]+),\s*([^,]+),\s*([^,]+),\s*(16|32)\)', r'new THREE.CylinderGeometry(\1, \2, \3, 8)', content)

with codecs.open('legacy_app.py', 'w', 'utf-8') as f:
    f.write(content)
print("Optimization complete.")
