"""
PigaBid Crystal Auction - Blender Scene Generator
Creates a procedural floating gem sculpture and exports as GLB.
Run with: blender --background --python scene_create.py
"""

import bpy
import math
import os

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "public", "gem_scene.glb")

os.makedirs(os.path.join(OUTPUT_DIR, "public"), exist_ok=True)

# ── Reset scene ──────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for mat in bpy.data.materials:
    bpy.data.materials.remove(mat)


# ── Helper: create PBR material ──────────────────────────────────────────────
def make_material(name, base_color, metallic=0.0, roughness=0.1,
                  emission_color=None, emission_strength=0.0, alpha=1.0,
                  transmission=0.0, ior=1.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = 'BLEND' if alpha < 1.0 or transmission > 0 else 'OPAQUE'
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if hasattr(bsdf.inputs.get("Transmission"), "default_value"):
        bsdf.inputs["Transmission"].default_value = transmission
    if hasattr(bsdf.inputs.get("IOR"), "default_value"):
        bsdf.inputs["IOR"].default_value = ior
    if emission_color:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


# ── Gem definitions ──────────────────────────────────────────────────────────
# Central hero gem: deep sapphire icosphere
def add_hero_gem():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "HeroGem"
    # Squash slightly to look like a cut gem
    obj.scale = (1.0, 1.0, 0.65)
    bpy.ops.object.transform_apply(scale=True)
    # Flat shading = faceted gem look
    bpy.ops.object.shade_flat()
    mat = make_material(
        "SapphireGem",
        base_color=(0.05, 0.15, 0.8),
        metallic=0.0,
        roughness=0.05,
        transmission=0.85,
        ior=1.77,
        emission_color=(0.1, 0.3, 1.0),
        emission_strength=0.4,
    )
    obj.data.materials.append(mat)
    return obj


# Orbiting gem: sharp octahedron style
def add_gem(name, location, scale, color, emission_color, metallic=0.0,
            roughness=0.08, transmission=0.7):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_flat()
    mat = make_material(
        name + "Mat",
        base_color=color,
        metallic=metallic,
        roughness=roughness,
        transmission=transmission,
        ior=1.65,
        emission_color=emission_color,
        emission_strength=0.6,
    )
    obj.data.materials.append(mat)
    return obj


# Ring of 8 gems orbiting hero gem
ORBIT_GEMS = [
    # (name,           x,    y,    z,    sx,  sy,  sz,   color,              emission)
    ("Ruby",          2.2,  0.0,  0.3,  0.28, 0.28, 0.42, (0.9, 0.05, 0.05), (1.0, 0.2, 0.1)),
    ("Emerald",      -2.2,  0.0, -0.2,  0.24, 0.24, 0.38, (0.05, 0.8, 0.2),  (0.1, 1.0, 0.3)),
    ("Amethyst",      0.0,  2.2,  0.4,  0.22, 0.22, 0.35, (0.6, 0.1, 0.9),   (0.7, 0.2, 1.0)),
    ("Topaz",         0.0, -2.2, -0.1,  0.26, 0.26, 0.40, (1.0, 0.8, 0.0),   (1.0, 0.9, 0.1)),
    ("Aquamarine",    1.6,  1.6,  0.6,  0.20, 0.20, 0.32, (0.2, 0.9, 0.9),   (0.2, 0.9, 1.0)),
    ("Garnet",       -1.6,  1.6, -0.4,  0.18, 0.18, 0.28, (0.85, 0.1, 0.3),  (1.0, 0.1, 0.3)),
    ("Citrine",      -1.6, -1.6,  0.5,  0.22, 0.22, 0.34, (1.0, 0.6, 0.1),   (1.0, 0.7, 0.2)),
    ("Tanzanite",     1.6, -1.6, -0.3,  0.20, 0.20, 0.30, (0.3, 0.2, 0.8),   (0.4, 0.3, 1.0)),
]

hero = add_hero_gem()
orbit_objects = []
for gdata in ORBIT_GEMS:
    name, x, y, z, sx, sy, sz, col, em = gdata
    obj = add_gem(name, (x, y, z), (sx, sy, sz), col, em)
    orbit_objects.append(obj)

# ── Floating particle crystals (small decorative shards) ─────────────────────
import random
random.seed(42)
for i in range(20):
    angle = random.uniform(0, math.pi * 2)
    r = random.uniform(0.8, 3.8)
    x = math.cos(angle) * r
    y = math.sin(angle) * r
    z = random.uniform(-1.2, 1.2)
    s = random.uniform(0.04, 0.12)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(x, y, z))
    shard = bpy.context.active_object
    shard.name = f"Shard_{i:02d}"
    shard.scale = (s, s, s * 1.6)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_flat()
    # Random rotation
    shard.rotation_euler = (
        random.uniform(0, math.pi),
        random.uniform(0, math.pi),
        random.uniform(0, math.pi),
    )
    r_hue = random.choice([
        ((0.8, 0.8, 1.0), (0.7, 0.7, 1.0)),  # ice-blue
        ((1.0, 0.9, 0.5), (1.0, 0.8, 0.2)),  # gold
        ((0.6, 1.0, 0.8), (0.2, 1.0, 0.6)),  # mint
    ])
    mat = make_material(
        f"Shard_{i:02d}Mat",
        base_color=r_hue[0],
        metallic=0.3,
        roughness=0.05,
        emission_color=r_hue[1],
        emission_strength=0.8,
        transmission=0.5,
    )
    shard.data.materials.append(mat)


