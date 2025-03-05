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
    "apply_all_modifiers",
    "apply_given_modifier",
    )
    
import bpy

from .view_fit import get_context_override

def apply_all_modifiers(context, obj_to_apply_modifier):        
    for obj in context.view_layer.objects:
        obj.select_set(False)
    context.view_layer.objects.active = obj_to_apply_modifier
    obj_to_apply_modifier.select_set(True)
        
    context_override, override_succesful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_succesful:
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.mode_set(mode='OBJECT')
            
        context_override, override_succesful = get_context_override(context, 'VIEW_3D', 'WINDOW')
        if override_succesful:
            with bpy.context.temp_override(**context_override):
                for m in obj_to_apply_modifier.modifiers:
                    try:
                        bpy.ops.object.modifier_apply(modifier=m.name)
                    except RuntimeError:
                        continue
        
def apply_given_modifier(context, obj_to_apply_modifier, modifier_type, modifier_name):
    for obj in context.view_layer.objects:
        obj.select_set(False)
    context.view_layer.objects.active = obj_to_apply_modifier
    obj_to_apply_modifier.select_set(True)
        
    context_override, override_succesful = get_context_override(context, 'VIEW_3D', 'WINDOW')
    if override_succesful:
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.mode_set(mode='OBJECT')
            
        context_override, override_succesful = get_context_override(context, 'VIEW_3D', 'WINDOW')
        if override_succesful:
            with bpy.context.temp_override(**context_override):
                for m in obj_to_apply_modifier.modifiers:
                    if m.type==modifier_type and m.name==modifier_name:
                        try:
                            bpy.ops.object.modifier_apply(modifier=m.name)
                        except RuntimeError:
                            return
                        return
