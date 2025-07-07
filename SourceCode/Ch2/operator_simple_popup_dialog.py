# ##### BEGIN GPL LICENSE BLOCK #####
#
#    GNU GPLv3, 29 June 2007
#
#    Examples from Ch2 of the book "Blender Scripting with Python" by Isabel Lupiani.
#    Object menu -> SimpleOperator. Print the name of objects in the scene in a pop-up dialog.
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
# ##### END GPL LICENSE BLOCK #####﻿

import bpy


def main(context):
    for ob in context.scene.objects:
        print(ob)


class SimpleOperator( bpy.types.Operator ):
    """
        사용자 정의 오퍼레이터 작성 예제 클래스 입니다
    """
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"

    @classmethod
    def poll( cls, context ):
        return context.active_object is not None

    def execute( self, context ):
        main( context )
        return {'FINISHED'}

    def invoke( self, context, event ):
        wm = context.window_manager
        return wm.invoke_props_dialog( self )

    def draw( self, context ):
        layout = self.layout
        
        col0 = layout.column()
        box0 = col0.box()

        # Display the names of the current scene objects.
        box0.label( text="Scene Objects : ", icon='OBJECT_DATA' )
        for ob in context.scene.objects:
            r = box0.row( align=True )
            r.label( text = str( ob.name ) )
    

def menu_func( self, context ):
    self.layout.operator( SimpleOperator.bl_idname, text="Simple Operator", icon='OBJECT_DATA' )
    
def menu_func_misc( self, context ):
    layout: bpy.types.UILayout = self.layout
    
    layout.separator()
    layout.label( text="Misc", icon='PREFERENCES' )
    layout.menu(
        SimpleOperator.bl_idname,
        text="Miscellaneous",
        icon='BLANK1'
    )


def register():
    bpy.utils.register_class( SimpleOperator )
    bpy.types.VIEW3D_MT_object.prepend( menu_func )
    bpy.types.VIEW3D_MT_editor_menus.append( menu_func_misc )


def unregister():
    bpy.utils.unregister_class( SimpleOperator )
    bpy.types.VIEW3D_MT_object.remove( menu_func )
    bpy.types.VIEW3D_MT_editor_menus.remove( menu_func_misc )


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.object.simple_operator()
elif __name__ == "<run_path>":
    '''
        VS Code의 명령창(Ctrl+Shift+P)에서 'Blender: Run Script'로 실행시에는 __name__ 이 "<run_path>" 로 설정됩니다.
    '''
    register()
    # test call
    bpy.ops.object.simple_operator()
