# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch4 of the book "Blender Scripting with Python" by Isabel Lupiani.
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
else:
    from . import creating_and_editing_mesh_objs

import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector

# ========== Utility Methods ====================================================        
def create_loop_stack(context, name="loop_stack_bmesh", location=(0, 0, 0), radius=1, num_loops=2, loop_segments=16, level_height=1):
    bm, obj = creating_and_editing_mesh_objs.get_placeholder_mesh_obj_and_bm(context, name, location)
    
    for i in range(num_loops):
        bmesh.ops.create_circle(bm, cap_ends=False, segments=loop_segments, radius=radius)
    bm.verts.ensure_lookup_table()
    for i in range(1, num_loops, 1):
        for v in bm.verts[loop_segments*i:loop_segments*(i+1)]:
            v.co[2] += level_height*i
    bm.edges.ensure_lookup_table()
    
    return bm, obj

def create_cylinder_bmesh(context, name="cylinder_bmesh", location=(0, 0, 0), radius1=1.5, radius2=1, segments=16, height=1):
    bm, obj = creating_and_editing_mesh_objs.get_placeholder_mesh_obj_and_bm(context, name, location)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius1, radius2=radius2, depth=height)
    bm.edges.ensure_lookup_table()  
    return bm, obj
    
def create_cone_bmesh(context, name="cone_bmesh", location=(0, 0, 0), radius=1, segments=16, height=1):
    bm, obj = create_cylinder_bmesh(context, name=name, location=location, radius1=radius, radius2=0, segments=segments, height=height)
    return bm, obj

def create_cube_bmesh(context, name="cube_bmesh", location=(0, 0, 0), size=2.0):
    bm, obj = creating_and_editing_mesh_objs.get_placeholder_mesh_obj_and_bm(context, name, location)
    bmesh.ops.create_cube(bm, size=size) 
    bm.edges.ensure_lookup_table()  
    return bm, obj

def create_grid_bmesh(context, name="grid_bmesh", location=(0, 0, 0), x_segments=5, y_segments=10, size=10):
    bm, obj = creating_and_editing_mesh_objs.get_placeholder_mesh_obj_and_bm(context, name, location)
    bmesh.ops.create_grid(bm, x_segments=x_segments, y_segments=y_segments, size=size) 
    bm.edges.ensure_lookup_table()  
    return bm, obj    

def create_circle_bmesh(context, name="circle_bmesh", location=(0, 0, 0), radius=1, segments=16):
    bm, obj = creating_and_editing_mesh_objs.get_placeholder_mesh_obj_and_bm(context, name, location)
    bmesh.ops.create_circle(bm, cap_ends=True, segments=segments, radius=radius)
    bm.edges.ensure_lookup_table()
    return bm, obj    

def create_cylinder_by_extrusion(context, name="cylinder_extruded_bmesh", location=(0, 0, 0), radius=1, segments=8, num_levels=2, level_height=2):
    bm, obj = create_circle_bmesh(bpy.context, name=name, location=location, radius=radius, segments=segments)
    bm.verts.ensure_lookup_table()
    seed_edge = bm.edges[0]
    direction = Vector((0, 0, level_height))
    scale = Vector((1, 1, 1))
    loops = []
    for i in range(num_levels):
        new_loop = extrude_edge_loop_copy_move(bm, seed_edge, direction, scale)
        seed_edge = new_loop[0]
        loops.append(new_loop)
    bm.edges.ensure_lookup_table()
    return bm, obj, loops

#========= Test Creating Primitive Shapes ========================================================
def test_create_loop_stack(context):
    _, obj = create_loop_stack(context, name="loop_stack_bmesh", location=(0, 0, 0), radius=1.5, num_loops=5, loop_segments=8, level_height=2)
    bmesh.update_edit_mesh(obj.data)

def test_create_cylinder_bmesh(context):
    _, obj = create_cylinder_bmesh(context, name="cylinder_bmesh", location=(0, 0, 4), radius1=1, radius2=0.5, segments=8, height=2)
    bmesh.update_edit_mesh(obj.data)
    
def test_create_cone_bmesh(context):
    _, obj = create_cone_bmesh(context, name="cone_bmesh", location=(6, -6, 1), radius=1, segments=12, height=2)
    bmesh.update_edit_mesh(obj.data)
    
