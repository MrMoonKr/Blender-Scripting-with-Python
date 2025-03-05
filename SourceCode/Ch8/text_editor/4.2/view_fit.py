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
    "get_context_override",
    "make_image_editor_fit_view",
    )

import bpy

def get_context_override(context, area_type, region_type, area_x=-1, image_name=''):
    override = context.copy()
    found_area_and_region = False
    image_matched = True
    area_x_matched = True
    for area in override['screen'].areas:
        if area.type == area_type: # e.g. 'VIEW_3D' for viewport, 'IMAGE_EDITOR' for UV/Image Editor, etc.
            override['area'] = area

            if len(image_name)>0 and area.type=='IMAGE_EDITOR':
                image_matched = False
                for space in area.spaces:
                    if space.type=='IMAGE_EDITOR':
                        if space.image and space.image.name==image_name:
                            image_matched = True
            if area_x >= 0:
                area_x_matched = (area.x==area_x)

            if image_matched and area_x_matched:
                for region in override['area'].regions:
                    if region.type==region_type: # e.g. 'WINDOW'
                        override['region'] = region
                        found_area_and_region = True
                        break

            if found_area_and_region:
                break

    return override, found_area_and_region

def make_image_editor_fit_view(context, editor_area_x=-1):
    image_editor_context_override, found_area_and_region = get_context_override(context, 'IMAGE_EDITOR', 'WINDOW', editor_area_x)

    # In a Image Editor or UV editor, resize the area to fit the image currently open.
    # Note that we have to use the correct context override so bpy.ops.image.view_all knows in which area to 
    # perform the zoom. If neither an Image nor UV Editor is open, this does nothing.
    if found_area_and_region:
        with bpy.context.temp_override(**image_editor_context_override):
            bpy.ops.image.view_all(fit_view=True)
        