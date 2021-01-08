from typing import *
import os
from functools import partial

import bpy
from bpy.types import WorkSpaceTool, Panel
from bpy.utils.toolsystem import ToolDef
#from bpy.ops import _BPyOpsSubModOp

from . make_corner import MCE_OT_MakeCorner
from . make_end import MCE_OT_MakeEnd
from . four_to_two import MCE_OT_MakeFourToTwo
from . five_to_three import MCE_OT_MakeFiveToThree
from . three_to_two import MCE_OT_MakeThreeToTwo
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
                break
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

    _, func = get_op_module_and_func(operator.bl_idname)
    # op_func = _BPyOpsSubModOp(module, func)
    # op_func(context_override,'INVOKE_DEFAULT')
    tools = context_override["workspace"].tools
    current_active_tool = tools.from_space_view3d_mode(bpy.context.mode).idname

    if func == "make_corner":
        bpy.ops.mce.make_corner('EXEC_DEFAULT')
    elif func == "make_end":
        bpy.ops.mce.make_end('EXEC_DEFAULT')
    elif func == "four_to_two":
        bpy.ops.mce.four_to_two('EXEC_DEFAULT')
    elif func == "five_to_three" and current_active_tool == "mce_tool_five_to_three_alt":
        bpy.ops.mce.five_to_three('EXEC_DEFAULT', alt_algo=True)
    elif func == "five_to_three":
        bpy.ops.mce.five_to_three('EXEC_DEFAULT')
    elif func == "three_to_two":
        bpy.ops.mce.three_to_two('EXEC_DEFAULT')
    

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


class Tool_FourToTwo(MCE_ToolBase):
    bl_idname = "mce_tool_four_to_two"
    bl_label = "Four to Two"
    bl_description = ("")
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "mce.four_to_two")
    bl_widget  = "MCE_GGT_FourToTwo"

    def get_operator():
        return MCE_OT_MakeFourToTwo


class Tool_FiveToThree(MCE_ToolBase):
    bl_idname = "mce_tool_five_to_three"
    bl_label = "Five to Three"
    bl_description = ("")
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "mce.five_to_three")
    bl_widget  = "MCE_GGT_FiveToThree"

    def get_operator():
        return MCE_OT_MakeFiveToThree


class Tool_FiveToThreeAlt(MCE_ToolBase):
    bl_idname = "mce_tool_five_to_three_alt"
    bl_label = "Five to Three Alt"
    bl_description = ("")
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "mce.five_to_three_alt")
    bl_widget  = "MCE_GGT_FiveToThreeAlt"

    def get_operator():
        return MCE_OT_MakeFiveToThree


class Tool_ThreeToTwo(MCE_ToolBase):
    bl_idname = "mce_tool_three_to_two"
    bl_label = "Three to Two"
    bl_description = ("")
    bl_icon = os.path.join(os.path.join(os.path.dirname(__file__), "icons") , "mce.three_to_two")
    bl_widget  = "MCE_GGT_ThreeToTwo"

    def get_operator():
        return MCE_OT_MakeThreeToTwo

    
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


class MCE_GGT_FourToTwo(MCE_GGT_GizmoGroupBase):
    tool = Tool_FourToTwo
    bl_idname = tool.bl_widget
    bl_label = "Four to Two GG"

    def get_tool(self):
        return __class__.tool


class MCE_GGT_FiveToThree(MCE_GGT_GizmoGroupBase):
    tool = Tool_FiveToThree
    bl_idname = tool.bl_widget
    bl_label = "Five to Three GG"

    def get_tool(self):
        return __class__.tool


class MCE_GGT_FiveToThreeAlt(MCE_GGT_GizmoGroupBase):
    tool = Tool_FiveToThreeAlt
    bl_idname = tool.bl_widget
    bl_label = "Five to Three Alt GG"

    def get_tool(self):
        return __class__.tool


class MCE_GGT_ThreeToTwo(MCE_GGT_GizmoGroupBase):
    tool = Tool_ThreeToTwo
    bl_idname = tool.bl_widget
    bl_label = "Three to Two GG"

    def get_tool(self):
        return __class__.tool