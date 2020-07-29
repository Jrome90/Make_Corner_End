# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Build_Corner_End",
    "author" : "Jrome",
    "description" : "Build a Corner or an End",
    "blender" : (2, 90, 0),
    "version" : (0, 3, 0),
    "location" : "",
    "warning" : "",
    "category" : "Mesh"
}

if "bpy" in locals():
    import importlib
    importlib.reload()
    importlib.reload()
else:

    from . import (
        build_corner,
        build_end,
        bce_menu,
        tools,
        operator_service,
        preferences
    )
import os
import bpy

from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from bpy.utils.toolsystem import ToolDef

from . preferences import BCE_Preferences
from . bce_menu import BCE_MT_PieMenu
from . build_corner import BCE_OT_BuildCorner
from . build_end import BCE_OT_BuildEnd
from . operator_service import BCE_OT_OperatorService
from . tools import Tool_BuildCorner, BCE_GGT_BuildCorner, BCE_GGT_BuildEnd, Tool_BuildEnd

# def register_icons():
#     path = os.path.join(os.path.dirname(__file__), "icons")
#     icons = previews.new()

#     for i in os.listdir(path):
#         if i.endswith(".png"):
#             icon_name = i[:-4]
#             file_path = os.path.join(path, i)

#             icons.load(icon_name, file_path, 'IMAGE')

#     return icons

# def unregister_icons(icons):
#     previews.remove(icons)

def get_addon_preferences():
    preferences = bpy.context.preferences
    return preferences.addons[__package__].preferences

def add_to_toolbar():
    bpy.utils.register_tool(Tool_BuildCorner,  after={"builtin.loop_cut"} , group=True)
    bpy.utils.register_tool(Tool_BuildEnd, group=False)

def add_to_context_menu():
     bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_draw)

def remove_from_context_menu():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_draw)

def menu_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator(build_corner.BCE_OT_BuildCorner.bl_idname, text='Build Corner')
    layout.operator(build_end.BCE_OT_BuildEnd.bl_idname, text='Build End')

classes = [ BCE_Preferences,
            BCE_MT_PieMenu,
            BCE_OT_BuildCorner,
            BCE_OT_BuildEnd,
            BCE_OT_OperatorService,
            BCE_GGT_BuildCorner,
            BCE_GGT_BuildEnd
            ]

addon_keymaps = []
def register():
    

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.append(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_draw)

    preferences = get_addon_preferences()
    if preferences.enable_context_menu:
        add_to_context_menu()

    if preferences.add_to_toolbar:
       add_to_toolbar()

    # handle the keymap
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    kmi_menu = km.keymap_items.new("wm.call_menu_pie", 'COMMA', 'PRESS', alt=True, repeat=False).properties.name = BCE_MT_PieMenu.bl_idname
    
def unregister():

    if get_addon_preferences().add_to_toolbar:
        bpy.utils.unregister_tool(Tool_BuildCorner)
        bpy.utils.unregister_tool(Tool_BuildEnd)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_draw)
    remove_from_context_menu()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()
