import bpy
from bpy.types import Menu

class BCE_MT_PieMenu(Menu):
    bl_idname = "MESH_MT_BCE_Menu"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("mesh.build_end")
        pie.operator("mesh.build_corner")

        if hasattr(bpy.types, bpy.ops.mesh.connect_edges.idname()):
            pie.operator(bpy.ops.mesh.connect_edges.idname())