def test_create_cube_bmesh(context):
    _, obj = create_cube_bmesh(context, name="cube_bmesh", location=(-6, -6, 4), size=2.0)
    bmesh.update_edit_mesh(obj.data)

def test_create_grid_bmesh(context):
    _, obj = create_grid_bmesh(context, name="grid_bmesh", location=(0, 0, 0), x_segments=5, y_segments=10, size=10)
    bmesh.update_edit_mesh(obj.data)

def test_create_circle_bmesh(context):
    _, obj = create_circle_bmesh(context, name="circle_bmesh", location=(0, 0, 0), radius=1, segments=12)
    bmesh.update_edit_mesh(obj.data)

def test_create_cylinder_by_extrusion_bmesh(context):
    _, obj, _ = create_cylinder_by_extrusion(context, name="cylinder_extruded_bmesh", location=(6, 6, 0), radius=3, segments=16, num_levels=2, level_height=2)
    bmesh.update_edit_mesh(obj.data)

#========= Selecting Edge Loops =============================
def get_edge_loops(bm, ref_edges, select_rings=False):
    loops = []
    for re in ref_edges:
        bpy.ops.mesh.select_all(action='DESELECT')
        re.select = True
        bpy.ops.mesh.loop_multi_select(ring=select_rings)
        this_loop = []
        for e in bm.edges:
            if e.select:
                this_loop.append(e)
        loops.append(this_loop)
    bpy.ops.mesh.select_all(action='DESELECT')
    return loops

def select_edge_loops(bm, ref_edges, select_rings=False):
    bpy.ops.mesh.select_all(action='DESELECT')
    for re in ref_edges:
        re.select = True
    bpy.ops.mesh.loop_multi_select(ring=select_rings)
    
    loop_edges = []  
    for e in bm.edges:
        if e.select:
            loop_edges.append(e)
        
    return loop_edges

#========= Bridging Edge Loops ===============================
def bridge_loops_bmesh(bm, ref_edges):
    edges_in_loops = select_edge_loops(bm, ref_edges)
    new_geom = bmesh.ops.bridge_loops(bm, edges=edges_in_loops)
    return new_geom['faces'], new_geom['edges']

def bridge_loops_bpy(bm, ref_edges):
    select_edge_loops(bm, ref_edges)
    bpy.ops.mesh.bridge_edge_loops()

#============ Test Selecting and Bridging Loops ==========================================
def test_select_edge_loops(context):
    context.tool_settings.mesh_select_mode = [False, True, False]
    bm, obj = create_cylinder_bmesh(context, name="test_select_edge_loops", location=(0, 0, 0), radius1=1.5, radius2=1, segments=8, height=2)
    loop_edges = select_edge_loops(bm, ref_edges=[bm.edges[0], bm.edges[1]], select_rings=False)
    bmesh.update_edit_mesh(obj.data)

def test_get_edge_loops(context):
    bm, obj = create_cylinder_bmesh(context, name="test_get_edge_loops", location=(0, 0, 0), radius1=1.5, radius2=1, segments=8, height=2)
    bmesh.update_edit_mesh(obj.data)
    loops = get_edge_loops(bm, ref_edges = [bm.edges[0], bm.edges[1]], select_rings = False)
    for l in loops:
        print(str([e.index for e in l]))

def test_bridge_loops_bmesh(context):
    num_loops = 5
    num_segments = 8
    bm, stack_obj = create_loop_stack(context, name="test_bridge_loops_bmesh", location=(0, 0, 0), radius=1.5, num_loops=num_loops, loop_segments=num_segments, level_height=2)
    loop_ref_edges = [bm.edges[i*num_segments] for i in range(num_loops)]
    
    resulted_faces, resulted_edges = bridge_loops_bmesh(bm, loop_ref_edges)
    bmesh.update_edit_mesh(stack_obj.data)

def test_bridge_loops_bpy(context):
    num_loops = 5
    num_segments = 8
    bm, stack_obj = create_loop_stack(context, name="test_bridge_loops_bpy", location=(0, 4, 0), radius=1.5, num_loops=num_loops, loop_segments=num_segments, level_height=2)
    loop_ref_edges = [bm.edges[i*num_segments] for i in range(num_loops)]
    
    bridge_loops_bpy(bm, loop_ref_edges)
    bmesh.update_edit_mesh(stack_obj.data)

