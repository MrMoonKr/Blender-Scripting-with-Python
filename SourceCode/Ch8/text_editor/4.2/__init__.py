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

import bpy
from bpy.types import Operator
import bpy_extras
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
import bmesh

import math
from math import radians
from mathutils import Euler, Vector
from enum import Enum

import os, sys
script_dir = ""
if bpy.context.space_data and bpy.context.space_data.text:
    script_filepath = bpy.context.space_data.text.filepath
    if script_filepath:
        script_dir = os.path.dirname(script_filepath)
        if not script_dir in sys.path:
            sys.path.append(script_dir)
        
from apply_modifiers import apply_all_modifiers
from reference_image import load_image_empty
from unwrap_model import set_image_in_uv_editors, unwrap_model
from unwrap_by_project_from_view import unwrap_by_projecting_from_view
from view_fit import get_context_override

front_empty_name = "front_empty"
side_empty_name = "side_empty"

def poll_select_mesh_filter(self, object):
    return object.type == 'MESH'

def make_mesh_active_selected(context):
    selected_mesh = context.scene.select_mesh
    if selected_mesh:
        for obj in context.scene.objects:
            obj.select_set(False)
        context.view_layer.objects.active = selected_mesh
        context.view_layer.objects.active.select_set(True)

def get_uv_map_index(obj, uv_name):
    if obj and obj.data:
        for i in range(len(obj.data.uv_layers)):
            uv_map = obj.data.uv_layers[i]
            if uv_map.name == uv_name:
                return i
    return -1

def ready_for_projection_painting(context, view):
    selected_mesh = context.scene.select_mesh
    if not selected_mesh or not selected_mesh.data:
        return False
    
    if selected_mesh.data.uv_layers.find(context.scene.uv_name_overall) < 0:
        return False
    
    if view == 'FRONT':
        if not context.scene.image_empties[front_empty_name] or not context.scene.image_empties[front_empty_name].data:
            return False
        if selected_mesh.data.uv_layers.find(context.scene.uv_name_front) < 0:
            return False
    else:
        if not context.scene.image_empties[side_empty_name] or not context.scene.image_empties[side_empty_name].data:
            return False
        if selected_mesh.data.uv_layers.find(context.scene.uv_name_side) < 0:
            return False

    return True

def setup_for_projection_painting(context, view):
    context.scene.render.engine = 'CYCLES'
    make_mesh_active_selected(context)
    viewport_context_override, viewport_override_successful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if viewport_override_successful:
        with bpy.context.temp_override(**viewport_context_override):
            bpy.ops.view3d.view_axis(type=view, align_active=False)    
    
    uv_overall_index = get_uv_map_index(context.scene.select_mesh, context.scene.uv_name_overall)
    context.scene.select_mesh.data.uv_layers.active_index = uv_overall_index
    
    for uv in context.scene.select_mesh.data.uv_layers:
        uv.active_render = False
    context.scene.select_mesh.data.uv_layers[context.scene.uv_name_overall].active_render = True
    
    bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
    context.scene.tool_settings.image_paint.mode = 'IMAGE'
    context.scene.tool_settings.image_paint.use_clone_layer = True
    context.scene.tool_settings.image_paint.interpolation = 'CLOSEST'
    
    overall_texture = bpy.data.images[context.scene.uv_name_overall+"_texture"]
    context.scene.tool_settings.image_paint.canvas = overall_texture
    set_image_in_uv_editors(context, overall_texture)
            
    bpy.ops.paint.brush_select(image_tool='CLONE')
    empty_name = front_empty_name if view=='FRONT' else side_empty_name
    context.scene.tool_settings.image_paint.clone_image = context.scene.image_empties[empty_name].data
    context.scene.tool_settings.image_paint.use_symmetry_y = False if view=='FRONT' else True
    context.scene.tool_settings.image_paint.use_symmetry_x = False
    context.scene.tool_settings.image_paint.use_symmetry_z = False

    uv_proj_name = context.scene.uv_name_front if view=='FRONT' else context.scene.uv_name_side
    uv_proj_index = get_uv_map_index(context.scene.select_mesh, uv_proj_name)
    bpy.ops.wm.context_set_int(data_path="active_object.data.uv_layer_clone_index", value=uv_proj_index)

    context.scene.tool_settings.unified_paint_settings.size = 100
    bpy.data.brushes["Clone"].strength = 1.0
    bpy.data.brushes['Clone'].blend = 'MIX'
    bpy.data.brushes["Clone"].use_accumulate = False
    bpy.data.brushes["Clone"].use_alpha = False
    bpy.data.brushes["Clone"].stroke_method = 'AIRBRUSH'
    bpy.data.brushes["Clone"].rate = 1.0

