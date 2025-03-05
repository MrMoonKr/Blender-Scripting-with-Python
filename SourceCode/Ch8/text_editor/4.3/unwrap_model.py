# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch8 of the book "Blender Scripting with Python" by Isabel Lupiani.
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

__all__ = (
    "generate_and_seam_cube",
    "unwrap_model",
    "export_uv_layout",
    "set_image_in_uv_editors"
    )

import bpy
import bmesh
import sys
import os

script_dir = ''
if bpy.context.space_data and bpy.context.space_data.text:
    script_filepath = bpy.context.space_data.text.filepath
    if script_filepath:
        script_dir = os.path.dirname(script_filepath)
        if not script_dir in sys.path:
            sys.path.append(script_dir)

from create_and_save_images import create_image_data_block
from split_screen_area import split_screen_area
from uv_settings import get_uv_editor
from view_fit import get_context_override

def generate_and_seam_cube(context, obj_name="cube_obj", side_length=1, center=(0, 0, 0)):
    if bpy.data.meshes.find("cube_mesh") >= 0:
        bpy.data.meshes.remove(bpy.data.meshes["cube_mesh"])
        
    cube_mesh = bpy.data.meshes.new(name="cube_mesh")
    
    if bpy.data.objects.find(obj_name) < 0:
        cube_obj = bpy.data.objects.new(name=obj_name, object_data=cube_mesh)
        context.collection.objects.link(cube_obj)
    else:
        cube_obj = bpy.data.objects[obj_name]
        cube_obj.data = cube_mesh
        if context.collection.objects.find(cube_obj) < 0:
            context.collection.objects.link(cube_obj)
    
    for o in context.view_layer.objects:
        o.select_set(False)     
    context.view_layer.objects.active = cube_obj
    cube_obj.select_set(True)
    
    viewport_context_override, override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.object.mode_set(mode='EDIT')
    else:
        return

    bm = bmesh.from_edit_mesh(cube_mesh)
    half_side_len = side_length/2
    bottom_z = center[2] - half_side_len
    top_z = center[2] + half_side_len
    # verts of the bottom face, counterclockwise.
    #         3  2
    #         0  1
    verts = []
    verts.append(bm.verts.new((center[0]+half_side_len, center[1]-half_side_len, bottom_z)))
    verts.append(bm.verts.new((center[0]+half_side_len, center[1]+half_side_len, bottom_z)))
    verts.append(bm.verts.new((center[0]-half_side_len, center[1]+half_side_len, bottom_z)))
    verts.append(bm.verts.new((center[0]-half_side_len, center[1]-half_side_len, bottom_z)))
    bottom_face = verts[0:4]
    # verts of the top face, counterclockwise.
    #         7  6
    #         4  5
    verts.append(bm.verts.new((center[0]+half_side_len, center[1]-half_side_len, top_z)))
    verts.append(bm.verts.new((center[0]+half_side_len, center[1]+half_side_len, top_z)))
    verts.append(bm.verts.new((center[0]-half_side_len, center[1]+half_side_len, top_z)))
    verts.append(bm.verts.new((center[0]-half_side_len, center[1]-half_side_len, top_z)))
    top_face = verts[4:]

    # Fill in the faces.
    #         3 e2 2
    #        e3    e1
    #         0 e0 1
    bm.faces.new(verts[0:4])
    #         7 e6 6
    #        e7    e5
    #         4 e4 5
    bm.faces.new(verts[4:])
    for i in range(3):
        #         4+i       5+i
        #        e9+i      e8+i
        #         0+i       1+i
        bm.faces.new([verts[i], verts[i+1], verts[i+1+4], verts[i+4]])
    bm.faces.new([verts[3], verts[0], verts[4], verts[7]])
    bm.edges.ensure_lookup_table()

    # edges 1, 3, 5, 6, 7, 9, 10
    edge_indices_to_select = [1, 3, 5, 6, 7, 9, 10]
    for idx in edge_indices_to_select:
        bm.edges[idx].select = True
    bpy.ops.mesh.mark_seam(clear=False)

    viewport_context_override, override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            
def create_material(obj, material_name, image):
    if bpy.data.materials.find(material_name) < 0:
        bpy.data.materials.new(material_name)
    material = bpy.data.materials[material_name]
    obj.data.materials.append(material)
    obj.active_material_index = obj.data.materials.find(material.name)
    material.use_nodes = True

    tcm_nodes = material.node_tree.nodes
    bsdf_index = tcm_nodes.find('Principled BSDF')
    node_bsdf = tcm_nodes.new(type='ShaderNodeBsdfPrincipled') if bsdf_index < 0 else tcm_nodes[bsdf_index]
    
    node_texture = tcm_nodes.new('ShaderNodeTexImage')
    node_texture.image = image
    
    node_output = tcm_nodes.new(type='ShaderNodeOutputMaterial')    
    tcm_links = material.node_tree.links
    tcm_links.new(node_texture.outputs['Color'], node_bsdf.inputs['Base Color'])
    tcm_links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
    