#========= Extrusion =========================================
def extrude_edge_loop_copy_move(bm, ref_edge, direction, scale_factor):
    select_edge_loops(bm, [ref_edge], select_rings=False)
    bpy.ops.mesh.duplicate()
    bpy.ops.transform.translate(value=direction)
    bpy.ops.transform.resize(value=scale_factor)

    new_edge_loop = []
    for e in bm.edges:
        if e.select:
            new_edge_loop.append(e)

    bridge_loops_bpy(bm, [new_edge_loop[0], ref_edge])
    for e in new_edge_loop:
        e.select = False
    return new_edge_loop

def loop_extrude_region_move(bm, ref_edge, direction):
    select_edge_loops(bm, [ref_edge], select_rings = False)
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": direction})

#============== Test Extrusion ========================================================== 
def test_extrude_before(context):
    segments = 8    
    bm, obj = create_circle_bmesh(context, name="test_extrude_before", location=(0, -3, 0), radius=1, segments=8)
    bmesh.update_edit_mesh(obj.data)
           
def test_extrude_edge_loop_copy_move(context):
    bm, obj = create_circle_bmesh(context, name="test_extrude_copy_move", location=(0, 3, 0), radius=1, segments=8)
    ref_edge = bm.edges[0]
    num_extrusions = 5

    for i in range(num_extrusions):
        direction = Vector((1, 1, 1.5)) if i % 2 == 0 else Vector((1, -1, 1.5))
        scale = Vector((0.75, 0.5, 1)) if i % 2 == 0 else Vector((0.5, 0.75, 1))
        new_loop = extrude_edge_loop_copy_move(bm, ref_edge, direction, scale)
        ref_edge = new_loop[0]
    
    bmesh.update_edit_mesh(obj.data)
    
def test_loop_extrude_region_move(context):
    bm, obj = create_circle_bmesh(context, name="test_loop_extrude_region_move", location=(0, 0, 0), radius=1, segments=8)
    loop_extrude_region_move(bm, ref_edge=bm.edges[0], direction=Vector((1, 1, 2)))
    bmesh.update_edit_mesh(obj.data)

def test_extrude(context):
    test_extrude_before(context)
    test_extrude_edge_loop_copy_move(context)
    test_loop_extrude_region_move(context)
    
#========== Loop Cuts and Slides ====================================
def offset_loop_slide(context, bm, ref_edge, slide_distance):
    select_edge_loops(bm, [ref_edge], select_rings=False)
    context_override = get_context_override(context, 'VIEW_3D', 'WINDOW')
    with bpy.context.temp_override(**context_override):
        bpy.ops.mesh.offset_edge_loops_slide(TRANSFORM_OT_edge_slide={"value": slide_distance})

def get_context_override(context, area_type, region_type):
    override = context.copy()
    for area in override['screen'].areas:
        if area.type == area_type: # e.g. 'VIEW_3D' for viewport, 'IMAGE_EDITOR' for UV/Image Editor, etc.
            override['area'] = area
            break
    for region in override['area'].regions:
        if region.type == region_type: # e.g. 'WINDOW'
            override['region'] = region
            break
    return override
    
def loop_cut_slide(context, ref_edge, num_cuts, slide_distance):     
    # reference_edge is the edge closest and perpendicular to where the loop cut should be made.
    context_override = get_context_override(context, 'VIEW_3D', 'WINDOW')
    with bpy.context.temp_override(**context_override):
        bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts":num_cuts, "object_index":0, "edge_index":ref_edge.index, \
        "mesh_select_mode_init":(False, True, False)}, TRANSFORM_OT_edge_slide={"value":slide_distance})


#=========== Test Loop Cuts + Slides =========================================================

