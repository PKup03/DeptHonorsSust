### Live code, check below for test code
import adsk.core, traceback, adsk.fusion, importlib
import json, os, adsk.cam
import math
from .LCA_Interaction import Parameters
from .LCA_Interaction import TargetMasses
#from .LCA_Interaction import 

# global set of event handlers to keep them referenced
handlers = []
app = adsk.core.Application.get()
ui  = app.userInterface
des = adsk.fusion.Design.cast(app.activeProduct)
unitsMgr = des.unitsManager
userParams = des.userParameters
root = des.rootComponent

palette = ui.palettes.add('partMasses', 'Part Masses', 'palette.html', False, True, True, 300, 200, True)
# The True/Falses control whether the palette is visible, if a 'Close' button is shown, and if the palette can be resized
palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
palette.isVisible = True

def PaletteUpdate():
    # Code to react to the event.

    bodyMasses = []
    massesStrText = ""
    ## Set the new value for the global parameter
    importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated parameter values
    Parameters = LCA_Interaction.Parameters() # Get the updated parameter values from the LCA_Interaction file
    # 'CubeLength' is the name of the Fusion User Parameter to be changed
    # Paramaters[0] is the new value of the 'CubeLength' parameter from the LCA file
    #userParams.itemByName(userParams[0].name).expression = str(Parameters[0]) + ' in'
    #ui.messageBox('Parameter 1 has been set to ' + str(Parameters[1]) + ' in')

    if userParams:

        numBodies = root.bRepBodies.count #Get number of bodies in the component

        #Determine mass of each body in the component
        for j in range(0, numBodies):
            body = root.bRepBodies.item(j)
            physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
            mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
            bodyMasses.append(mass)
            # ui.messageBox('Body' + str(j+1) + ' has a mass of ' + str(bodyMasses[j]) + " kg")
            massesStrText += '<b>' + root.bRepBodies[j].name + ' mass:</b> ' + str(bodyMasses[j]) + ' kg' + "<br />" #The ending is for HTML line breaks
            #massesStrText += '<b>Body ' + str(j+1) + '</b> mass: ' + str(bodyMasses[j]) + ' kg' + "<br />" #The ending is for HTML line breaks
            palette.sendInfoToHTML('send', massesStrText)

    else:
        ui.messageBox('Global parameter not found.')

def FindDerivative(paramName):
        bodyMasses = []
        bodyMassesNew = []
        BodyDerivatives = []

        ## Set the new value for the global parameter
        importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated parameter values
        Parameters = LCA_Interaction.Parameters() # Get the updated parameter values from the LCA_Interaction file
        userParams.itemByName(str(paramName)).expression = str(userParams[0].value) + ' in'

        #Find initial mass of each body in the component
        for j in range(0, root.bRepBodies.count):
            body = root.bRepBodies.item(j)
            physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
            mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
            bodyMasses.append(mass)
        
        #Set the new value for the global parameter
        userParams.itemByName(str(paramName)).expression = str(userParams[0].value+0.0001) + ' in'

        #Find new body masses after parameter change
        for j in range(0, root.bRepBodies.count):
            body = root.bRepBodies.item(j)
            physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
            mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
            bodyMassesNew.append(mass)

        #Calculate and display derivative of mass with respect to parameter
        for j in range(0, root.bRepBodies.count):
            BodyDerivatives.append((float(bodyMassesNew[j])-float(bodyMasses[j]))/0.0001)
            #ui.messageBox('Derivative of ' + root.bRepBodies[j].name + ' mass with respect to ' + paramName + ' is ' + str(BodyDerivatives[j]) + ' kg/in')
        return BodyDerivatives

def AllDerivatives():
    currentDerivatives = []
    for i in range(0, userParams.count-1):
        currentDerivatives.append(FindDerivative(userParams[i].name))
    #ui.messageBox(str(currentDerivatives))
    return currentDerivatives

