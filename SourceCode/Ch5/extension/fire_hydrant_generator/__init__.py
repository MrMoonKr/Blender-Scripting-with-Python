# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch5 of the book "Blender Scripting with Python" by Isabel Lupiani.
#    Copyright (C) 2024  Isabel Lupiani, Apress.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

if "bpy" in locals():
    import importlib
    importlib.reload(creating_and_editing_mesh_objs)
    importlib.reload(mesh_editing_ops)
else:
    from . import creating_and_editing_mesh_objs, mesh_editing_ops

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator
import bmesh
from math import asin, cos, pow, radians
from mathutils import Vector

#=========== Putting It Altogether ===========================================
def gen_stylized_fire_hydrant(context, name, location=(0, 0, 0), num_cir_segments=16, pole_radius=3, num_pole_levels=3, num_dome_levels=3, \
    stylize=False, pole_bent_factor=1, dome_bent_factor=1, subsurf=False, subsurf_level=2, add_geo_for_sharp_loops=True):
    
    bm, fh_obj = creating_and_editing_mesh_objs.get_placeholder_mesh_obj_and_bm(context, name=name, location=location)
    if subsurf:
        fh_subsurf_mod = fh_obj.modifiers.new("subsurf_mod", 'SUBSURF')
        fh_subsurf_mod.levels = subsurf_level
        fh_subsurf_mod.subdivision_type = 'CATMULL_CLARK'

    ratio_base_to_pole = 1.5
    base_radius = pole_radius*ratio_base_to_pole
    base_height = pole_radius*0.5
    loops_to_add_geo = []
    
    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=num_cir_segments, radius1=base_radius, radius2=base_radius, depth=base_height)
    
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    base_ref_edges = []
    loop_cut_ref_edge = None
    for e in bm.faces[0].edges:
        if e.verts[0].co[2] == e.verts[1].co[2]:
            base_ref_edges.append(e)
        else:
            loop_cut_ref_edge = e
    
    base_loops = mesh_editing_ops.get_edge_loops(bm, base_ref_edges, select_rings=False)
    loops_to_add_geo.extend(base_loops)
    
    mesh_editing_ops.loop_cut_slide(context, loop_cut_ref_edge, num_cuts=2, slide_distance=0)
    bm.edges.ensure_lookup_table()

    for f in bm.faces:
        num_edges_selected = sum([1 if f.edges[i].select else 0 for i in range(4)])
        if num_edges_selected >=2:
            f.select = True;
    context.tool_settings.mesh_select_mode = [False, False, True]
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate = {"value": Vector((0, 0, 0))})
    bpy.ops.transform.resize(value=(1.05, 1.05, 1.0), orient_type='GLOBAL')
    bm.faces.ensure_lookup_table()
    
    if add_geo_for_sharp_loops:
        base_ridge_loop_ref_edges = []
        for f in bm.faces:
            if f.select:
                for e in f.edges:
                    if e.verts[0].co[2] == e.verts[1].co[2]:
                        base_ridge_loop_ref_edges.append(e)
                break
        bpy.ops.mesh.select_all(action='DESELECT')
        mesh_editing_ops.select_edge_loops(bm, base_ridge_loop_ref_edges, select_rings=False)
        bpy.ops.mesh.bevel(offset=0.1, segments=2, loop_slide=False)
        bpy.ops.mesh.select_all(action='DESELECT')

    context.tool_settings.mesh_select_mode = [False, True, False]
    bm.edges.ensure_lookup_table()
    top_loop_edge = base_ref_edges[0] if base_ref_edges[0].verts[0].co[2] > base_ref_edges[1].verts[0].co[2] else base_ref_edges[1]
    mesh_editing_ops.select_edge_loops(bm, [top_loop_edge], select_rings=False)

    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": Vector((0, 0, 0))})
    ratio_pole_to_base = 1 / ratio_base_to_pole
    bpy.ops.transform.resize(value=(ratio_pole_to_base, ratio_pole_to_base, 1), orient_type='GLOBAL')
        
    bm.edges.ensure_lookup_table()
    pole_bottom_loop = []
    for e in bm.edges:
        if e.select:
            pole_bottom_loop.append(e)
    ref_edge = pole_bottom_loop[0]
    loops_to_add_geo.append(pole_bottom_loop)
    
    context.tool_settings.mesh_select_mode = [False, False, True]
    edge_loops_pole_cross_sections = []
    pole_level_height = pole_radius*1.5
    face_loop_pole_bottom = []
    # Extrude the given number of pole levels, then an additional level for the cap base (which matches the base base in height).
    for i in range(num_pole_levels+1):
        z_offset = pole_level_height if i < num_pole_levels else base_height
        if stylize:            
            skew = pole_radius*0.5*pole_bent_factor
            direction = Vector((skew, skew, z_offset)) if i%2 == 0 \
                else Vector((-skew, -skew, z_offset))
            scale = Vector((0.85, 1, 1)) if i%2 == 0 else Vector((1, 0.85, 1))
        else:
            direction = Vector((0, 0, z_offset))
            scale = Vector((1, 1, 1))
        extrusion = mesh_editing_ops.extrude_edge_loop_copy_move(bm, ref_edge, direction, scale)
        edge_loops_pole_cross_sections.append(extrusion)
        ref_edge = extrusion[0]

        if i == 0:
            face_idx = 0
            for f in bm.faces:
                if f.select:
                    if face_idx%2 == 0:
                        face_loop_pole_bottom.append(f)
                    face_idx += 1
                    
        if i >= num_pole_levels-1:
            loops_to_add_geo.append(extrusion)
                    
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": Vector((0, 0, 0))})
    bpy.ops.transform.resize(value=(ratio_base_to_pole, ratio_base_to_pole, 1), orient_type='GLOBAL')
    
    bm.faces.ensure_lookup_table()
    face_loop_pole_top = []
    for f in bm.faces:
        if f.select:
            face_loop_pole_top.append(f)

    face_loops_dome = []
    face_loops_dome_cap = []
    dome_radius = pole_radius
    dome_height = pole_level_height
    dome_level_height = dome_height/num_dome_levels
    pcrt_of_sphere_for_dome = 0.75
    r_prev_level = pole_radius
    
    for i in range(num_dome_levels+4):
        if i < num_dome_levels:
            z_offset = (dome_radius/num_dome_levels)*(i+1)*pcrt_of_sphere_for_dome
            theta = asin(z_offset/pole_radius)
            r_at_level = pole_radius*cos(theta)
            
            level_scale_factor = r_at_level/r_prev_level
            scale = Vector((level_scale_factor, level_scale_factor, 1))
            
            skew = dome_radius*0.2*dome_bent_factor if stylize else 0          
            direction = Vector((skew, skew, dome_level_height)) if i%2 == 0 else Vector((-skew, -skew, dome_level_height))
        else:
            z_offset = pole_radius*0.2
            direction = Vector((0, 0, z_offset))
            scale = Vector((1, 1, 1))
        extrusion = mesh_editing_ops.extrude_edge_loop_copy_move(bm, ref_edge, direction, scale)
        edge_loops_pole_cross_sections.append(extrusion)
        ref_edge = extrusion[0]
        r_prev_level = r_at_level      
        bm.faces.ensure_lookup_table()
        
        if i < num_dome_levels:
            face_idx = 0
            for f in bm.faces:
                if f.select:
                    if face_idx%2 == 0:
                        face_loops_dome.append(f)
                    face_idx += 1
        else:
            cur_loop = []
            for f in bm.faces:
                if f.select:
                    cur_loop.append(f)
            face_loops_dome_cap.append(cur_loop)

    new_face_loops_dome_cap = []
    dome_cap_scale_factors = {1:0.8, 2:1.3, 3:0.3}
    for i in range(1, 4, 1):
        bpy.ops.mesh.select_all(action='DESELECT')
        for f in face_loops_dome_cap[i]:
            f.select = True
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": Vector((0, 0, 0))})
        scale_factor = dome_cap_scale_factors[i]
        bpy.ops.transform.resize(value=(scale_factor, scale_factor, 1), orient_type='GLOBAL')
        
        new_face_loop_this_level = []
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            if f.select:
                new_face_loop_this_level.append(f)
        new_face_loops_dome_cap.append(new_face_loop_this_level)

    bpy.ops.mesh.select_all(action='DESELECT')
    mesh_editing_ops.select_edge_loops(bm, [ref_edge], select_rings=False)
    bpy.ops.mesh.edge_collapse()

    bmesh.ops.inset_region(bm, faces=face_loop_pole_top, thickness=0.3, depth=0.1)
    bmesh.ops.inset_individual(bm, faces=face_loop_pole_bottom, thickness=0.1, depth=-0.15)
    bmesh.ops.inset_region(bm, faces=face_loops_dome, thickness=0.1, depth=-0.15)
    
    bpy.ops.mesh.select_all(action='DESELECT')
    bot_base_loop = base_loops[0] if base_loops[0][0].verts[0].co[2] < base_loops[1][0].verts[0].co[2] else base_loops[1]
    for e in bot_base_loop:
        e.select = True
    bpy.ops.mesh.edge_face_add() # Fill with n-gon
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Add extra geometry to keep certain edge loops sharp (i.e. not rounded by subsurf).
    if add_geo_for_sharp_loops:
        for l in loops_to_add_geo:
            for e in l:
                e.select = True
        bpy.ops.mesh.bevel(offset=0.1, segments=2, loop_slide=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        
        for nfldc in new_face_loops_dome_cap:
            bpy.ops.mesh.select_all(action='DESELECT')
            f0 = nfldc[0]
            nfldc_loop_ref_edges = []
            for e in f0.edges:
                if e.verts[0].co[2] == e.verts[1].co[2]:
                    nfldc_loop_ref_edges.append(e)
            mesh_editing_ops.select_edge_loops(bm, nfldc_loop_ref_edges, select_rings=False)
            bpy.ops.mesh.bevel(offset=0.1, segments=2, loop_slide=False)

        bpy.ops.mesh.select_all(action='DESELECT')
            
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.update_edit_mesh(fh_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

#========= Test Fire Hydrant Generation ======================================================
def test_gen_fire_hydrant(context):
    gen_stylized_fire_hydrant(context, "fh_default", location=(35, -14, 0))
    gen_stylized_fire_hydrant(context, "fh_no_extra_loops_subsurf", location=(21, -14, 0), subsurf=True, subsurf_level=2, add_geo_for_sharp_loops=False)
    gen_stylized_fire_hydrant(context, "fh_with_extra_loops_subsurf", location=(7, -14, 0), subsurf=True, subsurf_level=2)
    gen_stylized_fire_hydrant(context, "fh_32seg_subsurf_lvl3", location=(-7, -14, 0), num_cir_segments=32, subsurf=True, subsurf_level=3)
    gen_stylized_fire_hydrant(context, "fh_pole_lvl1", location=(-21, -14, 0), pole_radius=4, num_pole_levels=1)
    gen_stylized_fire_hydrant(context, "fh_pole_r1.5_lvl12", location=(-35, -14, 0), pole_radius=1.5, num_pole_levels=12, num_dome_levels=5)

    gen_stylized_fire_hydrant(context, "fh_stylize_defaults", location=(35, 0, 0), stylize=True)
    gen_stylized_fire_hydrant(context, "fh_stylize_subsurf", location=(21, 0, 0), stylize=True, subsurf=True)
    gen_stylized_fire_hydrant(context, "fh_stylize_no_extra_loops_pbf2.5", location=(7, 0, 0), pole_radius=5, stylize=True, subsurf=True, subsurf_level=3, \
        pole_bent_factor=2.5, dome_bent_factor=2.5, add_geo_for_sharp_loops=False)
    gen_stylized_fire_hydrant(context, "fh_stylize_pole_lvl1", location=(-7, 0, 0), pole_radius=3, num_pole_levels=1, stylize=True)
    gen_stylized_fire_hydrant(context, "fh_stylize_pr1.5_plvl10_dlvl5", location=(-21, 0, 0), pole_radius=1.5, num_pole_levels=10, num_dome_levels=5, \
        stylize=True, pole_bent_factor=1.5, dome_bent_factor=1.25)
    gen_stylized_fire_hydrant(context, "fh_stylize_pr2_plvl8_dlvl5", location=(-35, 0, 0), pole_radius=2, num_pole_levels=8, num_dome_levels=5, \
        stylize=True)

def test_gen_fh_num_segments(context):
    pole_radius = 3
    spacing = pole_radius * 1.5 * 3
    gen_stylized_fire_hydrant(context, location=(spacing, 0, 0), num_cir_segments=8, pole_radius=pole_radius)
    gen_stylized_fire_hydrant(context, location=(0, 0, 0), num_cir_segments=16, pole_radius=pole_radius)
    gen_stylized_fire_hydrant(context, location=(-spacing, 0, 0), num_cir_segments=32, pole_radius=pole_radius)

#========= Create Scean Variables for User Input =============================================
def init_scene_vars():
    bpy.types.Scene.fh_object_name = StringProperty(
        name="Object Name",
        description="Name for the fire hydrant object",
        default="fire_hydrant",
        subtype="NONE")
            
    bpy.types.Scene.num_cir_segments = bpy.props.IntProperty(
        name="Num Segments",
        description="Number of segments for the cross section",
        default=16,
        max=64,
        min=8)

    bpy.types.Scene.pole_radius= bpy.props.FloatProperty(
        name="Pole Radius",
        description="Radius of fire hydrant pole",
        default=3.0,
        max=50.0,
        min=1.0)

    bpy.types.Scene.num_pole_levels = bpy.props.IntProperty(
        name="Num Pole Levels",
        description="Number of pole levels",
        default=3,
        max=20,
        min=1)
    
    bpy.types.Scene.num_dome_levels = bpy.props.IntProperty(
        name="Num Dome Levels",
        description="Number of dome levels",
        default=3,
        max=20,
        min=1)
    
    bpy.types.Scene.subsurf = bpy.props.BoolProperty(
        name="Subsurf",
        description="Whether to add a subsurf modifier to the generated mesh",
        default=True)
    
    bpy.types.Scene.subsurf_level = bpy.props.IntProperty(
        name="Subsurf Level",
        description="Number of subsurf levels for preview/render",
        default=2,
        max=4,
        min=1)
    
    bpy.types.Scene.add_geo_for_sharp_loops = bpy.props.BoolProperty(
        name="Cut Extra Loops for Subsurf",
        description="Whether to cut extra edge loops to keep them sharp under subsurf",
        default=True)
    
    bpy.types.Scene.stylize = bpy.props.BoolProperty(
        name="Stylize?",
        description="Whether to stylize the object",
        default=False)
    
    bpy.types.Scene.pole_bent_factor = bpy.props.FloatProperty(
        name="Pole Bent Factor",
        description="Factor of how much the pole is bent",
        default=1.0,
        max=10.0,
        min=1.0)
    
    bpy.types.Scene.dome_bent_factor = bpy.props.FloatProperty(
        name="Dome Bent Factor",
        description="Factor of how much the dome is bent",
        default=1.0,
        max=10.0,
        min=1.0)

def del_scene_vars():
    del bpy.types.Scene.fh_object_name
    del bpy.types.Scene.num_cir_segments
    del bpy.types.Scene.pole_radius
    del bpy.types.Scene.num_pole_levels
    del bpy.types.Scene.stylize
    del bpy.types.Scene.subsurf_level
    del bpy.types.Scene.add_geo_for_sharp_loops
    del bpy.types.Scene.pole_bent_factor
    del bpy.types.Scene.dome_bent_factor

#========= Operators for Running Test Functions ===========================================================
class GenerateFireHydrantOperator(Operator):
    bl_idname = "mesh.generate_fire_hydrant"
    bl_label = "Generate"
    """Generate Fire Hydrant Meshes With User Input Values"""

    def execute(self, context):
        gen_stylized_fire_hydrant(context, context.scene.fh_object_name, location=context.scene.cursor.location, \
            num_cir_segments=context.scene.num_cir_segments, pole_radius=context.scene.pole_radius, \
            num_pole_levels=context.scene.num_pole_levels, num_dome_levels=context.scene.num_dome_levels, \
            stylize=context.scene.stylize, pole_bent_factor=context.scene.pole_bent_factor, \
            dome_bent_factor=context.scene.dome_bent_factor, subsurf=context.scene.subsurf, \
            subsurf_level=context.scene.subsurf_level, add_geo_for_sharp_loops=context.scene.add_geo_for_sharp_loops)
        self.report({'INFO'}, "Generate Fire Hydrant Meshes With User Input Values.")
        return {'FINISHED'}

class GenerateFireHydrantsWithPresetsOperator(Operator):
    bl_idname = "mesh.generate_fire_hydrant_with_presets"
    bl_label = "Generate With Presets"
    """Generate Fire Hydrant Meshes With Presets"""

    def execute(self, context):
        test_gen_fire_hydrant(context)
        self.report({'INFO'}, "Generate Fire Hydrant Meshes With Presets.")
        return {'FINISHED'}
    
#========= Fire Hydrant Generator Properties shelf Tool tab ================================================

class FIRE_HYDRANT_GENERATOR_PT_ToolPanel(bpy.types.Panel):
    bl_idname = "FIRE_HYDRANT_GENERATOR_PT_ToolPanel"
    bl_label = "FIRE_HYDRANT_GENERATOR"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    """Fire Hydrant Generator Tool"""
    def draw(self, context):
        layout = self.layout
        col0 = layout.column()
        box0 = col0.box()
        box0.label(text="Generation Params:", icon='TEXT')
        r = box0.row(align=True)
        r.prop(context.scene, "fh_object_name")
        r = box0.row(align=True)
        r.prop(context.scene, "num_cir_segments")
        r = box0.row(align=True)
        r.prop(context.scene, "pole_radius")
        r = box0.row(align=True)
        r.prop(context.scene, "num_pole_levels")
        r = box0.row(align=True)
        r.prop(context.scene, "num_dome_levels")
        r = box0.row(align=True)
        r.prop(context.scene, "subsurf")
        r = box0.row(align=True)
        r.prop(context.scene, "subsurf_level")
        r = box0.row(align=True)
        r.prop(context.scene, "add_geo_for_sharp_loops")
        r = box0.row(align=True)
        r.prop(context.scene, "stylize")
        r = box0.row(align=True)
        r.prop(context.scene, "pole_bent_factor")
        r = box0.row(align=True)
        r.prop(context.scene, "dome_bent_factor")
        box0.operator("mesh.generate_fire_hydrant", icon='MESH_DATA')
        
        box1 = col0.box()
        box1.label(text="Presets")
        box1.operator("mesh.generate_fire_hydrant_with_presets", icon='MESH_DATA')

classes = [GenerateFireHydrantOperator,
           GenerateFireHydrantsWithPresetsOperator,
           FIRE_HYDRANT_GENERATOR_PT_ToolPanel]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    init_scene_vars()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del_scene_vars()

if __name__ == "__main__":
    register()
