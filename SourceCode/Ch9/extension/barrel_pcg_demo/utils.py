# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch9 of the book "Blender Scripting with Python" by Isabel Lupiani.
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
    "set_viewport_rotation"
    )

import bpy
from mathutils import Vector

# Set viewport rotations instead of calling bpy.ops.view3d.view_axis() to set viewport view direction. 
# This function allows additional viewport properties to be set at the same time, such as view_distance.
# view_persp is ‘PERSP’, ‘ORTHO’, or ‘CAMERA’.
# Use wxyz = [0.7071, 0.7071, 0, 0] for front view, and wxyz = [0.5, 0.5, -0.5, -0.5] for left view.
def set_viewport_rotation(context, location, wxyz, view_persp, view_dist):
    for a in context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D': 
                    s.region_3d.lock_rotation = False
                    s.region_3d.view_location = location

                    s.region_3d.view_rotation.w = wxyz[0]
                    s.region_3d.view_rotation.x = wxyz[1]
                    s.region_3d.view_rotation.y = wxyz[2]
                    s.region_3d.view_rotation.z = wxyz[3]
                    s.region_3d.view_perspective = view_persp
                    s.region_3d.view_distance = view_dist
                    
                    s.region_3d.update()
                    
def set_viewport_guides_visibility(context, visibility):
    for a in context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.overlay.show_ortho_grid = visibility
                    s.overlay.show_floor = visibility
                    s.overlay.show_axis_x = visibility
                    s.overlay.show_axis_y = visibility
                    s.overlay.show_axis_z = visibility
                    s.overlay.show_cursor = visibility
                   
def set_viewport_overlays_visibility(context, visibility):
    for a in context.window.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.overlay.show_overlays = visibility    
                    
def hide_scene_objects(context, hide=True):
    for obj in context.scene.objects:
        obj.hide_set(hide)
                    
if __name__ == "__main__":
    set_viewport_guides_visibility(bpy.context, True)
    set_viewport_overlays_visibility(bpy.context, True)
    hide_scene_objects(bpy.context, False)
