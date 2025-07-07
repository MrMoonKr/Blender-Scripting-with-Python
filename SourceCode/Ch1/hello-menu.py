import bpy

# 1. 단순 문자열을 출력하는 오퍼레이터 정의
class SIMPLE_OT_print_hello( bpy.types.Operator ):
    bl_idname = "wm.simple_print_hello"
    bl_label = "Print Hello"

    def execute(self, context):
        print("Hello from menu")
        self.report({'INFO'}, "Hello printed to console")
        return {'FINISHED'}


# 2. 'Misc' 상위 메뉴 정의
class VIEW3D_MT_misc_menu( bpy.types.Menu ):
    bl_label = "Misc"
    bl_idname = "VIEW3D_MT_misc_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.simple_print_hello", icon='CONSOLE')


# 3. 상단 메뉴 바에 'Misc' 메뉴를 추가하는 함수
def draw_misc_top_level( self, context ):
    layout: bpy.types.UILayout = self.layout
    layout.menu( VIEW3D_MT_misc_menu.bl_idname, text="Misc", icon='PREFERENCES' )


# 4. 등록 및 해제
classes = (
    SIMPLE_OT_print_hello,
    VIEW3D_MT_misc_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class( cls )

    # VIEW3D 상단 메뉴바에 Misc 추가
    bpy.types.VIEW3D_MT_editor_menus.append( draw_misc_top_level )

def unregister():
    # VIEW3D 상단 메뉴바에서 Misc 제거
    bpy.types.VIEW3D_MT_editor_menus.remove( draw_misc_top_level )

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
elif __name__ == "<run_path>":
    register()
