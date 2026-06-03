import bpy
import sys
import os

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

blend_file = sys.argv[-2]
export_path = sys.argv[-1]

print(f"Loading {blend_file}...")
bpy.ops.wm.open_mainfile(filepath=blend_file)

# We need to optimize the scene heavily
print("Optimizing scene...")

# 1. Remove hidden objects, cameras, and lights
for obj in bpy.context.scene.objects:
    if obj.type in ('CAMERA', 'LIGHT') or obj.hide_viewport or obj.hide_render:
        bpy.data.objects.remove(obj, do_unlink=True)

# 2. Apply decimate modifier to all meshes to reduce poly count
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        # Select object
        bpy.context.view_layer.objects.active = obj
        
        # Add Decimate modifier
        mod = obj.modifiers.new(name='Decimate', type='DECIMATE')
        mod.ratio = 0.1 # Reduce by 90%
        
        # Apply modifier
        bpy.ops.object.modifier_apply(modifier=mod.name)

# 3. Export to GLB
print(f"Exporting to {export_path}...")
bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format='GLB',
    export_texture_dir='textures',
    export_materials='EXPORT',
    export_colors=True,
    export_cameras=False,
    export_lights=False,
    export_apply=True
)

print("Done!")