def config_viewport_materials(context):
    for a in context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.shading.show_backface_culling = True
                    s.shading.type = 'MATERIAL'
                    
def set_image_in_uv_editors(context, image):
    override = context.copy()
    found_uv_editor = False
    for area in context.screen.areas:
        if area.type=='IMAGE_EDITOR' and area.ui_type=='UV':
            for space in area.spaces:
                if space.type=='IMAGE_EDITOR':
                    space.image = image
                    space.uv_editor.use_live_unwrap = True
                    space.uv_editor.show_stretch = True
                    found_uv_editor = True
                    
                    override['area'] = area
                    for region in override['area'].regions:
                        if region.type=='WINDOW':
                            override['region'] = region
                            break
                    with bpy.context.temp_override(**override):
                        bpy.ops.image.view_all(fit_view=True)         
        
    if not found_uv_editor:
        uv_editor_area = split_screen_area(context, 'VERTICAL', 0.5, 'IMAGE_EDITOR', 'UV', False)
        override['area'] = uv_editor_area
        for s in uv_editor_area.spaces:
            if s.type=='IMAGE_EDITOR':
                s.image = image
                s.uv_editor.use_live_unwrap = True
                s.uv_editor.show_stretch = True
                break
            
        for region in override['area'].regions:
            if region.type=='WINDOW':
                override['region'] = region
                break
        with bpy.context.temp_override(**override):
            bpy.ops.image.view_all(fit_view=True)

# This function assumes that the model has already been seamed.
def unwrap_model(context, model_name, num_min_stretch_iterations, uv_map_name="uv_map", image_block_name="uv_grid_texture"):
    if context.scene.objects.find(model_name) < 0:
        return
    obj = context.scene.objects[model_name]
    if obj.type != 'MESH':
        return
    
    obj_mesh = obj.data
    if not obj_mesh:
        return False
    
    if len(uv_map_name) < 1:
        uv_map_name = "uv_map"
    
    uv_map_index = obj_mesh.uv_layers.find(uv_map_name)
    if uv_map_index < 0:
        obj_mesh.uv_layers.new(name=uv_map_name)
        uv_map_index = obj_mesh.uv_layers.find(uv_map_name)
        
    uv_map = obj_mesh.uv_layers[uv_map_name]
    obj_mesh.uv_layers.active_index = uv_map_index

    for o in context.view_layer.objects:
        o.select_set(False)           
    context.view_layer.objects.active = obj
    obj.select_set(True)
    
    viewport_context_override, override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.object.mode_set(mode='EDIT')
    else:
        return
            
    viewport_context_override, override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            bpy.ops.uv.minimize_stretch(iterations=num_min_stretch_iterations)
    else:
        return
        
    uv_grid = None
    if bpy.data.images.find(image_block_name) < 0 or not bpy.data.images[image_block_name].has_data:
        uv_grid, _ = create_image_data_block(context, image_block_name, image_type='UV_GRID', color=(0, 0, 0, 1), image_filepath='', display_image=False)
    else:
        uv_grid = bpy.data.images[image_block_name]
        
    set_image_in_uv_editors(context, uv_grid)
    create_material(obj, model_name + "_material", uv_grid)
    bpy.ops.object.material_slot_assign()
    config_viewport_materials(context)
    
    viewport_context_override, override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.view3d.view_selected(use_all_regions=False)
    
def export_uv_layout(context, name, dirpath):
    image_editor_context_override, override_successful = get_context_override(context, 'IMAGE_EDITOR', 'WINDOW')
    if override_successful:
        image_filepath = dirpath + '\\' + name + '.png'
        with bpy.context.temp_override(**image_editor_context_override):    
            bpy.ops.uv.export_layout(filepath=image_filepath, check_existing=True, \
                export_all=False, modified=False, mode='PNG', size=(1024, 1024), opacity=0.25)

if __name__ == "__main__":
    # Generate a cube with name 'test_cube', side length of 2, that centers at the origin, and mark seams on it.
    generate_and_seam_cube(bpy.context, "test_cube", 2, (0, 0, 0))

    # Unwrap the test_cube object with 2 minimize stretch iterations.
    unwrap_model(bpy.context, "test_cube", 2, "tc_uv_map", "uv_grid_texture")

    # Test exporting the current active layout to file.
    export_uv_layout(bpy.context, "uv_layout", script_dir)