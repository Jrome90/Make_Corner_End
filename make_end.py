from typing import *
#from collections import defaultdict
import bpy
from bpy.props import FloatProperty

import bmesh
from bmesh.types import *

from .utils import (get_selected_edges,
                    get_face_loop_for_edge,
                    bmesh_face_loop_walker,
                    )

class MCE_OT_MakeEnd(bpy.types.Operator):
    bl_idname = "mce.make_end"
    bl_label = "make end"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Make a quad end."

    position: FloatProperty(name="Position", default=0.5, description="")

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT'
            )

    def execute(self, context):
        self.execute_make_end(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    @staticmethod
    def make_end(bm, edge_loop, face, fac=0.5):
        
        loop = edge_loop
        edge = edge_loop.edge
        vert_a = loop.link_loop_next.vert
        vert_b = loop.link_loop_prev.edge.other_vert(loop.link_loop_prev.vert)

        edges = []
        loop_verts = []
        for loop in bmesh_face_loop_walker(face, loop):
            edges.append(loop.edge)
            loop_verts.append(loop.vert)

        opposite_edge_vert = loop_verts[3]
        opposite_edge_other_vert = edges[3].other_vert(opposite_edge_vert)

        p1 = opposite_edge_vert.co.lerp(opposite_edge_other_vert.co, 1.0 / 3.0)
        p2 = opposite_edge_vert.co.lerp(opposite_edge_other_vert.co, 2.0 / 3.0)

        p3 = vert_a.co.lerp(p1, fac)
        p4 = vert_b.co.lerp(p2, fac)

        v1 = bm.verts.new(p3)
        v2 = bm.verts.new(p4)
        v3 = vert_a
        v4 = vert_b

        bm.verts.index_update()
        # Create the edges for the inner face
        new_edge_a = bm.edges.new([vert_a, v1])
        new_edge_b = bm.edges.new([vert_b, v2])
        new_edge_c = bm.edges.new([v1, v2])

        connect_edge_a = bm.edges.new([opposite_edge_vert, v1])
        connect_edge_b = bm.edges.new([opposite_edge_other_vert, v2])
        bm.edges.index_update()

        bmesh.utils.face_split_edgenet(face, [new_edge_a, new_edge_b, new_edge_c, connect_edge_a, connect_edge_b])

    def execute_make_end(self, context):
        # Get the active mesh
        obj = bpy.context.edit_object
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)

        for edge in get_selected_edges(bm):
            for face in list(edge.link_faces):
                if len(face.edges) == 6:
                    edge_loop = get_face_loop_for_edge(face, edge)
                    self.make_end(bm, edge_loop, face, self.position)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()
        bm.normal_update()
        bmesh.update_edit_mesh(mesh)

