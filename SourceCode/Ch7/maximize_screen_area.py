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
    "maximize_screen_area",
    )

import bpy

def maximize_screen_area(context, type_of_area_to_maximize):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == type_of_area_to_maximize:
                for region in area.regions:
                    if region.type == 'WINDOW':
                        # Create a context override (a Python dictionary) containing 
                        # the target area, so the operator call knows which area to 
                        # maximize. 
                        override = {'window': window, 'screen': window.screen, \
                        'area': area,'region': region}
                        
                        with bpy.context.temp_override(**override):
                            bpy.ops.screen.screen_full_area()
                        break
            
if __name__ == "__main__":
    maximize_screen_area(bpy.context, 'VIEW_3D')