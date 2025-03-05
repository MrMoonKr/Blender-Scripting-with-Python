# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch7 of the book "Blender Scripting with Python" by Isabel Lupiani.
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
    "get_image_editor",
    "get_uv_editor"
    )

import bpy

def get_image_editor(context, image_name=''):
    for area in context.screen.areas:
        if area.type=='IMAGE_EDITOR' and area.ui_type=='IMAGE_EDITOR':
            for space in area.spaces:
                if space.type=='IMAGE_EDITOR':
                    if len(image_name) == 0:
                        return [area, space]
                    else:
                        if space.image and space.image.name == image_name:
                            return [area, space]
    return [None, None]

def get_uv_editor(context, image_name=''):
    for area in context.screen.areas:
        if area.type=='IMAGE_EDITOR' and area.ui_type=='UV':
            for space in area.spaces:
                if space.type=='IMAGE_EDITOR':
                    if len(image_name) == 0:
                        return area, space, space.uv_editor
                    else:
                        if space.image and space.image.name == image_name:
                            return area, space, space.uv_editor
    return [None, None, None]

if __name__ == "__main__":
    area, image_editor, uv_editor = get_uv_editor(bpy.context)

    if uv_editor:
        uv_editor.show_stretch = True
        uv_editor.use_live_unwrap = True
        uv_editor.show_metadata = True
    
    if image_editor:
        image_editor.use_realtime_update = True
        
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.context.scene.tool_settings.uv_sticky_select_mode = 'SHARED_VERTEX'
        
