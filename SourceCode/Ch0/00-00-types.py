import bpy

# base_type = bpy.types.Menu

# for type_name in dir( bpy.types ):
#     menu_type = getattr( bpy.types, type_name )
#     if issubclass( menu_type, base_type ):
#         print( menu_type )
        
def print_all_menu_subclasses():
    print( "bpy.types.Menu의 모든 하위 클래스 목록 : \n" )
    
    for attr_name in dir( bpy.types ):
        attr_value = getattr( bpy.types, attr_name )
        if isinstance( attr_value, type ) and issubclass( attr_value, bpy.types.Menu ):
            print( f"{attr_name} : {attr_value}" )
            
print_all_menu_subclasses()