def test_offset_loop_slide(context):
    num_loops = 5
    num_segments = 8
    bm, stack_obj = create_loop_stack(context, name="test_offset_loop_slide", location=(0, 0, 0), radius=1.5, num_loops=num_loops, loop_segments=num_segments, level_height=2)
    loop_ref_edges = [bm.edges[i*num_segments] for i in range(num_loops)]
    resulted_faces, resulted_edges = bridge_loops_bmesh(bm, loop_ref_edges)
    bmesh.update_edit_mesh(stack_obj.data)
    
    offset_loop_slide(context, bm, ref_edge = loop_ref_edges[1], slide_distance=0.2)
    bmesh.update_edit_mesh(stack_obj.data)
    context.view_layer.update()

def test_loop_cut_slide(context):
    num_segments = 8
    bm, obj, loops = create_cylinder_by_extrusion(context, name="test_loop_cut_slide", location=(0, -7, 0), radius=2, segments=num_segments, num_levels=3)
    bpy.ops.mesh.select_all(action='DESELECT')

    ref_edge_index = loops[1][-1].index + 1
    loop_cut_slide(context, ref_edge=bm.edges[ref_edge_index], num_cuts=2, slide_distance=0.3)
    bmesh.update_edit_mesh(obj.data)
  
def test_offset_and_cut_loop_slide(context):
    test_offset_loop_slide(context)
    test_loop_cut_slide(context)

#========== Merging Verts ===========================================
def merge_verts_bpy(target_map, merge_type='CENTER'):
    for v_from, v_to in target_map.items():
        bpy.ops.mesh.select_all(action='DESELECT')
        v_from.select = True
        v_to.select = True
    
        # type is: 'CENTER', 'CURSOR', or 'COLLAPSE'
        bpy.ops.mesh.merge(type = merge_type)

#=========== Test Merging Verts=============================================================
def test_merge_verts_before(context):
    bm, obj = create_grid_bmesh(context, name="test_merge_verts_before", location=(5, 0, 0), x_segments=5, y_segments=6, size=3)
    bmesh.update_edit_mesh(obj.data)
    context.tool_settings.mesh_select_mode = [True, False, False]
    
def test_merge_verts_bmesh(context):
    bm, obj = create_grid_bmesh(context, name="test_merge_verts_bmesh", location=(-5, 0, 0), x_segments=5, y_segments=6, size=3)
    
    context.tool_settings.mesh_select_mode = [True, False, False]
    bm.verts.ensure_lookup_table()
    from_list = [bm.verts[i] for i in range(1, 4, 1)]
    to_list = [bm.verts[i] for i in range(6, 9, 1)]
    target_map = {from_list[i]: to_list[i] for i in range(3)}
    bmesh.ops.weld_verts(bm, targetmap=target_map)
    bmesh.update_edit_mesh(obj.data)

def test_merge_verts_bpy(context):
    bm, obj = create_grid_bmesh(bpy.context, name="test_merge_verts_bpy", location=(0, -10, 0), x_segments=5, y_segments=6, size=3)
    bmesh.update_edit_mesh(obj.data)
    context.tool_settings.mesh_select_mode = [True, False, False]
    
    bm.verts.ensure_lookup_table()
    from_list = [bm.verts[i] for i in range(1, 4, 1)]
    to_list = [bm.verts[i] for i in range(6, 9, 1)]
    target_map = {from_list[i]: to_list[i] for i in range(3)}
    merge_verts_bpy(target_map, merge_type='CENTER')
    bmesh.update_edit_mesh(obj.data)

#============================================================================================
        
def merge_vert_loops(bm, vert_loop_source, vert_loop_target):
    tm = dict()
    len_source = len(vert_loop_source)
    len_target = len(vert_loop_target)
    vert_loop_merged = vert_loop_target if len_source > len_target else vert_loop_source
    tm_length = min(len_source, len_target)
    
    for i in range(tm_length):
        tm[vert_loop_source[i]] = vert_loop_target[i]

    bmesh.ops.weld_verts(bm, targetmap = tm)
    vert_loop_merged[0:tm_length] = vert_loop_target
    resulted_indices = [v.index for v in vert_loop_merged]
    return vert_loop_merged, resulted_indices

