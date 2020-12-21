import bpy
from bpy.types import Menu

class MCE_MT_PieMenu(Menu):
    bl_idname = "MESH_MT_MCE_Menu"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("mce.make_end")
        pie.operator("mce.make_corner")
        pie.operator("mce.three_to_two")
        pie.operator("mce.four_to_two")
        pie.operator("mce.five_to_three")

        # if hasattr(bpy.types, bpy.ops.mesh.connect_edges.idname()):
        #     pie.operator(bpy.ops.mesh.connect_edges.idname())

