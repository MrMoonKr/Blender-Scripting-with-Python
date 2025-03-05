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

import bmesh
import bpy
from bpy_extras import view3d_utils
from bpy.props import StringProperty, FloatProperty, IntProperty
from bpy.types import Operator

from enum import IntEnum, unique
from mathutils import Vector, Euler
from math import radians

import os, sys
script_dir = ""
if bpy.context.space_data and bpy.context.space_data.text:
    script_filepath = bpy.context.space_data.text.filepath
    if script_filepath:
        script_dir = os.path.dirname(script_filepath)
        if not script_dir in sys.path:
            sys.path.append(script_dir)

from creating_and_editing_mesh_objs import add_circle, get_placeholder_mesh_obj_and_bm
from utils import set_viewport_rotation

@unique
class BarrelGenSteps(IntEnum):
    Before = 0
    CrossSections = 1
    TopBottomFaces = 2
    BridgeLoops = 3
    SubdivSmooth = 4
    Whole = 5

demo_steps_msgs = {BarrelGenSteps.Before: "Welcome to the Barrel Generation Demo",
                   BarrelGenSteps.CrossSections: "Create Circular Cross-Sections", 
                   BarrelGenSteps.TopBottomFaces: "Fill in Top and Bottom Faces",
                   BarrelGenSteps.BridgeLoops: "Bridge the Cross-Sections with Edge Loops",
                   BarrelGenSteps.SubdivSmooth: "Subdivide Smooth",
                   BarrelGenSteps.Whole: "Complete Model"}
                   
default_barrel_name = "barrel_obj"
modal_text_obj_name = "modal_text_obj"

def hide_all_meshes(context):
    for obj in context.scene.objects:
        if obj.type == 'MESH':
            obj.hide_set(True)

def generate_barrel(context, name, radius_end, radius_mid, height, num_segments, center, step):
    if len(name) < 1:
        name = default_barrel_name

    bm, barrel_obj = get_placeholder_mesh_obj_and_bm(context, name, center)
    if step.value < BarrelGenSteps.Whole.value:
        barrel_obj.name += ("_" + str(step.value) + "_" + step.name)
    
    if step.value > BarrelGenSteps.Before.value:
        bottom_cap_verts = add_circle(bm, radius_end, num_segments, -height/2)
        add_circle(bm, radius_mid, num_segments, 0)
        top_cap_verts = add_circle(bm, radius_end, num_segments, height/2)
    
    if step.value > BarrelGenSteps.CrossSections.value:
        bm.faces.new(top_cap_verts)
        bm.faces.new(bottom_cap_verts)
    
    if step.value > BarrelGenSteps.TopBottomFaces.value:
        bmesh.ops.bridge_loops(bm, edges=bm.edges)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    if step.value > BarrelGenSteps.BridgeLoops.value:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(smoothness=1)
    
    bmesh.update_edit_mesh(barrel_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
def set_view(context):
    # Use the same viewport rotation as the default Cube object.
    set_viewport_rotation(context, context.scene.cursor.location, wxyz=(0.716, 0.439, 0.291, 0.459), view_persp='PERSP', view_dist=30.0)
        
class GenerateBarrelOperator(Operator):
    bl_idname = "mesh.generate_barrel"
    bl_label = "Generate Barrel"
    """Unwrap Side UV for the Face Mesh from View"""

    def execute(self, context):
        generate_barrel(context, context.scene.barrel_name, context.scene.barrel_radius_ends, \
            context.scene.barrel_radius_mid, context.scene.barrel_height, context.scene.barrel_segments, \
            context.scene.cursor.location, BarrelGenSteps.Whole)
        self.report({'INFO'}, "Barrel generated.")
        return {'FINISHED'}

    def invoke(self, context, event):
        hide_all_meshes(context)
        set_view(context)
        return self.execute(context)
    
def get_text_obj_loc(context):
    z_offset = context.scene.barrel_height * 0.5 + 3
    x, y, z = context.scene.cursor.location
    return Vector((x, y, z+z_offset))

def init_text_obj(context, text, location):
    curve_name = modal_text_obj_name + "_curve"
    curve_obj = bpy.data.curves[curve_name] if bpy.data.curves.find(curve_name) >= 0 else bpy.data.curves.new(curve_name, 'FONT')
    curve_obj.fill_mode = 'FRONT'
    curve_obj.body = text
    curve_obj.align_x = 'CENTER'
    curve_obj.align_y = 'CENTER'
    
    text_obj = bpy.data.objects[modal_text_obj_name] if bpy.data.objects.find(modal_text_obj_name) >= 0 else bpy.data.objects.new(modal_text_obj_name, curve_obj)
    text_obj.location = location
    text_obj.data.size = 1.5
    text_obj.rotation_euler = Euler((radians(d) for d in [90, 0, 90]), 'XYZ')
    if context.collection.objects.find(modal_text_obj_name) < 0:
        context.collection.objects.link(text_obj)

    cur_active_obj = context.view_layer.objects.active
    context.view_layer.objects.active = text_obj
    bpy.ops.material.new()
    mat = bpy.data.materials[-1]
    mat.name = modal_text_obj_name + "_mat"
    mat.diffuse_color = (1, 1, 1, 1)
    bpy.ops.object.material_slot_add()
    text_obj.material_slots[-1].material = mat
    text_obj.active_material_index = text_obj.data.materials.find(mat.name)
    context.view_layer.objects.active = cur_active_obj

    text_obj.hide_set(False)
    bpy.types.Scene.text_obj = text_obj

def update_text_obj(context, new_text, new_location):
    context.scene.text_obj.hide_set(False)
    context.scene.text_obj.data.body = new_text
    context.scene.text_obj.location = new_location

def clear_text_obj(context):
    context.scene.text_obj.data.body = ""
    context.scene.text_obj.hide_set(True)

class BarrelDemoInteractive(Operator):
    bl_idname = "modal.barrel_demo_interactive"
    bl_label = "Barrel Demo Interactive"
    """PCG Barrel Interactive Demo"""

    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        # Down arrow to advance one step in the barrel generation.
        if event.type == 'DOWN_ARROW' and event.value == 'RELEASE':
            if self._current_step == BarrelGenSteps.Whole:
                self.cancel(context)
                return {'FINISHED'}
            else:
                self._current_step = BarrelGenSteps(self._current_step.value+1)
                
                generate_barrel(context, context.scene.barrel_name, context.scene.barrel_radius_ends, \
                    context.scene.barrel_radius_mid, context.scene.barrel_height, \
                    context.scene.barrel_segments, context.scene.cursor.location, self._current_step)                
                
                update_text_obj(context, demo_steps_msgs[self._current_step], get_text_obj_loc(context))

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        hide_all_meshes(context)
        set_view(context)
        
        context.window_manager.modal_handler_add(self)
        self._current_step = BarrelGenSteps.Before
        init_text_obj(context, demo_steps_msgs[self._current_step] + "\nPress Down Arrow to Continue and Esc to Quit.", context.scene.cursor.location)
        
        self.report({'INFO'}, "Barrel Demo Interactive: Invoke.")
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        clear_text_obj(context)

class BarrelDemoTimelapse(Operator):
    bl_idname = "modal.barrel_demo_timelapse"
    bl_label = "Barrel Demo Timelapse"
    """PCG Barrel Demo Timelapse"""

    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self._current_step == BarrelGenSteps.Whole:
                self.cancel(context)
                return {'FINISHED'}
            else:
                self._current_step = BarrelGenSteps(self._current_step.value+1)
                
                generate_barrel(context, context.scene.barrel_name, context.scene.barrel_radius_ends, \
                    context.scene.barrel_radius_mid, context.scene.barrel_height, \
                    context.scene.barrel_segments, context.scene.cursor.location, self._current_step)
                    
                update_text_obj(context, demo_steps_msgs[self._current_step], get_text_obj_loc(context))

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        hide_all_meshes(context)
        set_view(context)
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=1, window=context.window)
        wm.modal_handler_add(self)
        self._current_step = BarrelGenSteps.Before
        init_text_obj(context, demo_steps_msgs[self._current_step], get_text_obj_loc(context))
        
        self.report({'INFO'}, "Barrel Demo Timelapse: Invoke.")
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        clear_text_obj(context)
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