#========== Test Merging Loops ===========================================================
def test_merge_vert_loops(context):
    segments = 8    
    bm, obj = create_cylinder_bmesh(context, name="merged_vert_loops_bottom_to_top", location=(0, 4, 0), radius1=1, radius2=0.5, segments=segments, height=2)
    context.tool_settings.mesh_select_mode = [True, False, False]
    bm.verts.ensure_lookup_table()
    even_verts = [bm.verts[i] for i in range(0, segments*2, 2)]
    odd_verts = [bm.verts[i] for i in range(1, segments*2, 2)]
    merge_vert_loops(bm, even_verts, odd_verts)
    bmesh.update_edit_mesh(obj.data)
    
def test_merge_vert_loops_reverse(context):
    segments = 8    
    bm, obj = create_cylinder_bmesh(context, name="merged_vert_loops_top_to_bottom", location=(0, -4, 0), radius1=1, radius2=0.5, segments=segments, height=2)
    context.tool_settings.mesh_select_mode = [True, False, False]
    bm.verts.ensure_lookup_table()
    even_verts = [bm.verts[i] for i in range(0, segments*2, 2)]
    odd_verts = [bm.verts[i] for i in range(1, segments*2, 2)]
    merge_vert_loops(bm, odd_verts, even_verts)
    bmesh.update_edit_mesh(obj.data)
    
# ========== Ripping Verts ======================================================
def rip_verts_bmesh(rip_map, offset):
    ripped_verts = []
    for f, rip_corner_index in rip_map.items():
        v = bmesh.utils.face_vert_separate(f, f.verts[rip_corner_index])
        v.co += offset
        ripped_verts.append(v)
    return ripped_verts

#=========== Test Ripping =============================================================
def test_rip_verts_before(context):
    bm, obj = create_grid_bmesh(context, name="test_rip_verts_before", location=(7, 0, 0), x_segments=10, y_segments=4, size=6)
    bmesh.update_edit_mesh(obj.data)
    context.tool_settings.mesh_select_mode = [True, False, False]
    
def test_rip_verts_bmesh(context):
    bm, obj = create_grid_bmesh(context, name="test_rip_verts_bmesh", location=(-7, 0, 0), x_segments=10, y_segments=4, size=6)

    context.tool_settings.mesh_select_mode = [False, False, True]
    bm.faces.ensure_lookup_table()
    offset = Vector((1, 0.75, 1.25))
    rip_map = {bm.faces[10]: 0, bm.faces[12]: 1, bm.faces[14]: 2, bm.faces[16]: 3}
    rip_verts_bmesh(rip_map, offset)
    
    bmesh.update_edit_mesh(obj.data)
    
def test_rip_verts(context):
    test_rip_verts_before(context)
    test_rip_verts_bmesh(context)

# ========== Insetting + Beveling ===============================================
def bevel_bpy(edge_list, offset=0.15, segments=2, loop_slide=True, vertex_only=False):
    bpy.ops.mesh.select_all(action='DESELECT')
    for e in edge_list:
        e.select = True
    bpy.ops.mesh.bevel(offset=offset, segments=segments, loop_slide=loop_slide, affect='VERTICES' if vertex_only else 'EDGES')

#========= Test Insettting ========================================================
def test_inset_bmesh_before(context):
    bm, obj = create_grid_bmesh(context, name="test_inset_before", location=(7, 0, 2), x_segments=10, y_segments=4, size=6)
    context.tool_settings.mesh_select_mode = [False, False, True]
    bmesh.update_edit_mesh(obj.data)
    
def test_inset_bmesh(context):
    bm, obj = create_grid_bmesh(context, name="test_inset_indv", location=(-7, 0, 2), x_segments=10, y_segments=4, size=6)
    context.tool_settings.mesh_select_mode = [False, False, True]
    
    bm.faces.ensure_lookup_table()
    faces_indv_out = bm.faces[0:4]
    faces_indv_in = bm.faces[6:10]
    faces_region_out = bm.faces[20:24]
    faces_region_in = bm.faces[26:30]

    bmesh.ops.inset_individual(bm, faces=faces_indv_out, thickness=0.3, depth=0.5)
    bmesh.ops.inset_individual(bm, faces=faces_indv_in, thickness=0.5, depth=-0.2)
    bmesh.ops.inset_region(bm, faces=faces_region_out, thickness=0.3, depth=0.5)
    bmesh.ops.inset_region(bm, faces=faces_region_in, thickness=0.5, depth=-0.2)
    bmesh.update_edit_mesh(obj.data)

