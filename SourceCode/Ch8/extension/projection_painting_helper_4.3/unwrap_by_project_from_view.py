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
    'set_viewport_rotation',
    'rename_uv_map',
    'unwrap_by_projecting_from_view'
    )

import bpy
import mathutils

# if "bpy" in locals():
#     import importlib
#     importlib.reload(apply_modifiers)
#     importlib.reload(create_and_save_images)
#     importlib.reload(split_screen_area)
#     importlib.reload(uv_settings)
#     importlib.reload(view_fit)
#     importlib.reload(unwrap_model)
# else:
#     from . import apply_modifiers
#     from . import create_and_save_images
#     from . import split_screen_area
#     from . import uv_settings
#     from . import view_fit
#     from . import unwrap_model

from .apply_modifiers import *
from .create_and_save_images import *
from .split_screen_area import *
from .uv_settings import *
from .view_fit import *
from .unwrap_model import create_material, config_viewport_materials, set_image_in_uv_editors

# Alternative to using bpy.ops.view3d.view_axis() to set viewport view direction, by setting viewport rotations
# directly. This method allows additional viewport properties to be set at the same time, such as view_distance.
# view_persp is ‘PERSP’, ‘ORTHO’, or ‘CAMERA’.
# Use wxyz = [0.7071067690849304, 0.7071067690849304, 0, 0] for front view, and wxyz = [0.5, 0.5, -0.5, -0.5] for left view.
def set_viewport_rotation(context, wxyz, view_persp):#, view_dist):
    for a in context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D': 
                    s.region_3d.lock_rotation = False # Ensure viewport rotation isn't locked.
                    s.region_3d.view_location = mathutils.Vector((0, 0, 0)) # And we're looking down centered at the origin.

                    s.region_3d.view_rotation.w = wxyz[0]
                    s.region_3d.view_rotation.x = wxyz[1]
                    s.region_3d.view_rotation.y = wxyz[2]
                    s.region_3d.view_rotation.z = wxyz[3]
                    s.region_3d.view_perspective = view_persp # either 'PERSP' for perspective, or 'ORTHO' or orthographic.
                    #s.region_3d.view_distance = view_dist
                    
                    s.region_3d.update()
    
def rename_uv_map(context, obj, old_name, new_name, set_active=True):
    if not obj or obj.type != 'MESH':
        return False
    
    obj_mesh = obj.data
    if not obj_mesh:
        return False
    
    if len(new_name) < 1:
        return False
    
    # Before unwrapping, check if we need to create a new UVMap entry in Properties window -> Object data -> UV Maps.
    uv_map_index = obj_mesh.uv_layers.find(old_name)
    if uv_map_index < 0:
        return False
    
    obj_mesh.uv_layers[uv_map_index].name = new_name
    if set_active:
        obj_mesh.uv_layers.active_index = uv_map_index
        
    return True

# view is 'FRONT', 'RIGHT', 'LEFT', etc.
def unwrap_by_projecting_from_view(context, obj_to_unwrap_name, view, uv_map_name, image_block_name):
    if bpy.data.objects.find(obj_to_unwrap_name) < 0:
        return False
    
    obj_to_unwrap = bpy.data.objects[obj_to_unwrap_name]
    
    if obj_to_unwrap.type != 'MESH':
        return False
    
    obj_mesh = obj_to_unwrap.data
    if not obj_mesh:
        return False
    
    if len(uv_map_name) < 1:
        uv_map_name = "uv_map"
    
    # Before unwrapping, check if we need to create a new UV Map entry in Properties window -> Object data -> UV Maps.
    uv_map_index = obj_mesh.uv_layers.find(uv_map_name)
    if uv_map_index < 0:
        obj_mesh.uv_layers.new(name=uv_map_name)
        uv_map_index = obj_mesh.uv_layers.find(uv_map_name)
        
    uv_map = obj_mesh.uv_layers[uv_map_name]
    uv_map.active_render = True
    # Make sure the right UV Map index is selected in Properties window -> Object data -> UV Maps, so the subsequent 
    # unwrap gets mapped to it.
    obj_mesh.uv_layers.active_index = uv_map_index
    
    # Before unwrapping, first we switch to Object mode and apply all modifiers (mirror, subsurf, etc.).
    # apply_all_modifiers() will set the obj_to_unwrap as the active object, select it, and deselect all other objects
    # in the 3D view.
    apply_all_modifiers(context, obj_to_unwrap)

    # Switch obj_to_unwrap in Edit mode to unwrap.
    viewport_context_override, viewport_override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if viewport_override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.object.mode_set(mode='EDIT')
            
    # Now that obj_to_unwrap is in Edit mode, select all, and use View -> Frame Selected to adjust zoom.
    viewport_context_override, viewport_override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if viewport_override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.view3d.view_selected(use_all_regions=False)
            
    # Set the viewport to the given view (e.g. 'FRONT', 'LEFT', etc with bpy.ops.view3d.view_axis().
    viewport_context_override, viewport_override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if viewport_override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.view3d.view_axis(type=view, align_active=False)
            
    # Make the viewport update() to ensure the view_axis change takes effect.
    for a in context.window.screen.areas:
        if a.type=='VIEW_3D':
            for s in a.spaces:
                if s.type=='VIEW_3D':
                    s.region_3d.update()

    # Unwrap by projecting from view.
    viewport_context_override, viewport_override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if viewport_override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
            
    viewport_context_override, viewport_override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if viewport_override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.uv.select_all(action='SELECT')
            
    uv_grid = None
    if bpy.data.images.find(image_block_name) < 0 or not bpy.data.images[image_block_name].has_data:
        uv_grid, _ = create_image_data_block(context, image_block_name, image_type='UV_GRID', color=(0, 0, 0, 1), image_filepath='', display_image=False)
    else:
        uv_grid = bpy.data.images[image_block_name]
        
    set_image_in_uv_editors(context, uv_grid)
    bpy.ops.object.material_slot_assign()
    config_viewport_materials(context)
            
    return True

if __name__ == "__main__":
    #unwrap_by_projecting_from_view(bpy.context, "Suzanne", 'FRONT', "uv_map_front", "front_texture")
    unwrap_by_projecting_from_view(bpy.context, "Suzanne", 'RIGHT', "uv_map_right", "side_texture")