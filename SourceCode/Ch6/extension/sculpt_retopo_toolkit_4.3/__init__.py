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

if "bpy" in locals():
    import importlib
    importlib.reload(mesh_editing_ops)
else:
    from . import mesh_editing_ops

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty, IntProperty
from mathutils import Vector
import bmesh
from math import floor

srtk_gp_obj_name = "Sculpt_Retopo_Toolkit_GP"

def poll_select_mesh_dropdown_filter(self, object):
    return object.type == 'MESH'

def init_scene_vars():
    bpy.types.Scene.select_mesh_dropdown = bpy.props.PointerProperty(
        name="Edit Mesh",
        type=bpy.types.Object,
        poll=poll_select_mesh_dropdown_filter)
        
    bpy.types.Scene.cut_thru_checkbox = BoolProperty(
        name="Cut Through",
        description="Whether to cut thru the mesh to the other side with Carve and In/Outset.",
        default=False)

    bpy.types.Scene.inoutset_amount = FloatProperty(
        name="In/Outset Amount",
        description="Amount to inset(+) or outset(-).",
        default=0.1)

    bpy.types.Scene.num_grid_lines = IntProperty(
        name="Grid Lines",
        description="Number of horizontal grid lines to make from GP strokes.",
        default=5,
        min=2)
        
def del_scene_vars():
    del bpy.types.Scene.select_mesh_dropdown
    del bpy.types.Scene.cut_thru_checkbox
    del bpy.types.Scene.inoutset_amount
    del bpy.types.Scene.num_grid_lines
    
#################################################################################################

def reset_gp(context, clear_strokes=False):
    if bpy.data.grease_pencils.find("srtk_gp_data") < 0:
        gp_data = bpy.data.grease_pencils.new("srtk_gp_data")
    else:
        gp_data = bpy.data.grease_pencils["srtk_gp_data"]

    if clear_strokes:
        if gp_data.layers.find("srtk_gp_data_layer") >= 0:
            gp_data.layers.remove(gp_data.layers["srtk_gp_data_layer"])
    if gp_data.layers.find("srtk_gp_data_layer") < 0:
        new_layer = gp_data.layers.new("srtk_gp_data_layer")

    gp_data.layers.active_index = gp_data.layers.find("srtk_gp_data_layer")
    active_layer = gp_data.layers[gp_data.layers.active_index]
        
    frame0_found = False
    for f in active_layer.frames:
        if f.frame_number == 0:
            frame0_found = True
            break
    if not frame0_found:
        active_layer.frames.new(0)

    context.scene.frame_set(0)
    active_layer.color = (0, 0.5, 0.5)
    context.scene.tool_settings.annotation_stroke_placement_view3d = 'SURFACE'
    context.scene.grease_pencil = gp_data
    
    existing_gp_obj_index = context.collection.objects.find(srtk_gp_obj_name)
    if existing_gp_obj_index < 0:
        gp_obj = bpy.data.objects.new(srtk_gp_obj_name, gp_data)
        context.collection.objects.link(gp_obj)
    else:
        gp_obj = context.collection.objects[existing_gp_obj_index]
        gp_obj.data = gp_data

class BUTTON_OT_reset_gp(Operator):
    bl_idname = "button.reset_gp"
    bl_label = "Reset GP"
    '''Reset GP'''

    def execute(self, context):
        reset_gp(context, clear_strokes=True)
        self.report({'INFO'}, "Sculpt & Retopo Toolkit: Reset GP.")
        return {'FINISHED'}
    
class BUTTON_OT_draw_with_GP(Operator):
    bl_idname = "button.draw_with_gp"
    bl_label = "Draw with GP"
    '''Draw with GP'''

    def execute(self, context):
        reset_gp(context, clear_strokes=False)
        existing_gp_obj_index = context.collection.objects.find(srtk_gp_obj_name)
        gp_obj = context.collection.objects[existing_gp_obj_index]
                
        for obj in context.view_layer.objects:
            obj.select_set(False)
            
        gp_obj.select_set(True)
        context.view_layer.objects.active = gp_obj
        bpy.ops.wm.tool_set_by_id(name="builtin.annotate")
        
        self.report({'INFO'}, 'Sculpt & Retopo Toolkit: Draw with GP.')
        return {'FINISHED'}
    