def test_inset(context):
    test_inset_bmesh_before(context)
    test_inset_bmesh(context)

#=========== Test Beveling ===================================================
def test_bevel_bpy_before(context):
    bm, obj = create_cube_bmesh(context, name="test_bevel_bpy_before", location=(0, 12, 3), size=5.0)
    bmesh.update_edit_mesh(obj.data)   
    
def test_bevel_bpy_edges(context):
    bm, obj = create_cube_bmesh(context, name="test_bevel_bpy_edges", location=(0, 6, 3), size=5.0)
    bm.edges.ensure_lookup_table()
    bevel_bpy(edge_list=bm.edges[0:4], offset=1.0, segments=5, loop_slide=True, vertex_only=False)
    bmesh.update_edit_mesh(obj.data)
    
def test_bevel_bpy_edges_no_slide(context):
    bm, obj = create_cube_bmesh(context, name="test_bevel_bpy_edges_no_slide", location=(0, 0, 3), size=5.0)

    bm.edges.ensure_lookup_table()
    bevel_bpy(edge_list=bm.edges[0:4], offset=1.0, segments=5, loop_slide=False, vertex_only=False)

    bmesh.update_edit_mesh(obj.data)
    
def test_bevel_bpy_vertex_only(context):
    bm, obj = create_cube_bmesh(context, name="test_bevel_bpy_vertex_only", location=(0, -6, 3), size=5.0)

    bm.edges.ensure_lookup_table()
    bevel_bpy(edge_list=bm.edges[0:4], offset=1.0, segments=5, loop_slide=False, vertex_only=True)

    bmesh.update_edit_mesh(obj.data)
    
def test_bevel_bpy(context):
    test_bevel_bpy_before(context)
    test_bevel_bpy_edges(context)
    test_bevel_bpy_edges_no_slide(context)
    test_bevel_bpy_vertex_only(context)
       
# ========== Remove Loose Verts =================================================       
def remove_loose_verts(bm):
    verts_to_remove = []
    for v in bm.verts:
        if len(v.link_edges) == 0:
            verts_to_remove.append(v)
            
    for v in verts_to_remove:
        bm.verts.remove(v)

#=========== Test Removing Loose Verts ====================================
def gen_mesh_with_loose_verts(context, location, name):
    bm, obj = create_cube_bmesh(context, name=name, location=location, size=4.0)
    existing_verts = list(bm.verts)
    for v in existing_verts:
        bm.verts.new(v.co + Vector((-1, -1, 1)))
    bm.verts.ensure_lookup_table()  
    return bm, obj

def test_remove_loose_verts_before(context):
    _, obj_before = gen_mesh_with_loose_verts(context, (0, 4, 0), "test_remove_loose_verts_before")
    context.tool_settings.mesh_select_mode = [True, False, False]
    bmesh.update_edit_mesh(obj_before.data)

def test_remove_loose_verts_after(context):    
    bm_after, obj_after = gen_mesh_with_loose_verts(context, (0, -4, 0), "test_remove_loose_verts_after")
    remove_loose_verts(bm_after)
    context.tool_settings.mesh_select_mode = [True, False, False]
    bmesh.update_edit_mesh(obj_after.data)
    
def test_remove_loose_verts(context):
    test_remove_loose_verts_before(context)
    test_remove_loose_verts_after(context)

#=========== Test Joining + Splitting Faces =============================================================
def test_join_split_faces_before(context):
    bm, obj = create_grid_bmesh(context, name="test_join_faces_before", location=(7, 0, 0), x_segments=10, y_segments=4, size=6)
    bmesh.update_edit_mesh(obj.data)
    context.tool_settings.mesh_select_mode = [True, False, True]  
    
def test_join_split_faces_bmesh(context):
    bm, obj = create_grid_bmesh(context, name="test_join_faces_bmesh", location=(-7, 0, 0), x_segments=10, y_segments=4, size=6)

    context.tool_settings.mesh_select_mode = [True, False, True]
    bm.faces.ensure_lookup_table()
    faces_to_join = bm.faces[0:9]
    face_to_split = bm.faces[13]
    joined_face = bmesh.utils.face_join(faces_to_join)
    split_face = bmesh.utils.face_split(face_to_split, face_to_split.verts[0], face_to_split.verts[2])
    joined_face.select = True
    split_face[0].select = True
    
    bmesh.update_edit_mesh(obj.data)

