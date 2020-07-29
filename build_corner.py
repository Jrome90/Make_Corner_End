from typing import *
from collections import defaultdict

import bpy
import bmesh
from bmesh.types import *

from .utils import (get_selected_edges,
                    get_selected_verts,
                    get_face_loops_for_vert,
                    get_face_with_verts,
                    get_vertex_shared_by_edges,
                    normalize,
                    )

class BCE_OT_BuildCorner(bpy.types.Operator):
    bl_idname = "bce.build_corner"
    bl_label = "build corner"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Builds a quad corner"

    @classmethod
    def poll(cls, context):
        if context is not None:
            if context.space_data is None:
                print("space_data is none")
                return False              
            else:
                return (
                    context.space_data.type == 'VIEW_3D'
                    and context.active_object is not None
                    and context.active_object.type == "MESH"
                    and context.active_object.mode == 'EDIT'
                    )
        return False

    def execute(self, context):
        self.execute_build_corner(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


    def build_corner(self, bm, verts):
        face = get_face_with_verts(verts)
        if face is not None and len(face.edges) == 6:

            done = False
            loop_a = None
            loop_b = None
            for vert in verts:
                face_loops = get_face_loops_for_vert(vert, face)
                for loop in face_loops:
                    if loop.vert in verts:
                        loop_a = loop

                        if loop.link_loop_next.link_loop_next.vert in verts:
                            loop_b = loop.link_loop_next

                            done = True
                            break
                if done:
                    break

            if loop_a is not None and loop_b is not None:
                edge_a = loop_a.link_loop_prev.link_loop_prev.edge
                edge_b = loop_b.link_loop_next.link_loop_next.edge

                edge_a_mid = edge_a.verts[0].co.lerp(edge_a.verts[1].co, 0.5)
                edge_b_mid = edge_b.verts[0].co.lerp(edge_b.verts[1].co, 0.5)

                p1 = loop_b.edge.other_vert(loop_b.vert).co.lerp(edge_a_mid, 0.5)
                p2 = loop_a.vert.co.lerp(edge_b_mid, 0.5)

                center_vert_co = p1.lerp(p2, 0.5)

                # Build the corner geometry
                center_vert: BMVert = bmesh.ops.create_vert(bm, co=center_vert_co)["vert"][0]
                shared_vert = get_vertex_shared_by_edges([loop_a.edge, loop_b.edge])
                verts.extend([shared_vert, center_vert])

                bm.faces.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.verts.ensure_lookup_table()

                new_face: BMFace = bmesh.ops.contextual_create(bm, geom=verts)["faces"][0]

                if normalize(face.normal).dot(normalize(new_face.normal)) < 0.0:
                    new_face.normal_flip()

                bmesh.ops.delete(bm, geom=[face], context='FACES_KEEP_BOUNDARY')

                bridge_list = [edge_a, edge_b]
                bridge_list.extend(center_vert.link_edges)

                bmesh.ops.bridge_loops(bm, edges=bridge_list)

    def execute_build_corner(self, context):
        # Get the active mesh
        obj = context.active_object
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)

        bm.select_mode = {'EDGE'}
        bm.select_flush_mode()

        face_set = set()
        vert_pairs = []

        for edge in get_selected_edges(bm):

            # A simple check to prevent accidental edge dissolves. This can still fail, but it's unlikely.
            if (len(edge.link_faces) == 2) and \
                    (len(edge.link_faces[0].edges) == 3 or len(edge.link_faces[1].edges) == 3) and \
                    (len(edge.link_faces[0].edges) == 5 or len(edge.link_faces[1].edges) == 5):

                vert_pairs.append(list(edge.verts))
                face_set.update([face.index for face in edge.link_faces])
                bmesh.ops.dissolve_edges(bm, edges=[edge])

        face_vert_map = defaultdict(list)
        for vert in get_selected_verts(bm):
            for face in vert.link_faces:
                if face.index not in face_set:
                    face_vert_map[face.index].append(vert)

        for verts in face_vert_map.values():
            if len(verts) == 2:
                vert_pairs.append(verts)

        for vert_pair in vert_pairs:
            self.build_corner(bm, vert_pair)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()

        bmesh.update_edit_mesh(mesh, True)
