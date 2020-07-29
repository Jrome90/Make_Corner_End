import bpy
from bpy.types import Operator

from .utils import DelayedEvent, Event, get_addon_preferences

class BCE_OT_OperatorService(Operator):
    bl_idname = "bce.operator_service"
    bl_label = "OperatorService"
    bl_options = {'INTERNAL'}
    listeners = set()
    event = DelayedEvent(0.1)
    running = False

    @classmethod 
    def poll(cls, context):
        return not cls.running and get_addon_preferences().interactive

    def modal(self, context, event):
        if context.mode != 'EDIT_MESH' or not \
        any(tool_name in [listener.bl_idname for listener in list(BCE_OT_OperatorService.listeners)] \
            for tool_name in [tool.idname for tool in context.workspace.tools]):

            BCE_OT_OperatorService.running = False
            return {'CANCELLED'}

        if event.type in {'LEFTMOUSE'} and event.value == 'PRESS':
            BCE_OT_OperatorService.event.notify(context, event)
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        print("Running Operator Service")
        if BCE_OT_OperatorService.running:
            return {"CANCELLED"}

        bpy.ops.mesh.select_all(action='DESELECT')
        BCE_OT_OperatorService.running = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    @staticmethod
    def register_listener(listener, callback):
        if listener not in BCE_OT_OperatorService.listeners:
            BCE_OT_OperatorService.event.register(callback)
            BCE_OT_OperatorService.listeners.add(listener)

        