class BARREL_GENERATOR_PT_ToolPanel(bpy.types.Panel):
    bl_idname = "BARREL_GENERATOR_PT_ToolPanel"
    bl_label = "BARREL_GENERATOR"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    """Barrel Generator Tool"""

    def draw(self, context):
        layout = self.layout
        col0 = layout.column()
        box0 = col0.box()

        box0.label(text = 'Barrel Generator')
        box0_row0 = box0.row(align=True)
        box0_row0.prop(context.scene, 'barrel_name')
        box0_row0 = box0.row(align=True)
        box0_row0.prop(context.scene, 'barrel_radius_ends')
        box0_row1 = box0.row(align=True)
        box0_row1.prop(context.scene, 'barrel_radius_mid')
        box0_row1 = box0.row(align=True)
        box0_row1.prop(context.scene, 'barrel_height')
        box0_row1 = box0.row(align=True)
        box0_row1.prop(context.scene, 'barrel_segments')

        box0.operator('mesh.generate_barrel', icon='MESH_DATA')
        box0.operator('modal.barrel_demo_interactive')
        box0.operator('modal.barrel_demo_timelapse')

def init_scene_vars():
    bpy.types.Scene.barrel_name = StringProperty(
        name="Barrel Name",
        description="Enter name for the barrel object.",
        default=default_barrel_name,
        subtype='NONE')
            
    bpy.types.Scene.barrel_radius_ends = bpy.props.FloatProperty(
        name="Radius Top/Bottom",
        description="Radius of the top/bottom of the barrel.",
        default=5.0,
        min=1.0)

    bpy.types.Scene.barrel_radius_mid = bpy.props.FloatProperty(
        name="Radius Middle",
        description="Radius of the middle of the barrel.",
        default=7.0,
        min=1.0)

    bpy.types.Scene.barrel_height = bpy.props.FloatProperty(
        name="Height",
        description="Height of the barrel.",
        default=8.0,
        min=1.0)

    bpy.types.Scene.barrel_segments = bpy.props.IntProperty(
        name="Segments",
        description="Number of circular segments for the barrel.",
        default=16,
        min=4)
    
    bpy.types.Scene.text_obj = None

def del_scene_vars():
    del bpy.types.Scene.text_obj
    del bpy.types.Scene.barrel_name
    del bpy.types.Scene.barrel_radius_ends
    del bpy.types.Scene.barrel_radius_mid
    del bpy.types.Scene.barrel_height
    del bpy.types.Scene.barrel_segments

classes = [GenerateBarrelOperator, BarrelDemoInteractive, BarrelDemoTimelapse, BARREL_GENERATOR_PT_ToolPanel]

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