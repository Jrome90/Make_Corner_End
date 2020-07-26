from typing import *
from collections import defaultdict
import bpy
#from bpy.props import IntProperty, BoolProperty
import bmesh
from bmesh.types import *

from .utils import (get_selected_edges,
                    get_face_loop_for_edge,
                    bmesh_face_loop_walker,
                    normalize
                    )

class MESH_OT_BuildEnd(bpy.types.Operator):
    bl_idname = "mesh.build_end"
    bl_label = "build end"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Builds a quad ending at two parallel loops"

    @classmethod
    def poll(cls, context):
        return (
                context.space_data.type == 'VIEW_3D'
                and context.active_object is not None
                and context.active_object.type == "MESH"
                and context.active_object.mode == 'EDIT'
        )

    def execute(self, context):
        self.execute_build_end(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


    def execute_build_end(self, context):
        # Get the active mesh
        obj = bpy.context.edit_object
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)

        for edge in get_selected_edges(bm):
            for face in list(edge.link_faces):
                if len(face.edges) == 6:
                    selected_edge_loop = get_face_loop_for_edge(face, edge)

                    loop = selected_edge_loop

                    vert_a = loop.link_loop_next.vert
                    vert_b = loop.link_loop_prev.edge.other_vert(loop.link_loop_prev.vert)

                    edges = []
                    loop_verts = []
                    for loop in bmesh_face_loop_walker(face, selected_edge_loop):
                        edges.append(loop.edge)
                        loop_verts.append(loop.vert)

                    opposite_edge_vert = loop_verts[3]
                    opposite_edge_other_vert = edges[3].other_vert(opposite_edge_vert)

                    p1 = opposite_edge_vert.co.lerp(opposite_edge_other_vert.co, 1.0 / 3.0)
                    p2 = opposite_edge_vert.co.lerp(opposite_edge_other_vert.co, 2.0 / 3.0)

                    p3 = vert_a.co.lerp(p1, 0.5)
                    p4 = vert_b.co.lerp(p2, 0.5)

                    v1 = bmesh.ops.create_vert(bm, co=p3)["vert"][0]
                    v2 = bmesh.ops.create_vert(bm, co=p4)["vert"][0]
                    v3 = vert_a
                    v4 = vert_b
                    #
                    ret: Dict[str, List[BMFace]] = bmesh.ops.contextual_create(bm, geom=[v1, v2, v3, v4])
                    new_face = ret["faces"][0]

                    if normalize(face.normal).dot(normalize(new_face.normal)) < 0.0:
                        new_face.normal_flip()
                    #
                    bmesh.ops.delete(bm, geom=[face], context='FACES_KEEP_BOUNDARY')

                    # Bridge the edges
                    bridge_list = edges[2:-1]
                    # Add the edges from the newly created face to bridge
                    for new_edge in ret["faces"][0].edges:
                        if new_edge.index == edge.index:
                            continue
                        bridge_list.append(new_edge)
                    bmesh.ops.bridge_loops(bm, edges=bridge_list)

        bpy.ops.mesh.select_all(action='DESELECT')

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()

        bmesh.update_edit_mesh(mesh, True)
