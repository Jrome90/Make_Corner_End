from typing import *
from collections import defaultdict

import bpy
import bmesh
from bmesh.types import *
from bpy.props import FloatProperty, BoolProperty
from mathutils.geometry import intersect_point_line, intersect_line_line
from .utils import (get_selected_edges,
                    get_face_loops_for_vert,
                    bmesh_face_loop_walker,
                    get_face_with_verts,
                    face_has_verts,
                    get_vertex_shared_by_edges,
                    )

from .make_end import MCE_OT_MakeEnd
from .make_corner import MCE_OT_MakeCorner

class MCE_OT_MakeFiveToThree(bpy.types.Operator):
    bl_idname = "mce.five_to_three"
    bl_label = "make five to three"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ""

    alt_algo: BoolProperty(name="Secondary", default=False, description="Alternative topology")
    straight: BoolProperty(name="Straight", default=True, description="Better topology with straight inner edges")
    position: FloatProperty(name="Position", default=0.5, description="")

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.type == 'VIEW_3D'
            and context.active_object is not None
            and context.active_object.type == "MESH"
            and context.active_object.mode == 'EDIT'
            )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        row = col.row()
        row.prop(self, "position")

        if not self.alt_algo:
            row2 = col.row()
            row2.prop(self, "straight")

        row3 = col.row()
        row3.prop(self, "alt_algo")

       

    def execute(self, context):
        self.execute_five_to_three(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def make_five_to_three_alt(self, bm, face, edges):

        if face is not None and len(face.edges) == 10:
           
            middle_edge_loop = None
            middle_edge_loop_index = 0
            face_loops = []
            for index, loop in enumerate(bmesh_face_loop_walker(face)):
                if loop.edge in edges and loop.link_loop_next.edge not in edges:
                    middle_edge_loop = loop.link_loop_prev
                    middle_edge_loop_index = index - 1
                face_loops.append(loop)

            edge_a_loop = face_loops[middle_edge_loop_index + 1]
            edge_a = edge_a_loop.edge
            vert_a = edge_a.other_vert(edge_a_loop.vert).index

            edge_b_loop = face_loops[middle_edge_loop_index - 1]
            edge_b = edge_b_loop.edge
            vert_b = edge_b_loop.vert.index
        
            vert_a2 = face_loops[(middle_edge_loop_index + 5) % len(face_loops)].vert.index
            vert_b2 = face_loops[middle_edge_loop_index - 4].vert.index

            bm.verts.ensure_lookup_table()
            new_face_a = bmesh.utils.face_split(face, bm.verts[vert_a], bm.verts[vert_a2])[0]       

            bm.edges.index_update()
            new_face_b = None
            if face_has_verts(face, [bm.verts[vert_b], bm.verts[vert_b2]]):
                new_face_b = bmesh.utils.face_split(face, bm.verts[vert_b], bm.verts[vert_b2])[0]
            else:
                new_face_b = bmesh.utils.face_split(new_face_a, bm.verts[vert_b], bm.verts[vert_b2])[0]

            # TODO: If this fails use the other face
            MCE_OT_MakeEnd.make_end(bm, middle_edge_loop, new_face_a, fac=self.position)

   
    def make_five_to_three(self, bm, face, edges):
        def make_corner_straight(bm, verts, p1, p2):
            v1 = verts[0]
            v2 = verts[1]
            

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
                    
                    isect_point = intersect_line_line(p1, p2, edge_b.verts[0].co, edge_b.verts[1].co)
                    if isect_point is not None:
                        isect_point = isect_point[0]
                    else:
                        isect_point = intersect_line_line(p1, p2, edge_a.verts[0].co, edge_a.verts[1].co)[0]


                    center_vert_co, _ =  intersect_point_line(v2.co, isect_point, v1.co)#p1.lerp(p2, 0.5)

                    # Make the corner geometry
                    center_vert: BMVert = bm.verts.new(center_vert_co) #bmesh.ops.create_vert(bm, co=center_vert_co)["vert"][0]
                    connect_vert = get_vertex_shared_by_edges([edge_a, edge_b])

                    new_edge_a = bm.edges.new([verts[0], center_vert])
                    new_edge_b = bm.edges.new([verts[1], center_vert])
                    new_edge_c = bm.edges.new([center_vert, connect_vert])

                    bmesh.utils.face_split_edgenet(face, [new_edge_a, new_edge_b, new_edge_c])

                    bm.faces.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                    bm.verts.ensure_lookup_table()


        if face is not None and len(face.edges) == 10:

            # Get the middle edge
            middle_edge_loop = None
            middle_edge_loop_index = 0
            face_loops = []
            edge_net = []
            for index, loop in enumerate(bmesh_face_loop_walker(face)):
                if loop.edge in edges and loop.link_loop_next.edge not in edges:
                    middle_edge_loop = loop.link_loop_prev
                    middle_edge_loop_index = index - 1
                face_loops.append(loop)
                edge_net.append(loop.edge)
                
            middle_edge = middle_edge_loop.edge

            # From CCW order the "a" side is the first side that is stepped over. "b" is the last.
            vert_a = middle_edge.other_vert(middle_edge_loop.vert)
            vert_b = middle_edge_loop.vert


            edge_a_loop = face_loops[(middle_edge_loop_index + 3) % len(face_loops)]
            # First edge between the two sides
            edge_a = edge_a_loop.edge

            edge_b_loop = face_loops[middle_edge_loop_index - 3]
            # Other edge between the two sides
            edge_b = edge_b_loop.edge

            # First vertex on the opposite side (Later create an edge connecting this with vert_a)
            vert_a2 = face_loops[(middle_edge_loop_index + 5) % len(face_loops)].vert
            # Last vertex on the opposite side (Later create an edge connecting this with vert_b)
            vert_b2 = face_loops[middle_edge_loop_index - 4].vert

            # Points defining  a line segment along edge a
            line_a_p1 = edge_a_loop.vert.co
            line_a_p2 = edge_a.other_vert(edge_a_loop.vert).co
           
            # The nearest point along line segment a
            nearest_point_a, fac_a = intersect_point_line(vert_a.co, line_a_p1, line_a_p2)
            # The nearest point along line segment a
            nearest_point_a2, fac_a2 = intersect_point_line(vert_a2.co, line_a_p1, line_a_p2)

            # Points defining  a line segment along edge b
            line_b_p1 = edge_b.verts[0].co
            line_b_p2 = edge_b.other_vert(edge_b.verts[0]).co
            # The nearest point along line segment b
            nearest_point_b, _ = intersect_point_line(vert_b.co, line_b_p1, line_b_p2)
            # The nearest point along line segment b
            nearest_point_b2, _ = intersect_point_line(vert_b2.co, line_b_p1, line_b_p2)

            line_p1 = nearest_point_a.lerp(nearest_point_a2, self.position)
            line_p2 = nearest_point_b.lerp(nearest_point_b2, self.position)

            p1, _ = intersect_point_line(vert_a.co, line_p1, line_p2) 
            p2, _ = intersect_point_line(vert_b.co, line_p1, line_p2)

            new_vert_a = bm.verts.new(p1)
            new_vert_b = bm.verts.new(p2)

            new_edge_center = bm.edges.new([new_vert_a, new_vert_b])

            new_edge_a = bm.edges.new([vert_a, new_vert_a])
            new_edge_b = bm.edges.new([vert_b, new_vert_b])
            
            new_edge_a2 = bm.edges.new([new_vert_a, vert_a2])
            new_edge_b2 = bm.edges.new([new_vert_b, vert_b2])

            edge_net.extend([new_edge_a, new_edge_b, new_edge_a2, new_edge_b2, new_edge_center])

            bm.verts.index_update()
            bc_verts_a = [new_vert_a, face_loops[(middle_edge_loop_index + 2) % len(face_loops)].vert]
            bc_verts_b = [new_vert_b, face_loops[(middle_edge_loop_index - 1) % len(face_loops)].vert]

            bmesh.utils.face_split_edgenet(face, edge_net)

            if self.straight:
                make_corner_straight(bm, bc_verts_a, p1, p2)
                make_corner_straight(bm, bc_verts_b, p1, p2)
            else:
                MCE_OT_MakeCorner.make_corner(bm, bc_verts_a, fac=self.position)
                MCE_OT_MakeCorner.make_corner(bm, bc_verts_b, fac=self.position)
    
    def execute_five_to_three(self, context):
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
                face_edge_map[face.index].append(edge)

        for face, edges in face_edge_map.items():
            bm.faces.ensure_lookup_table()
            if not self.alt_algo:
                self.make_five_to_three(bm, bm.faces[face], edges)
            else:
                self.make_five_to_three_alt(bm, bm.faces[face], edges)

        bm.edges.index_update()
        bm.verts.index_update()
        bm.faces.index_update()

        bm.select_flush_mode()
        bm.normal_update()
        bmesh.update_edit_mesh(mesh)
