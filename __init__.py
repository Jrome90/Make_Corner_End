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
    "version" : (0, 1, 0),
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
        bce_menu
    )

import bpy

def menu_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator(build_corner.MESH_OT_BuildCorner.bl_idname, text='Build Corner')
    layout.operator(build_end.MESH_OT_BuildEnd.bl_idname, text='Build End')

addon_keymaps = []

def register():
    bpy.utils.register_class(build_corner.MESH_OT_BuildCorner)
    bpy.utils.register_class(build_end.MESH_OT_BuildEnd)
    bpy.utils.register_class(bce_menu.MESH_MT_BCE_Menu)

    bpy.types.VIEW3D_MT_edit_mesh_edges.append(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_draw)

    # handle the keymap
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    kmi_menu = km.keymap_items.new("wm.call_menu_pie", 'COMMA', 'PRESS', alt=True, repeat=False).properties.name = bce_menu.MESH_MT_BCE_Menu.bl_idname
    

def unregister():
    bpy.utils.unregister_class(build_corner.MESH_OT_BuildCorner)
    bpy.utils.unregister_class(build_end.MESH_OT_BuildEnd)
    bpy.utils.unregister_class(bce_menu.MESH_MT_BCE_Menu)

    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_draw)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_draw)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()