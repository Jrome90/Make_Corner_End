from typing import *
from functools import reduce, partial

import bmesh
import bpy
from bmesh.types import *

def bmesh_loop_index_update(bm: BMesh):
    index = 0
    for face in bm.faces:
        for loop in face.loops:
            loop.index = index
            index += 1


def bmesh_subdivide_edge(bm: BMesh, edge: BMEdge, n=1):
    ret = []
    for i in range(0, n):
        percent = 1.0 / float((n + 1 - i))
        ret.extend(bmesh.utils.edge_split(edge, edge.verts[0], percent))

    bm.verts.index_update()
    bm.edges.index_update()
    bmesh_loop_index_update(bm)
    return ret

def bmesh_face_loop_walker(face: BMFace, start_loop=None):

    if start_loop is None:
        start_loop = face.loops[0]

    next_loop = start_loop
    test_condition = True
    while test_condition:
        yield next_loop

        next_loop = next_loop.link_loop_next
        test_condition = next_loop.index != start_loop.index


def get_face_loop_for_edge(face: BMFace, edge: BMEdge) -> BMLoop:
    for loop in face.loops:
        if loop.edge.index == edge.index:
            return loop
    return None

# Given a face and a vert on the face, return both face loops that the vertex is shared by. 
def get_face_loops_for_vert(vert: BMVert, face: BMFace):
    loops = []
    for loop in vert.link_loops:
        if face.index in set([face.index for face in loop.edge.link_faces]):
            loops.append(loop)
    return loops

def get_face_loop_for_vert(face: BMFace, vert: BMVert) -> BMLoop:
    for loop in face.loops:
        if loop.vert.index == vert.index:
            return loop
    return None

def get_selected_verts(bm: BMesh) -> List[BMVert]:
    return [e for e in bm.verts if e.select]


def get_selected_edges(mesh: BMesh) -> List[BMEdge]:
    return [e for e in mesh.edges if e.select]


def get_vertex_shared_by_edges(edges) -> BMVert:
    verts = reduce(lambda x, y: (set(x) & set(y)), [edge.verts for edge in edges])
    if len(verts) == 1:
        return verts.pop()

    return None


def face_has_verts(face: BMFace, verts) -> bool:
    return len(set(verts).intersection(set(face.verts))) == len(verts)


def get_face_with_verts(verts) -> BMFace:
    assert (len(verts) >= 2)

    faces = {face for vert in verts for face in vert.link_faces}

    while len(faces) > 0:
        face = faces.pop()
        if face_has_verts(face, verts):
            return face
    return None


def face_has_edges(face: BMFace, edges) -> bool:
    return len(set(edges).intersection(set(face.edges))) == len(edges)


def get_face_with_edges(edges) -> BMFace:
    assert (len(edges) >= 2)

    faces = {face for edge in edges for face in edge.link_faces}

    while len(faces) > 0:
        face = faces.pop()
        if face_has_edges(face, edges):
            return face
    return None

def get_addon_preferences():
    preferences = bpy.context.preferences
    return preferences.addons[__package__].preferences


def get_op_module_and_func(id_name):
    return id_name.split('.', 1)


def filter_by_type(l, type_of):
    return [n for n in l if isinstance(n, type_of)]