class BUTTON_OT_projection_paint_texture_front(Operator):
    bl_idname = "button.projection_paint_texture_front"
    bl_label = "Projection Paint Texture - Front"
    """Projection Paint Texture using the Front UV and Reference Photo"""

    def execute(self, context):
        self.report({'INFO'}, "Projection Painting Helper: Texture projection painted from frontal reference photo.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return ready_for_projection_painting(context, 'FRONT')

    def invoke(self, context, event):
        setup_for_projection_painting(context, 'FRONT')
        return self.execute(context)

class BUTTON_OT_projection_paint_texture_side(Operator):
    bl_idname = "button.projection_paint_texture_side"
    bl_label = "Projection Paint Texture - Side"
    """Projection Paint Texture using the Side UV and Reference Photo"""

    def execute(self, context):
        self.report({'INFO'}, "Projection Painting Helper: Texture projection painted from side reference photo.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return ready_for_projection_painting(context, context.scene.side_dir)

    def invoke(self, context, event):
        setup_for_projection_painting(context, context.scene.side_dir)
        return self.execute(context)
    
class BUTTON_OT_projection_paint_texture_oppo_side(Operator):
    bl_idname = "button.projection_paint_texture_oppo_side"
    bl_label = "Projection Paint Texture - Opposite Side"
    """Projection Paint Texture on the Opposite Side of Side UV and Reference Photo"""

    def execute(self, context):
        self.report({'INFO'}, "Projection Painting Helper: Texture projection painted from opposite side of reference photo.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return ready_for_projection_painting(context, context.scene.side_dir)

    def invoke(self, context, event):
        oppo_dir = 'LEFT' if context.scene.side_dir=='RIGHT' else 'RIGHT'
        setup_for_projection_painting(context, oppo_dir)
        return self.execute(context)
    
class BUTTON_OT_unwrap_overall(Operator):
    bl_idname = "button.unwrap_overall"
    bl_label = "Unwrap Overall UV"
    """Unwrap Overall UV for the Selected Mesh"""

    def execute(self, context):
        apply_all_modifiers(context, context.scene.select_mesh)
        unwrap_model(context, context.scene.select_mesh.name, context.scene.uv_min_stretch_iterations, context.scene.uv_name_overall, context.scene.uv_name_overall+"_texture")
        self.report({'INFO'}, "Projection Painting Helper: Mesh overall UV unwrapped.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True if context.scene.select_mesh else False

class BUTTON_OT_unwrap_front(Operator):
    bl_idname = "button.unwrap_front"
    bl_label = "Unwrap Front UV"
    """Unwrap UV for the Selected Mesh from the Front View"""

    def execute(self, context):
        if len(context.scene.uv_name_front) < 1:
            context.scene.uv_name_front = "front_uv"
        
        front_empty = context.scene.image_empties[front_empty_name]
        front_image_name = front_empty.data.name if front_empty and front_empty.data else context.scene.uv_name_front+"_texture"
        unwrap_by_projecting_from_view(context, context.scene.select_mesh.name, 'FRONT', context.scene.uv_name_front, front_image_name)
        
        self.report({'INFO'}, "Projection Painting Helper: Face mesh front UV unwrapped.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True if context.scene.select_mesh else False

class BUTTON_OT_unwrap_side(Operator):
    bl_idname = "button.unwrap_side"
    bl_label = "Unwrap Side UV"
    """Unwrap UV for the Selected Mesh from Side View"""

    def execute(self, context):
        if len(context.scene.uv_name_side) < 1:
            context.scene.uv_name_side = "side_uv"
            
        side_empty = context.scene.image_empties[side_empty_name]
        side_image_name = side_empty.data.name if side_empty and side_empty.data else context.scene.uv_name_side+"_texture"
        unwrap_by_projecting_from_view(context, context.scene.select_mesh.name, context.scene.side_dir, context.scene.uv_name_side, side_image_name)

        self.report({'INFO'}, "Projection Painting Helper: Face mesh side UV unwrapped.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True if context.scene.select_mesh else False

class IMPORT_OT_open_front_ref(Operator, ImportHelper):
    bl_idname = "import.open_front_ref"
    bl_label = "Open front ref image"
    """Load front reference image file."""

    def execute(self, context):
        empty_loc = context.scene.select_mesh.location if context.scene.select_mesh else (0,0,0)
        if bpy.data.objects.find(front_empty_name) >= 0:
            bpy.data.objects.remove(bpy.data.objects[front_empty_name])
        load_image_empty(context, front_empty_name, self.filepath, empty_loc, [90,0,0], 'DEFAULT', 'DOUBLE_SIDED', 1.0)
        context.scene.image_empties[front_empty_name] = bpy.data.objects[front_empty_name]
        context.scene.image_empties[front_empty_name].hide_set(True)

        self.report({'INFO'}, "Projection Painting Helper loaded frontal ref: " + self.filepath)
        return {'FINISHED'}

class IMPORT_OT_open_side_ref(Operator, ImportHelper):
    bl_idname = "import.open_side_ref"
    bl_label = "Open side ref image"
    """Load side reference image file."""

    def execute(self, context):
        empty_loc = context.scene.select_mesh.location if context.scene.select_mesh else (0,0,0)
        if bpy.data.objects.find(side_empty_name) >= 0:
            bpy.data.objects.remove(bpy.data.objects[side_empty_name])
        load_image_empty(context, side_empty_name, self.filepath, empty_loc, [90,0,90], 'DEFAULT', 'DOUBLE_SIDED', 1.0)
        context.scene.image_empties[side_empty_name] = bpy.data.objects[side_empty_name]
        context.scene.image_empties[side_empty_name].hide_set(True)

        self.report({'INFO'}, "Projection Painting Helper: Loaded side ref: " + self.filepath)
        return {'FINISHED'}

class PROJECTION_PAINTING_HELPER_PT_PANEL(bpy.types.Panel):
    bl_label = "Projection Painting Helper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    """Helper tools for projection painting using the same front/side reference photons used for modeling"""
 
    def draw(self, context):  
        layout = self.layout
        row0 = layout.row()
        row0.alignment = 'CENTER'
        box0 = row0.box()
        box0.prop(context.scene, "select_mesh")
        box0.operator("import.open_front_ref", text="Front Reference Image", icon='FILE_IMAGE')

        front_empty = context.scene.image_empties[front_empty_name]
        if front_empty:
            if bpy.data.objects.find(front_empty_name) < 0 or not front_empty.data:
                context.scene.image_empties[front_empty_name] = None
            else:
                box0.label(text=str(front_empty.data.filepath), icon='FILE_IMAGE')
            
        box0.operator("import.open_side_ref", text="Side Reference Image", icon='FILE_IMAGE')

        side_empty = context.scene.image_empties[side_empty_name]
        if side_empty:
            if bpy.data.objects.find(side_empty_name) < 0 or not side_empty.data:
                context.scene.image_empties[side_empty_name] = None
            else:
                box0.label(text=str(side_empty.data.filepath), icon='FILE_IMAGE')
            
        r = box0.row(align=True)
        r.prop(context.scene, "side_dir")
        r = box0.row(align=True)
        r.prop(context.scene, "uv_min_stretch_iterations")
        r = box0.row(align=True)
        r.prop(context.scene, "uv_name_overall")
        r = box0.row(align=True)
        r.prop(context.scene, "uv_name_front")
        r = box0.row(align=True)
        r.prop(context.scene, "uv_name_side")
        
        box0.operator("button.unwrap_overall", text="Unwrap Overall UV", icon='UV')
        box0.operator("button.unwrap_front", text="Unwrap Front UV", icon='UV')
        box0.operator("button.unwrap_side", text="Unwrap Side UV", icon='UV')
        box0.operator("button.projection_paint_texture_front", text="Projection Paint Front", icon='TPAINT_HLT')
        box0.operator("button.projection_paint_texture_side", text="Projection Paint Side", icon='TPAINT_HLT')
        box0.operator("button.projection_paint_texture_oppo_side", text="Projection Paint Opposite Side", icon='TPAINT_HLT')

def init_scene_vars():
    bpy.types.Scene.select_mesh = bpy.props.PointerProperty(
        name="Mesh to Unwrap",
        type=bpy.types.Object,
        poll=poll_select_mesh_filter)
        
    bpy.types.Scene.side_dir = bpy.props.EnumProperty(
        name="Side Dir",
        items=(('LEFT', "LEFT", "LEFT"),
            ('RIGHT', "RIGHT", "RIGHT")),
        description="Select the side reference's direction (left or right).",
        default='LEFT')
        
    bpy.types.Scene.uv_min_stretch_iterations = bpy.props.IntProperty(
        name = "Minimize Stretch Iterations",
        description = "Number of iterations to minimize UV stretch.",
        default = 10,
        min = 0)

    bpy.types.Scene.uv_name_overall = bpy.props.StringProperty(
        name = "UV",
        description = "Name of overall uv map.",
        default = 'overall_uv',
        maxlen = 1024,
        subtype = "NONE")

    bpy.types.Scene.uv_name_front = bpy.props.StringProperty(
        name = "Front UV",
        description = "Name of front uv map.",
        default = "front_uv",
        maxlen = 1024,
        subtype = "NONE")

    bpy.types.Scene.uv_name_side = bpy.props.StringProperty(
        name = "Side UV",
        description = "Name of side uv map.",
        default = "side_uv",
        maxlen = 1024,
        subtype = "NONE")

    bpy.types.Scene.image_empties = {front_empty_name: None, side_empty_name: None}

def del_scene_vars():
    del bpy.types.Scene.select_mesh
    del bpy.types.Scene.side_dir
    del bpy.types.Scene.uv_min_stretch_iterations
    del bpy.types.Scene.uv_name_overall
    del bpy.types.Scene.uv_name_front
    del bpy.types.Scene.uv_name_side
    del bpy.types.Scene.image_empties

classes = [IMPORT_OT_open_front_ref, 
           IMPORT_OT_open_side_ref,
           BUTTON_OT_unwrap_overall,
           BUTTON_OT_unwrap_front,
           BUTTON_OT_unwrap_side,
           BUTTON_OT_projection_paint_texture_front,
           BUTTON_OT_projection_paint_texture_side,
           BUTTON_OT_projection_paint_texture_oppo_side,
           PROJECTION_PAINTING_HELPER_PT_PANEL]
      
def register():
    init_scene_vars()
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del_scene_vars()
      
if __name__ == "__main__":
    register()
 