# ── Pedestal ring ─────────────────────────────────────────────────────────────
bpy.ops.mesh.primitive_torus_add(
    major_radius=3.5, minor_radius=0.06,
    major_segments=80, minor_segments=16,
    location=(0, 0, -1.0)
)
ring = bpy.context.active_object
ring.name = "PedestalRing"
ring_mat = make_material(
    "GoldRing",
    base_color=(1.0, 0.78, 0.1),
    metallic=1.0,
    roughness=0.1,
    emission_color=(1.0, 0.85, 0.3),
    emission_strength=0.3,
)
ring.data.materials.append(ring_mat)

# Inner ring
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.4, minor_radius=0.04,
    major_segments=64, minor_segments=12,
    location=(0, 0, 0)
)
inner_ring = bpy.context.active_object
inner_ring.name = "InnerRing"
inner_ring.data.materials.append(ring_mat)


# ── Lighting ──────────────────────────────────────────────────────────────────
# Warm key light
bpy.ops.object.light_add(type='POINT', location=(4, -3, 5))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 800
key.data.color = (1.0, 0.9, 0.7)
key.data.shadow_soft_size = 2.0

# Cool fill from opposite side
bpy.ops.object.light_add(type='POINT', location=(-4, 3, 2))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 300
fill.data.color = (0.4, 0.6, 1.0)

# Rim light below
bpy.ops.object.light_add(type='POINT', location=(0, 0, -3))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 200
rim.data.color = (0.8, 0.4, 1.0)

# Top ambient
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "SunLight"
sun.data.energy = 1.5
sun.data.color = (0.9, 0.9, 1.0)
sun.rotation_euler = (math.radians(30), 0, math.radians(45))


# ── Camera ────────────────────────────────────────────────────────────────────
bpy.ops.object.camera_add(location=(6, -6, 4))
cam = bpy.context.active_object
cam.name = "Camera"
cam.rotation_euler = (math.radians(60), 0, math.radians(45))
bpy.context.scene.camera = cam


# ── Export GLB ────────────────────────────────────────────────────────────────
print(f"\n[BlenderMCP] Exporting scene to: {OUTPUT_GLB}")
bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB,
    export_format='GLB',
    export_apply=True,
    export_materials='EXPORT',
    export_lights=False,    # Three.js adds its own lighting
    export_cameras=False,   # Three.js manages camera
    export_extras=True,
)
print(f"[BlenderMCP] ✓ Export complete: {OUTPUT_GLB}")
