from typing import *
from collections import defaultdict

import bpy
from bpy.props import FloatProperty, BoolProperty
import bmesh
from bmesh.types import *
from mathutils.geometry import intersect_line_line, intersect_point_line
from .utils import (get_selected_edges,
                    get_selected_verts,
                    get_face_loops_for_vert,
                    get_face_with_verts,
                    get_vertex_shared_by_edges,
                    )

class MCE_OT_MakeCorner(bpy.types.Operator):
    bl_idname = "mce.make_corner"
    bl_label = "make corner"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Make a quad corner"

    position: FloatProperty(name="Position", default=0.0, description="")
    uneven_spacing: BoolProperty(name="Uneven spacing", default=False, description="")
    
    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT'
            )

    def execute(self, context):
        self.execute_make_corner(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    @staticmethod
    def make_corner(bm, verts, fac=0.0):

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

                connect_vert = get_vertex_shared_by_edges([edge_a, edge_b])
                center_vert_co = center_vert_co.lerp(connect_vert.co, fac)

                # Make the corner geometry
                center_vert: BMVert = bm.verts.new(center_vert_co)
                bm.verts.index_update()
                
                new_edge1 = bm.edges.new([verts[0], center_vert]) 
                new_edge2 = bm.edges.new([verts[1], center_vert])
                new_edge3 = bm.edges.new([connect_vert, center_vert])
                bm.edges.index_update()

                bm.faces.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.verts.ensure_lookup_table()

                bmesh.utils.face_split_edgenet(face, [new_edge1, new_edge2, new_edge3])

    def make_corner_alt(self, bm, verts, fac=0.5):
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
                vert_a = loop_a.vert
                vert_b = loop_b.edge.other_vert(loop_b.vert)

                edge_a_point, _ = intersect_point_line(vert_b.co, edge_a.verts[0].co, edge_a.verts[1].co)
                edge_b_point, _ = intersect_point_line(vert_a.co, edge_b.verts[0].co, edge_b.verts[1].co)
               

                isect_point = intersect_line_line(edge_a_point, vert_b.co, edge_b_point, vert_a.co)
                if isect_point is not None:
                    center_vert_co = isect_point[0]
                    shared_vert = get_vertex_shared_by_edges([loop_a.edge, loop_b.edge])
                    connect_vert = get_vertex_shared_by_edges([edge_a, edge_b])
                    center_vert_co = center_vert_co.lerp(connect_vert.co, fac)

                    # Make the corner geometry
                    center_vert: BMVert = bmesh.ops.create_vert(bm, co=center_vert_co)["vert"][0]

                    bm.faces.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()
                    
                    new_edge_a = bm.edges.new([vert_a, center_vert])
                    new_edge_b= bm.edges.new([vert_b, center_vert])
                    new_edge_c = bm.edges.new([center_vert, connect_vert])

                    bmesh.utils.face_split_edgenet(face, [new_edge_a, new_edge_b, new_edge_c])
                
    def execute_make_corner(self, context):
        # Get the active mesh
        obj = context.active_object
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)

        bm.select_mode = {'EDGE'}
        bm.select_flush_mode()

        face_set = set()
        vert_pairs = []

        for edge in get_selected_edges(bm):

            # A simple check to prevent accidental edge dissolves. This can still fail.
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
            if not self.uneven_spacing:
                self.make_corner(bm, vert_pair, fac=self.position)
            else:
                self.make_corner_alt(bm, vert_pair, fac=self.position)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()
        bm.normal_update()
        bmesh.update_edit_mesh(mesh)
