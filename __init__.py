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
    "name" : "Make_Corner_End",
    "author" : "Jrome",
    "description" : "Make Corner: Select the vertices that terminates a loop on each adjacent edge for the face, or select an edge that connects the two vertices. \n Make End: Select the vertices or the edge between them that are created when two parellel edge loops terminate at the same side.",
    "blender" : (2, 91, 0),
    "version" : (0, 4, 1),
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
        make_corner,
        make_end,
        mce_menu,
        tools,
        preferences,
    )
import os
import bpy

from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from bpy.utils.toolsystem import ToolDef

from . preferences import MCE_Preferences
from . mce_menu import MCE_MT_PieMenu
from . make_corner import MCE_OT_MakeCorner
from . make_end import MCE_OT_MakeEnd
from . four_to_two import MCE_OT_MakeFourToTwo
from . five_to_three import MCE_OT_MakeFiveToThree
from . three_to_two import MCE_OT_MakeThreeToTwo
from . tools import Tool_MakeCorner, MCE_GGT_MakeCorner, MCE_GGT_MakeEnd, Tool_MakeEnd


def get_addon_preferences():
    preferences = bpy.context.preferences
    return preferences.addons[__package__].preferences

def add_to_toolbar():
    bpy.utils.register_tool(Tool_MakeCorner)
    bpy.utils.register_tool(Tool_MakeEnd, after={"mce.make_corner"})

def add_to_context_menu():
     bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_draw)

def remove_from_context_menu():
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_draw)

def menu_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator(make_corner.MCE_OT_MakeCorner.bl_idname, text='Make Corner')
    layout.operator(make_end.MCE_OT_MakeEnd.bl_idname, text='Make End')
    layout.operator(four_to_two.MCE_OT_MakeFourToTwo.bl_idname, text='Four To Two')
    layout.operator(five_to_three.MCE_OT_MakeFiveToThree.bl_idname, text='Five To Three')
    layout.operator(three_to_two.MCE_OT_MakeThreeToTwo.bl_idname, text='Three To Two')

classes = [ MCE_Preferences,
            MCE_MT_PieMenu,
            MCE_OT_MakeCorner,
            MCE_OT_MakeEnd,
            MCE_GGT_MakeCorner,
            MCE_GGT_MakeEnd,
            MCE_OT_MakeFourToTwo,
            MCE_OT_MakeFiveToThree,
            MCE_OT_MakeThreeToTwo,
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

    kmi_menu = km.keymap_items.new("wm.call_menu_pie", 'COMMA', 'PRESS', alt=True, repeat=False).properties.name = MCE_MT_PieMenu.bl_idname
    
def unregister():

    if get_addon_preferences().add_to_toolbar:
        bpy.utils.unregister_tool(Tool_MakeCorner)
        bpy.utils.unregister_tool(Tool_MakeEnd)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_draw)
    remove_from_context_menu()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()
