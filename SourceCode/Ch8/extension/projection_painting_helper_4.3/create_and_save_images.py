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
    "create_image_data_block",
    "save_image_to_file",
    )
    
import bpy
import os

# if "bpy" in locals():
#     import importlib
#     importlib.reload(split_screen_area)
#     importlib.reload(uv_settings)
#     importlib.reload(view_fit)
# else:
#     from . import split_screen_area
#     from . import uv_settings
#     from . import view_fit

from .split_screen_area import split_screen_area
from .uv_settings import get_image_editor, get_uv_editor
from .view_fit import get_context_override

def create_image_data_block(context, name, image_type='UV_GRID', color=(0, 0, 0, 1), image_filepath='', display_image=True, area_ui_type='IMAGE_EDITOR'):
    image_block = None
    if bpy.data.images.find(name) < 0 or not bpy.data.images[name].has_data:
        if os.path.isfile(image_filepath):
            image_block = bpy.data.images.load(image_filepath)
            image_block.name = name
        else:
            bpy.data.images.new(name=name, width=1024, height=1024, alpha=True, float_buffer=False, stereo3d=False)
            image_block = bpy.data.images[name]
    else:
        image_block = bpy.data.images[name]
        
    image_block.generated_color = color
    image_block.generated_type = image_type

    if not display_image:
        return image_block, None

    [image_editor_area, image_editor_space, uv_editor] = [None, None, None]
    if area_ui_type=='IMAGE_EDITOR':
        [image_editor_area, image_editor_space] = get_image_editor(context, name)
    else:
        [image_editor_area, image_editor_space, uv_editor] = get_uv_editor(context, name)
    
    if image_editor_space:
        image_editor_space.image = image_block
    else:
        image_editor_area = split_screen_area(context, 'VERTICAL', 0.5, 'IMAGE_EDITOR', area_ui_type, False)
        for s in image_editor_area.spaces:
            if s.type == 'IMAGE_EDITOR':
                image_editor_space = s
                image_editor_space.image = image_block
                if area_ui_type == 'UV':
                    uv_editor = s.uv_editor
                break
            
    image_editor_context_override, override_successful = get_context_override(context, 'IMAGE_EDITOR', 'WINDOW', image_editor_area.x, name)
    if override_successful:
        with bpy.context.temp_override(**image_editor_context_override):
            bpy.ops.image.view_all(fit_view=True)
            
    return image_block, uv_editor
    
def save_image_to_file(context, name, dirpath):
    if bpy.data.images.find(name) < 0:
        print("No image by the name " + name + " exists.")
        return
    
    image = bpy.data.images[name]    
    image.filepath_raw = dirpath + '\\' + name + '.png'
    image.file_format = 'PNG'
    image.save()