def gp_knife_project(context, mesh_obj_to_edit):    
    existing_gp_obj_index = context.collection.objects.find(srtk_gp_obj_name)
    gp_obj = context.collection.objects[existing_gp_obj_index]
    curve_data = bpy.data.curves.new(name="curve_data", type='CURVE')
    curve_data.dimensions = '3D'
    curve_obj = bpy.data.objects.new(name="curve_obj", object_data=curve_data)
    context.collection.objects.link(curve_obj)        
    
    num_pts = 0
    layer = gp_obj.data.layers[gp_obj.data.layers.active_index]
    for f in layer.frames:
        for s in f.strokes:
            s_spline_data = curve_obj.data.splines.new(type='POLY')
            s_num_pts = len(s.points)
            if s_num_pts < 1:
                continue
            
            num_pts += s_num_pts
            
            s_spline_data.points.add(s_num_pts - 1)
            for i in range(s_num_pts):
                pi = s.points[i].co
                s_spline_data.points[i].co = [pi[0], pi[1], pi[2], 1]
            
            # Append the first point to the end to make it a loop.
            s_spline_data.points.add(1)
            p0 = s.points[0].co
            s_spline_data.points[-1].co = [p0[0], p0[1], p0[2], 1]
            
    if num_pts < 3:
        return False, None, num_pts
              
    for obj in context.view_layer.objects:
        obj.select_set(False)
    context.view_layer.objects.active = mesh_obj_to_edit
    mesh_obj_to_edit.select_set(True)
    curve_obj.select_set(True) 
    context_override = mesh_editing_ops.get_context_override(context, 'VIEW_3D', 'WINDOW')
    with bpy.context.temp_override(**context_override):
        bpy.ops.object.mode_set(mode='EDIT')
        
    context.scene.tool_settings.mesh_select_mode[1] = True
    context_override = mesh_editing_ops.get_context_override(context, 'VIEW_3D', 'WINDOW')
    with bpy.context.temp_override(**context_override):
        bpy.ops.mesh.knife_project(cut_through=context.scene.cut_thru_checkbox)
    
    reset_gp(context, clear_strokes=True)
    return True, curve_obj, num_pts

def gp_strokes_mesh_selection_check(self, context, mesh_obj_to_edit):
    if len(context.scene.grease_pencil.layers[context.scene.grease_pencil.layers.active_index].frames[0].strokes) == 0:
        self.report({'WARNING'}, 'Sculpt & Retopo Toolkit: No GP strokes.')
        return False

    if not mesh_obj_to_edit:
        self.report({'WARNING'}, 'Sculpt & Retopo Toolkit: No mesh object selected to edit.')
        return False
    
    return True

class BUTTON_OT_carve(Operator):
    bl_idname = "button.carve"
    bl_label = "Carve"
    '''Carve'''

    def execute(self, context):
        reset_gp(context, clear_strokes=False)
        obj_to_be_carved = context.scene.select_mesh_dropdown

        if not gp_strokes_mesh_selection_check(self, context, obj_to_be_carved):
            return {'FINISHED'}
        
        knife_project_success, hole_template_obj, num_pts = gp_knife_project(context, obj_to_be_carved)
        
        if not knife_project_success:
            if num_pts < 3:
                self.report({'WARNING'}, 'Sculpt & Retopo Toolkit: Carve - GP stroke does not define a polygon.')
            else:
                self.report({'WARNING'}, 'Sculpt & Retopo Toolkit: Carve - Knife project from GP strokes failed.')
            return {'FINISHED'}            
        
        try:
            bpy.ops.mesh.separate(type='SELECTED')
        except:
            self.report({'WARNING'}, 'Sculpt & Retopo Toolkit: Carve - Draw a hole to carve with a closed loop.')
            return {'FINISHED'}

        hole_template_obj.select_set(True)
        if hole_template_obj != obj_to_be_carved and hole_template_obj.type == 'MESH':
            boolean_mod = obj_to_be_carved.modifiers.new("boolean_mod", 'BOOLEAN')
            boolean_mod.object = hole_template_obj
            boolean_mod.operation = 'DIFFERENCE'
            
            context.scene.tool_settings.mesh_select_mode[1] = True
            context_override = mesh_editing_ops.get_context_override(context, 'VIEW_3D', 'WINDOW')
            with bpy.context.temp_override(**context_override):
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.data.objects.remove(hole_template_obj)
        bpy.data.objects.remove(context.scene.objects[-1])
        context.scene.select_mesh_dropdown = None
                
        self.report({'INFO'}, 'Sculpt & Retopo Toolkit: Carve.')
        return {'FINISHED'}

class BUTTON_OT_inset(Operator):
    bl_idname = "button.inset"
    bl_label = "Inset"
    '''Inset'''

    def execute(self, context):
        reset_gp(context, clear_strokes = False)
        obj_to_inset = context.scene.select_mesh_dropdown
        if not gp_strokes_mesh_selection_check(self, context, obj_to_inset):
            return {'FINISHED'}        
        
        knife_project_success, hole_template_obj, _ = gp_knife_project(context, obj_to_inset)
        if knife_project_success:
            bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={'value': Vector((0, 0, 0))})
            bpy.ops.transform.shrink_fatten(value=context.scene.inoutset_amount)
            bpy.data.objects.remove(hole_template_obj)

        context.scene.select_mesh_dropdown = None

        self.report({'INFO'}, 'Sculpt & Retopo Toolkit: In/Outset.')
        return {'FINISHED'}