def test_join_split_faces(context):
    test_join_split_faces_before(context)
    test_join_split_faces_bmesh(context)

#=========== Configure Viewport Debug Settings ============================================================
def config_viewport_debug_settings(context, show_indices, show_vn, show_fn, normals_length, shading_type):
    for a in context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.shading.type = shading_type
                    s.overlay.show_extra_indices = show_indices
                    s.overlay.show_vertex_normals = show_vn
                    s.overlay.show_face_normals = show_fn
                    s.overlay.normals_length = normals_length
                    return

#========= Operators for Running Test Functions ===========================================================    
class TestCreatePrimitivesBMeshOperator(Operator):
    bl_idname = "mesh.test_create_primitives_bmesh"
    bl_label = "Test Create Primitives BMesh"
    """Test Create Primitives BMesh"""

    def execute(self, context):
        test_create_loop_stack(context)
        test_create_cylinder_bmesh(context)
        test_create_cone_bmesh(context)
        test_create_cube_bmesh(context)
        test_create_grid_bmesh(context)        
        test_create_circle_bmesh(context)
        test_create_cylinder_by_extrusion_bmesh(context)
        self.report({'INFO'}, "Test Create Primitives BMesh")
        return {'FINISHED'}
    
class TestExtrusionOperator(Operator):
    bl_idname = "mesh.test_extrusion"
    bl_label = "Test Extrusion"
    """Test Extrusion"""

    def execute(self, context):
        test_extrude(context)
        self.report({'INFO'}, "Test Extrusion")
        return {'FINISHED'}
    
class TestBridgeLoopsOperator(Operator):
    bl_idname = "mesh.test_bridge_loops"
    bl_label = "Test Bridge Loops"
    """Test Bridge Loops"""

    def execute(self, context):
        test_bridge_loops_bmesh(context)
        test_bridge_loops_bpy(context)
        self.report({'INFO'}, "Test Bridge Loops")
        return {'FINISHED'}
    
class TestOffsetCutLoopSlideOperator(Operator):
    bl_idname = "mesh.test_offset_cut_loop_slide"
    bl_label = "Test Offset Cut Loop Slide"
    """Test Offset Cut Loop Slide"""

    def execute(self, context):
        test_offset_and_cut_loop_slide(context)
        self.report({'INFO'}, "Test Offset Cut Loop Slide")
        return {'FINISHED'}
    
class TestMergeVertsOperator(Operator):
    bl_idname = "mesh.test_merge_verts"
    bl_label = "Test Merge Verts"
    """Test Merge Verts"""

    def execute(self, context):
        test_merge_verts_before(context)
        test_merge_verts_bmesh(context)
        test_merge_verts_bpy(context)
        self.report({'INFO'}, "Test Merge Verts")
        return {'FINISHED'}
    
class TestMergeLoopsOperator(Operator):
    bl_idname = "mesh.test_merge_loops"
    bl_label = "Test Merge Loops"
    """Test Merge Loops"""

    def execute(self, context):
        test_merge_vert_loops(context)
        test_merge_vert_loops_reverse(context)
        self.report({'INFO'}, "Test Merge Loops")
        return {'FINISHED'}
    
class TestRipVertsOperator(Operator):
    bl_idname = "mesh.test_rip_verts"
    bl_label = "Test Rip Verts"
    """Test Rip Verts"""

    def execute(self, context):
        test_rip_verts(context)
        self.report({'INFO'}, "Test Rip Verts")
        return {'FINISHED'}
    
class TestInsetOperator(Operator):
    bl_idname = "mesh.test_inset"
    bl_label = "Test Inset"
    """Test Inset"""

    def execute(self, context):
        test_inset(context)
        self.report({'INFO'}, "Test Inset")
        return {'FINISHED'}
    
class TestBevelOperator(Operator):
    bl_idname = "mesh.test_bevel"
    bl_label = "Test Bevel"
    """Test Bevel"""

    def execute(self, context):
        test_bevel_bpy(context)
        self.report({'INFO'}, "Test Bevel")
        return {'FINISHED'}
    
