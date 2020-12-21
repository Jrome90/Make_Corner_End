from typing import *
import os
from functools import partial

import bpy
from bpy.types import WorkSpaceTool, Panel
from bpy.utils.toolsystem import ToolDef
from bpy.ops import BPyOpsSubModOp

from . make_corner import MCE_OT_MakeCorner
from . make_end import MCE_OT_MakeEnd
from . preferences import MCE_Preferences
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
    op_func = BPyOpsSubModOp(module, func)
    op_func(context_override,'INVOKE_DEFAULT')


class MCE_ToolBase(WorkSpaceTool):
    bl_space_type='VIEW_3D'
    bl_context_mode='EDIT_MESH'

    def get_operator():
        raise NotImplementedError

class Tool_MakeCorner(MCE_ToolBase):

    bl_idname = "mce_tool_make_corner"
    bl_label = "Make Corner"
    bl_description = ( "Makes a quad corner." )
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "mce.make_corner")
    bl_widget  = "MCE_GGT_MakeCorner"

    def get_operator():
        return MCE_OT_MakeCorner


class Tool_MakeEnd(MCE_ToolBase):

    bl_idname = "mce_tool_make_end"
    bl_label = "Make End"
    bl_description = ( "Makes a quad end." )
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "mce.make_end")
    bl_widget  = "MCE_GGT_MakeEnd"

    def get_operator():
        return MCE_OT_MakeEnd

    
class MCE_GGT_GizmoGroupBase(bpy.types.GizmoGroup):
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
            bpy.app.timers.register(partial(execute_operator, tool.get_operator()), first_interval=0.01)
        

class MCE_GGT_MakeCorner(MCE_GGT_GizmoGroupBase):
    tool = Tool_MakeCorner
    bl_idname = tool.bl_widget
    bl_label = "Make Corner GG"

    def get_tool(self):
        return __class__.tool

class MCE_GGT_MakeEnd(MCE_GGT_GizmoGroupBase):
    tool = Tool_MakeEnd
    bl_idname = tool.bl_widget
    bl_label = "Make End GG"

    def get_tool(self):
        return __class__.tool