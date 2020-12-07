from typing import *
from collections import defaultdict

import bpy
from bpy.props import FloatProperty, BoolProperty
import bmesh
from bmesh.types import *
from mathutils.geometry import intersect_point_line, intersect_line_plane
from .utils import (get_selected_edges,
                    get_face_loop_for_vert,
                    get_face_loops_for_vert,
                    bmesh_face_loop_walker,
                    get_face_with_verts,
                    get_vertex_shared_by_edges,
                    )

from .make_corner import MCE_OT_MakeCorner

class MCE_OT_MakeFourToTwo(bpy.types.Operator):
    bl_idname = "mce.four_to_two"
    bl_label = "make four to two"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ""

    position: FloatProperty(name="Position", default=0.5, description="")
    alt_algo: BoolProperty(name="Secondary", default=False, description="")
    
    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT'
            )

    def execute(self, context):
        self.execute_four_to_two(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def make_four_to_two(self, bm, edges):
        def make_corner(bm, verts, plane_co, plane_normal):
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
                    center_vert_co = center_vert_co.lerp(connect_vert.co, 0.5)

                    isect_point = intersect_line_plane(center_vert_co, connect_vert.co, plane_co, plane_normal)
                    if isect_point is not None:
                        result = intersect_point_line(isect_point, center_vert_co, connect_vert.co)
                        if result is not None:
                            center_vert_co = center_vert_co.lerp(connect_vert.co, result[1])
                        else:
                            center_vert_co = center_vert_co.lerp(connect_vert.co, 0.5)
                    else:
                        center_vert_co = center_vert_co.lerp(connect_vert.co, 0.5)


                    # Make the corner geometry
                    center_vert: BMVert = bm.verts.new(center_vert_co)
                    bm.verts.index_update()

                    new_edge_a = bm.edges.new([verts[0], center_vert]) 
                    new_edge_b = bm.edges.new([verts[1], center_vert])
                    new_edge_c = bm.edges.new([connect_vert, center_vert])
                    bm.edges.index_update()

                    bm.faces.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()

                    bmesh.utils.face_split_edgenet(face, [new_edge_a, new_edge_b, new_edge_c])

        verts = set()
        for edge in edges:
            for vert in edge.verts:
                verts.add(vert)
        face = get_face_with_verts(verts)

        if face is not None and len(face.edges) == 8:

            middle_vert = get_vertex_shared_by_edges(edges)

            middle_vert_loop = get_face_loop_for_vert(face, middle_vert)
            face_loops = list(bmesh_face_loop_walker(face, middle_vert_loop))

            opposite_middle_vert = face_loops[4].vert
        
            if middle_vert is not None and opposite_middle_vert is not None:
                new_face, new_loop = bmesh.utils.face_split(face, middle_vert, opposite_middle_vert)

                if new_face is not None:
                    bm.edges.index_update()
                    new_edge = new_loop.edge
                    edge, vert = bmesh.utils.edge_split(new_edge, middle_vert, self.position)
                    new_vert = vert

                    edge_a_other_vert = edges[0].other_vert(middle_vert)
                    edge_b_other_vert = edges[1].other_vert(middle_vert)

                    if not self.alt_algo:
                        plane_normal = (opposite_middle_vert.co-new_vert.co).normalized()
                        make_corner(bm, [new_vert, edge_a_other_vert], new_vert.co, plane_normal)
                        make_corner(bm, [new_vert, edge_b_other_vert], new_vert.co, plane_normal)
                    else:
                        MCE_OT_MakeCorner.make_corner(bm, [new_vert, edge_a_other_vert], 0.5)
                        MCE_OT_MakeCorner.make_corner(bm, [new_vert, edge_b_other_vert], 0.5)

    def execute_four_to_two(self, context):
        # Get the active mesh
        obj = context.active_object
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)

        bm.select_mode = {'EDGE'}
        bm.select_flush_mode()

        edge_pairs = []

        face_edge_map = defaultdict(list)
        for edge in get_selected_edges(bm):
            for face in edge.link_faces:
                face_edge_map[face.index].append(edge)

        for edges in face_edge_map.values():
            if len(edges) == 2:
                edge_pairs.append(edges)

        for edge_pair in edge_pairs:
            self.make_four_to_two(bm, edge_pair)

        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()
        bm.normal_update()
        bmesh.update_edit_mesh(mesh)

