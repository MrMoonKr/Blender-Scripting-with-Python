# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch6 of the book "Blender Scripting with Python" by Isabel Lupiani.
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

import bpy
import bmesh
from mathutils import Vector
import math 

def select_poles(context):
    obj = context.view_layer.objects.active
    if obj is not None and obj.type=='MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        context.tool_settings.mesh_select_mode = [True, False, False]
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            valence = len(v.link_edges)
            if valence == 3 or valence > 4:
                v.select = True
        bmesh.update_edit_mesh(obj.data)
        context.view_layer.update()
        
def get_angle_between_vectors(vector1, vector2):
    theta = math.acos(vector1.dot(vector2) / (vector1.length*vector2.length))
    return math.degrees(theta)    
        
def get_angle_between_edges(e1, e2):
    if e1.verts[0] in e2.verts:
        vert_shared = e1.verts[0]
    else:
        vert_shared = e1.verts[1]
    
    e1_end_v = e1.other_vert(vert_shared) 
    e2_end_v = e2.other_vert(vert_shared)
    vector1 = e1_end_v.co - vert_shared.co
    vector2 = e2_end_v.co - vert_shared.co
    return get_angle_between_vectors(vector1, vector2)       
    
def select_face_corners_less_than_angle(context, angle_in_degrees):
    obj = context.view_layer.objects.active
    if obj is not None and obj.type == 'MESH':
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        context.tool_settings.mesh_select_mode = [False, True, False]
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            num_edges = len(v.link_edges)
            for i in range(num_edges):
                e1 = v.link_edges[i]
                e2 = v.link_edges[0] if i == num_edges - 1 else v.link_edges[i+1]
                    
                if get_angle_between_edges(e1, e2) <= angle_in_degrees:
                    e1.select = True
                    e2.select = True
        bmesh.update_edit_mesh(obj.data)
        context.view_layer.update()

if __name__ == "__main__":
    #select_poles(bpy.context)
    select_face_corners_less_than_angle(bpy.context, 60)