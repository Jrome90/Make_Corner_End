from typing import *
from functools import reduce, partial

import bmesh
import bpy
from bmesh.types import *
from mathutils import Vector


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


def get_face_loops_for_vert(vert: BMVert, face: BMFace):
    loops = []
    for loop in vert.link_loops:
        if face.index in set([face.index for face in loop.edge.link_faces]):
            loops.append(loop)
    return loops


def get_selected_verts(bm: BMesh) -> List[BMVert]:
    return [e for e in bm.verts if e.select]


def get_selected_edges(mesh: BMesh) -> List[BMEdge]:
    return [e for e in mesh.edges if e.select]


def normalize(vector: Vector) -> Vector:
    vector.normalize()
    return vector


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


# Credit: https://stackoverflow.com/a/48339861
class Event(object):
    def __init__(self):
        self.callbacks = []

    def notify(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

    def register(self, callback):
        self.callbacks.append(callback)
        return callback

class DelayedEvent(Event):
    def __init__(self, delay):
        self.callbacks = []
        self.delay = delay

    def notify_listeners(self, *args, **kwargs):      
        for callback in self.callbacks:
                    callback(*args, **kwargs)
        return None

    def notify(self, *args, **kwargs):
        bpy.app.timers.register(partial(self.notify_listeners,*args, **kwargs), first_interval=self.delay)

    def register(self, callback):
        self.callbacks.append(callback)
        return callback

def get_addon_preferences():
    preferences = bpy.context.preferences
    return preferences.addons[__package__].preferences

def get_op_module_and_func(id_name):
    return id_name.split('.', 1)
