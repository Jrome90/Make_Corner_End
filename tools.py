from typing import *
import os
from functools import partial

import bpy
from bpy.types import WorkSpaceTool, Panel
from bpy.utils.toolsystem import ToolDef
from bpy.ops import BPyOpsSubModOp

from . build_corner import BCE_OT_BuildCorner
from . build_end import BCE_OT_BuildEnd
from . operator_service import BCE_OT_OperatorService
from . preferences import BCE_Preferences
from . utils import get_op_module_and_func


def get_addon_preferences():
    preferences = bpy.context.preferences
    return preferences.addons[__package__].preferences


def get_context_overrides(*objects):

    def get_base_context():
        window = bpy.context.window_manager.windows[0]
        area = None
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area = area

        return {'window': window, 'screen': window.screen, 'area' : area, "workspace" : window.workspace}

    context = get_base_context()
    context['object'] = objects[0]
    context['active_object'] = objects[0]
    context['selected_objects'] = objects
    context['selected_editable_objects'] = objects
    return context

def execute_operator(operator):

    active_obj = bpy.context.scene.view_layers[0].objects.active
    context_override = get_context_overrides(active_obj)

     # Emulate a single button press by setting the tool to select box
    bpy.ops.wm.tool_set_by_id(context_override,name="builtin.select_box")

    module, func = get_op_module_and_func(operator.bl_idname)
    BPyOpsSubModOp(module, func)(context_override,'INVOKE_DEFAULT')


class BCE_ToolBase(WorkSpaceTool):
    bl_space_type='VIEW_3D'
    bl_context_mode='EDIT_MESH'

    bl_keymap = (
        ("bce.operator_service", {"type": 'MOUSEMOVE', "value": 'ANY'},
        None),
    )

    def get_operator():
        raise NotImplementedError

    @staticmethod
    def event_raised(context, event):
        raise NotImplementedError

class Tool_BuildCorner(BCE_ToolBase):

    bl_idname = "bce_tool_build_corner"
    bl_label = "Build Corner"
    bl_description = ( "Builds a quad corner." )
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "bce.build_corner")
    bl_widget  = "BCE_GGT_BuildCorner"

    def get_operator():
        return BCE_OT_BuildCorner

    @staticmethod
    def event_raised(context, event):
                
        try:
            active_obj = bpy.context.scene.view_layers[0].objects.active
            context_override = get_context_overrides(active_obj)
            tools = context_override["workspace"].tools
            current_active_tool = tools.from_space_view3d_mode('EDIT_MESH').idname

            if current_active_tool == __class__.bl_idname:
                module, func = get_op_module_and_func(__class__.get_operator().bl_idname)
                BPyOpsSubModOp(module, func)(context_override,'INVOKE_DEFAULT')

        except BaseException as e:
            raise e


class Tool_BuildEnd(BCE_ToolBase):

    bl_idname = "bce_tool_build_end"
    bl_label = "Build End"
    bl_description = ( "Builds a quad ending at two parallel loops." )
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "bce.build_end")
    bl_widget  = "BCE_GGT_BuildEnd"

    def get_operator():
        return BCE_OT_BuildEnd

    @staticmethod
    def event_raised(context, event):
                
        try:
            active_obj = bpy.context.scene.view_layers[0].objects.active
            context_override = get_context_overrides(active_obj)
            tools = context_override["workspace"].tools
            current_active_tool = tools.from_space_view3d_mode('EDIT_MESH').idname
            
            if current_active_tool == __class__.bl_idname:
                module, func = get_op_module_and_func(__class__.get_operator().bl_idname)
                BPyOpsSubModOp(module, func)(context_override,'INVOKE_DEFAULT')

        except BaseException as e:
            raise e
    
class BCE_GGT_GizmoGroupBase(bpy.types.GizmoGroup):
    bl_label = "(internal)"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}
    
    def get_tool(self):
        raise NotImplementedError

    @classmethod
    def poll(cls, context):
         return (
                    context.space_data.type == 'VIEW_3D'
                    and context.active_object is not None
                    and context.active_object.type == "MESH"
                    and context.active_object.mode == 'EDIT'
                )

    def setup(self, context):
        tool = self.get_tool()

        tools = bpy.context.workspace.tools
        current_active_tool = tools.from_space_view3d_mode(bpy.context.mode).idname
        if current_active_tool == tool.bl_idname:
            if get_addon_preferences().interactive:
                BCE_OT_OperatorService.register_listener(tool, tool.event_raised)
            else:
                bpy.app.timers.register(partial(execute_operator, tool.get_operator()), first_interval=0.01)
        

class BCE_GGT_BuildCorner(BCE_GGT_GizmoGroupBase):
    tool = Tool_BuildCorner
    bl_idname = tool.bl_widget
    bl_label = "Build Corner GG"

    def get_tool(self):
        return __class__.tool

class BCE_GGT_BuildEnd(BCE_GGT_GizmoGroupBase):
    tool = Tool_BuildEnd
    bl_idname = tool.bl_widget
    bl_label = "Build End GG"

    def get_tool(self):
        return __class__.tool