def iterate():
    bodyMasses = []
    for j in range(0, root.bRepBodies.count):
        body = root.bRepBodies.item(j)
        physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
        mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
        bodyMasses.append(mass)

    currentDerivatives = AllDerivatives()
    power = 2
    temp = 1

    importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated target mass values
    TargetMasses = LCA_Interaction.TargetMasses() # Get the updated target mass values from the LCA_Interaction file
    ui.messageBox("Target Masses: " + str(TargetMasses[0]))

    if TargetMasses[0]-float(bodyMasses[0]) == 0:
        ui.messageBox("check 0")
        pass
    elif TargetMasses[0]-float(bodyMasses[0]) > 0 and currentDerivatives[0][0] < 0 or TargetMasses[0]-float(bodyMasses[0]) < 0 and currentDerivatives[0][0] > 0:
        while TargetMasses[0] - float(bodyMasses[0]) > 10**power:
            ui.messageBox("check 1")
            inc = temp*10**(power-1)
            userParams.itemByName(str(userParams[0].name)).expression = str(userParams[0]+inc) + ' in'
            if TargetMasses[0]-float(bodyMasses[0]) == 0:
                ui.messageBox("check 2")
                pass
            else:
                ui.messageBox("check 3")
                temp = -temp
                power -= 1
    else:
        while TargetMasses[0] - float(bodyMasses[0]) < -(10**power):
            ui.messageBox("check 4")
            inc = -temp*10**(power-1)
            userParams.itemByName(str(userParams[0].name)).expression = str(userParams[0].value+inc) + ' in'
            if TargetMasses[0]-float(bodyMasses[0]) == 0:
                ui.messageBox("check 5")
                pass
            else:
                ui.messageBox("check 6")
                temp = -temp
                power -= 1
    ui.messageBox("check 7")
    PaletteUpdate()

#Event handler for the cameraChanged event to remove the palette, allowing for the Add-In to be re-run without restarting Fusion 360.
class MyCameraMovedHandler(adsk.core.CameraEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Code to react to the event.
        app.log('In MyDocumentSavedHandler event handler.')
        palette.deleteMe()

class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            htmlArgs = adsk.core.HTMLEventArgs.cast(args)
            Firing = json.loads(htmlArgs.data)
            # ui.messageBox(str(Firing))
            if Firing == 'Firing':
            # data = json.loads(htmlArgs.data)
            # msg = "An event has been fired from the html to Fusion with the following data:\n"
            # msg += '    Command: {}\n    arg1: {}\n    arg2: {}'.format(htmlArgs.action, data['arg1'], data['arg2'])
                PaletteUpdate()
                #FindDerivative(userParams[1].name)
                AllDerivatives()
                iterate()
                del Firing
                # ui.messageBox(Firing)
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    try:
        # onDocumentSaved = MyDocumentSavedHandler()
        # app.documentSaved.add(onDocumentSaved)
        # handlers.append(onDocumentSaved)

        onHTMLEvent = MyHTMLEventHandler()
        palette.incomingFromHTML.add(onHTMLEvent)   
        handlers.append(onHTMLEvent)

        onCameraMoved = MyCameraMovedHandler()
        app.cameraChanged.add(onCameraMoved)
        handlers.append(onCameraMoved)

        # global_handler = CommandCreatedHandler()
        # app.commandCreated.add(global_handler)
        # handlers.append(global_handler)
        
    except:
        app.log('AddIn Start Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        pass
    except:
        app.log('AddIn Stop Failed: {}'.format(traceback.format_exc()))


### Helpful Samples - Not part of the active code
    #Changing a fusion parameter value using code and printing the new value
        ## Replace '10 in' with the desired new value and unit
        #userParams.itemByName('CubeLength').expression = '20 in'
        #ui.messageBox('Global parameter updated successfully.')

    # Event Handler
    # Event handler for the documentSaved event.
# class MyDocumentSavedHandler(adsk.core.DocumentEventHandler):
#     def __init__(self):
#         super().__init__()
#     def notify(self, args):
#         eventArgs = adsk.core.CommandEventArgs.cast(args)

#         # Code to react to the event.
#         app.log('In MyDocumentSavedHandler event handler.')

#         bodyMasses = []
#         massesStrText = ""
#         ## Set the new value for the global parameter
#         importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated parameter values
#         Parameters = LCA_Interaction.Parameters() # Get the updated parameter values from the LCA_Interaction file
#         # 'CubeLength' is the name of the Fusion User Parameter to be changed
#         # Paramaters[0] is the new value of the 'CubeLength' parameter from the LCA file
#         userParams.itemByName('CubeLength').expression = str(Parameters[0]) + ' in'
#         ui.messageBox('Parameter 1 has been set to ' + str(Parameters[1]) + ' in')

#         if userParams:

#             numBodies = root.bRepBodies.count #Get number of bodies in the component

#             #Determine mass of each body in the component
#             for j in range(0, numBodies):
#                 body = root.bRepBodies.item(j)
#                 physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
#                 mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
#                 bodyMasses.append(mass)
#                 # ui.messageBox('Body' + str(j+1) + ' has a mass of ' + str(bodyMasses[j]) + " kg")
#                 massesStrText += '<b>Body ' + str(j+1) + '</b> mass: ' + str(bodyMasses[j]) + ' kg' + "<br />" #The ending is for HTML line breaks
#                 palette.sendInfoToHTML('send', massesStrText)

#         else:
#             ui.messageBox('Global parameter not found.')