class BUTTON_OT_draw_grid(Operator):
    bl_idname = "button.draw_grid"
    bl_label = "Draw Grid"
    '''Draw Grid'''

    def execute(self, context):
        reset_gp(context, clear_strokes=False)
        obj_to_add_grid = context.scene.select_mesh_dropdown
        if not gp_strokes_mesh_selection_check(self, context, obj_to_add_grid):
            return {'FINISHED'}
        
        existing_gp_obj_index = context.collection.objects.find(srtk_gp_obj_name)
        gp_obj = context.collection.objects[existing_gp_obj_index]
        for obj in context.view_layer.objects:
            obj.select_set(False)
        context.view_layer.objects.active = obj_to_add_grid
        obj_to_add_grid.select_set(True)
        
        context_override = mesh_editing_ops.get_context_override(context, 'VIEW_3D', 'WINDOW')
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.mode_set(mode = 'OBJECT')

        context_override = mesh_editing_ops.get_context_override(context, 'VIEW_3D', 'WINDOW')
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.object.mode_set(mode = 'EDIT')

        context_override = mesh_editing_ops.get_context_override(context, 'VIEW_3D', 'WINDOW')
        with bpy.context.temp_override(**context_override):
            bpy.ops.mesh.select_all(action='DESELECT')

        context.scene.tool_settings.use_snap = True
        context.scene.tool_settings.snap_elements = {'FACE'}
        context.scene.tool_settings.snap_target = 'CLOSEST'
        context.scene.tool_settings.use_snap_self = True
        bm = bmesh.from_edit_mesh(obj_to_add_grid.data)
        verts_prev_stroke = []
        for s in gp_obj.data.layers[gp_obj.data.layers.active_index].frames[0].strokes:
            num_pts = len(s.points)
            if num_pts < context.scene.num_grid_lines:
                continue
            num_pts_per_cell = floor(num_pts/context.scene.num_grid_lines)

            v_prev = None
            verts_cur_stroke = []
            num_gls_left = context.scene.num_grid_lines
            for i in range(0, num_pts, num_pts_per_cell):
                if num_gls_left == 0:
                    break
                v = bm.verts.new(s.points[i].co - obj_to_add_grid.location)
                v.select = True
                if v_prev:
                    e = bm.edges.new([v_prev, v])
                    e.select = True
                
                v_prev = v
                verts_cur_stroke.append(v)
                num_gls_left -= 1

            if len(verts_prev_stroke) > 0:
                num_verts_to_bridge = min(len(verts_prev_stroke), len(verts_cur_stroke))
                for j in range(num_verts_to_bridge):
                    e = bm.edges.new([verts_prev_stroke[j], verts_cur_stroke[j]])
                    e.select = True
            verts_prev_stroke = verts_cur_stroke
        bpy.ops.mesh.edge_face_add()
        bmesh.update_edit_mesh(obj_to_add_grid.data)
        context.view_layer.update()
        self.report({'INFO'}, 'Sculpt & Retopo Toolkit: Draw Grid.')
        context.scene.select_mesh_dropdown = None

        reset_gp(context, clear_strokes=True)
        return {'FINISHED'}
    
class SCULPTRETOPO_PT_ToolShelfPanel(bpy.types.Panel):
    bl_idname = "SCULPT_RETOPO_PT_ToolShelfPanel"
    bl_label = "SCULPT RETOPO Toolkit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    '''A collection of grease pencil driven sculpt and retopo tools'''
 
    def draw(self, context):
        layout = self.layout
        col0 = layout.column()
        col0.operator("button.reset_gp")
        col0.operator("button.draw_with_gp")
        col0.prop(context.scene, "select_mesh_dropdown")
        
        box0 = col0.box()
        box0.label(text="Sculpt Tools", icon='SCULPTMODE_HLT')
        box0_row0 = box0.row(align=True)
        box0_row0.prop(context.scene, "cut_thru_checkbox")                 
        box0.operator("button.carve")
        box0_row1 = box0.row(align=True)
        box0_row1.prop(context.scene, "inoutset_amount")    
        box0.operator("button.inset", text="In/Outset")

        box1 = col0.box()
        box1.label(text="Retopo Tools", icon='MESH_GRID')
        box1_row0 = box1.row(align=True)
        box1_row0.prop(context.scene, "num_grid_lines")    
        box1.operator("button.draw_grid")

###########################################################################################

classes = [BUTTON_OT_reset_gp, BUTTON_OT_draw_with_GP, BUTTON_OT_carve, BUTTON_OT_inset, \
    SCULPTRETOPO_PT_ToolShelfPanel, BUTTON_OT_draw_grid]
      
def register():
    for c in classes:
        bpy.utils.register_class(c)
    init_scene_vars()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del_scene_vars()
      
if __name__ == '__main__':
    register()
