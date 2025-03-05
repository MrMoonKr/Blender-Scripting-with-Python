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
    "split_screen_area",
    )
    
import bpy

def split_screen_area(context, split_dir, split_ratio, type_of_new_area, ui_type_of_new_area, check_existing=False):
    existing_areas = list(context.screen.areas)

    if check_existing:
        for area in existing_areas:
            # Found an existing area of matching type
            if area.type == type_of_new_area and area.ui_type == ui_type_of_new_area:
                return area

    bpy.ops.screen.area_split(direction=split_dir, factor=split_ratio)

    for area in context.screen.areas:
        if area not in existing_areas:
            area.type = type_of_new_area
            area.ui_type = ui_type_of_new_area
            return area
        