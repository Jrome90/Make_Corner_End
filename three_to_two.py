from typing import *
from collections import defaultdict

import bpy
import bmesh
from bpy.props import BoolProperty
from bmesh.types import *

from .utils import (get_selected_edges,
                    get_face_loop_for_edge,
                    bmesh_face_loop_walker,
                    )

class MCE_OT_MakeThreeToTwo(bpy.types.Operator):
    bl_idname = "mce.three_to_two"
    bl_label = "make three to two"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ""

    flip_sides: BoolProperty(name="Flip sides", default=False, description="Flip the edge to the other side")

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT'
            )

    def execute(self, context):
        self.execute_three_to_two(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

   
    def make_three_to_two(self, bm, face, edge):
        
        if face is not None and len(face.edges) == 7:

            edge_loop = get_face_loop_for_edge(face, edge)
            face_loops = []
            edge_net = []
            for loop in bmesh_face_loop_walker(face, edge_loop):
                face_loops.append(loop)
                edge_net.append(loop.edge)

            edge_a = face_loops[2].edge
            edge_b = face_loops[-2].edge

            opposite_vert = face_loops[3].edge.other_vert(face_loops[3].vert)

            vert_a = edge.other_vert(edge_loop.vert)
            new_edge_a = bm.edges.new([vert_a, opposite_vert])
            edge_net.append(new_edge_a)
            vert_b = edge_loop.vert
            new_edge_b = bm.edges.new([vert_b, opposite_vert])
            edge_net.append(new_edge_b)

            e1 = None
            e2 = None
            new_edge_split = None
            if not self.flip_sides:
                e1, v1 =  bmesh.utils.edge_split(edge_a, edge_a.verts[0], 0.5)
                e2, v2 = bmesh.utils.edge_split(new_edge_a, vert_a, 0.5)
                new_edge_split = bm.edges.new([v1, v2])
            else:
                e1, v1 =  bmesh.utils.edge_split(edge_b, edge_b.verts[0], 0.5)
                e2, v2 = bmesh.utils.edge_split(new_edge_b, vert_b, 0.5)
                new_edge_split = bm.edges.new([v1, v2])
            edge_net.extend([new_edge_split, e1, e2])

            bmesh.utils.face_split_edgenet(face, edge_net)
            
    def execute_three_to_two(self, context):
        # Get the active mesh
        obj = context.active_object
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)

        bm.select_mode = {'EDGE'}
        bm.select_flush_mode()

        edge_groups = []

        face_edge_map = defaultdict(list)
        for edge in get_selected_edges(bm):
            for face in edge.link_faces:
                face_edge_map[face].append(edge)

        for face, edges in face_edge_map.items():
            if len(edges) == 1:
                edge_groups.append((face, edges[0]))

        for face, edges in edge_groups:
            self.make_three_to_two(bm, face, edges)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()
        bm.normal_update()
        bmesh.update_edit_mesh(mesh)
