# Assuming you have not changed the general structure of the template no modification is needed in this file.
from . import commands
from .lib import fusionAddInUtils as futil
import adsk.core, adsk.fusion, adsk.cam, traceback

local_handlers = []
# "application_var" is a variable referencing an Application object.
# "application_documentSaving" is the event handler function.
futil.add_handler(application_var.documentSaving, application_documentSaving, local_handlers=local_handlers)

def run(context):
    try:
        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.start()
        app = adsk.core.Application.get()
        ui  = app.userInterface

        des = adsk.fusion.Design.cast(app.activeProduct)
        userParams = des.userParameters
        root = des.rootComponent

        if userParams:
            # Set the new value for the global parameter
            # Replace '10 in' with the desired new value and unit
            #userParams.itemByName('CubeLength').expression = '10 in'
            #ui.messageBox('Global parameter updated successfully.')
            physProps = adsk.fusion.PhysicalProperties.cast(root.physicalProperties)
            mass = str((physProps.mass/1000)) #Converts mass from default g to kg, then converts to string for print
            ui.messageBox('The new part mass is ' + mass + " kg")
        else:
            ui.messageBox('Global parameter not found.')
    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()

    except:
        futil.handle_error('stop')

# Event handler for the documentSaving event.
def application_documentSaving(args: adsk.core.DocumentEventArgs):
    # Code to react to the event.
    app.log('In application_documentSaving event handler.')