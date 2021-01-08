import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

def update_show_in_context_menu(self, context):
    self.restart = True

def update_add_to_toolbar(self, context): 
    self.restart = True


class MCE_Preferences(AddonPreferences):

    bl_idname = __package__

    add_to_toolbar: BoolProperty(name="Add to toolbar", default=True, 
                                    description="Add buttons to the toolbar", update=update_add_to_toolbar)

    add_optional_to_toolbar: BoolProperty(name="Add the additional tools to toolbar", default=False, 
                                    description="Add a group of buttons to the toolbar to access the additional tools", update=update_add_to_toolbar)

    enable_context_menu: BoolProperty(name="Add to context menu", default=True, 
                                    description="Add the operators to the context menu", update=update_show_in_context_menu)

    restart: BoolProperty(name="Restart", default=False, options={'SKIP_SAVE'}) 

    def draw(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__package__].preferences

        layout = self.layout
        layout.prop(self, "enable_context_menu")
        layout.label(text="Experimental:")
        layout.prop(self, "add_to_toolbar")
        if self.add_to_toolbar:
            layout.prop(self, "add_optional_to_toolbar")
        if self.restart:
            layout.label(text="Requires Restart for the changes to take effect", icon = 'ERROR')
        