class TestJoinSplitFacesOperator(Operator):
    bl_idname = "mesh.test_join_split_faces"
    bl_label = "Test Join Split Faces"
    """Test Join Split Faces"""

    def execute(self, context):
        test_join_split_faces(context)
        self.report({'INFO'}, "Test Join Split Faces")
        return {'FINISHED'}
    
class TestRemoveLooseVertsOperator(Operator):
    bl_idname = "mesh.test_remove_loose_verts"
    bl_label = "Test Remove Loose Verts"
    """Test Remove Loose Verts"""

    def execute(self, context):
        test_remove_loose_verts(context)
        self.report({'INFO'}, "Test Remove Loose Verts")
        return {'FINISHED'}
    
class TestGetandSelectEdgeLoopsOperator(Operator):
    bl_idname = "mesh.test_get_and_select_edge_loops"
    bl_label = "Test Get and Select Edge Loops"
    """Test Get and Select Edge Loops"""

    def execute(self, context):
        test_get_edge_loops(context)
        test_select_edge_loops(context)
        self.report({'INFO'}, "Test Get and Select Edge Loops")
        return {'FINISHED'}
    
class ConfigViewportDebugSettings(Operator):
    bl_idname = "view3d.config_viewport_debug_settings"
    bl_label = "Config Viewport Debug Settings"
    """Config Viewport Debug Settings"""

    def execute(self, context):
        config_viewport_debug_settings(bpy.context, True, True, True, 1.0, 'WIREFRAME')
        self.report({'INFO'}, "Config Viewport Debug Settings")
        return {'FINISHED'}
    
#========= Operators for Running Test Functions ===========================================================

class TEST_MESH_EDITING_PT_ToolPanel(bpy.types.Panel):
    bl_idname = "TEST_MESH_EDITING_PT_ToolPanel"
    bl_label = "TEST_MESH_EDITING"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    """Test Mesh Editing Tool"""

    def draw(self, context):
        layout = self.layout
        col0 = layout.column()
        box0 = col0.box()

        box0.label(text="Test Create Primitives with BMesh")
        box0.operator("mesh.test_create_primitives_bmesh", icon='MESH_DATA')

        box0.label(text="Test Extrusion")
        box0.operator("mesh.test_extrusion", icon='MESH_DATA')

        box0.label(text="Test Bridge Edge Loops")
        box0.operator("mesh.test_bridge_loops", icon='MESH_DATA')

        box0.label(text="Test Offset & Cut Loop Slide")
        box0.operator("mesh.test_offset_cut_loop_slide", icon='MESH_DATA')

        box0.label(text="Test Merge")
        box0.operator("mesh.test_merge_verts", icon='MESH_DATA')
        box0.operator("mesh.test_merge_loops", icon='MESH_DATA')

        box0.label(text="Test Rip Verts")
        box0.operator("mesh.test_rip_verts", icon='MESH_DATA')

        box0.label(text="Test Inset & Bevel")
        box0.operator("mesh.test_inset", icon='MESH_DATA')
        box0.operator("mesh.test_bevel", icon='MESH_DATA')

        box0.label(text="Test Join & Split Faces")
        box0.operator("mesh.test_join_split_faces", icon='MESH_DATA')        

        box0.label(text="Test Remove Loose Verts")
        box0.operator("mesh.test_remove_loose_verts", icon='MESH_DATA')

        box0.label(text="Test Get and Select Edge Loops")
        box0.operator("mesh.test_get_and_select_edge_loops", icon='MESH_DATA')

        box0.label(text="Config Viewport Debug Settings")
        box0.operator("view3d.config_viewport_debug_settings", icon='MESH_DATA')

classes = [TestCreatePrimitivesBMeshOperator,
           TestBridgeLoopsOperator,
           TestExtrusionOperator,
           TestOffsetCutLoopSlideOperator,
           TestMergeVertsOperator,
           TestMergeLoopsOperator,
           TestRipVertsOperator,
           TestInsetOperator,
           TestBevelOperator,
           TestJoinSplitFacesOperator,
           TestRemoveLooseVertsOperator,
           TestGetandSelectEdgeLoopsOperator,
           ConfigViewportDebugSettings,
           TEST_MESH_EDITING_PT_ToolPanel]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()