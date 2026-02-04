### Live code, check below for test code
import adsk.core, traceback, adsk.fusion, importlib
import json, os, adsk.cam
import math, time
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

# Specifying units
lenUnits = 'in'  # inches
massUnits = 'kg'  # kilograms

palette = ui.palettes.add('partMasses', 'Part Masses', 'palette.html', False, True, True, 300, 200, True)
# The True/Falses control whether the palette is visible, if a 'Close' button is shown, and if the palette can be resized
palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
palette.isVisible = True

def PaletteUpdate():
    # Code to react to the event.

    bodyMasses = []
    massesStrText = ""
    ## Set the new value for the global parameter
    #importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated parameter values
    #Parameters = LCA_Interaction.Parameters() # Get the updated parameter values from the LCA_Interaction file
    # 'CubeLength' is the name of the Fusion User Parameter to be changed
    # Paramaters[0] is the new value of the 'CubeLength' parameter from the LCA file
    #userParams.itemByName(userParams[0].name).expression = str(Parameters[0]) + ' in'
    #ui.messageBox('Parameter 1 has been set to ' + str(Parameters[1]) + ' in')

    if userParams:

        #Determine mass of each body in the component
        for j in range(0, root.bRepBodies.count):
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

        # ## Set the new value for the global parameter
        # importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated parameter values
        # Parameters = LCA_Interaction.Parameters() # Get the updated parameter values from the LCA_Interaction file
        # userParams.itemByName(str(paramName.name)).expression = str(paramName.value) + ' in'

        #Find initial mass of each body in the component
        for j in range(0, root.bRepBodies.count):
            body = root.bRepBodies.item(j)
            physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
            mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
            bodyMasses.append(mass)
        
        #Set the new value for the global parameter
        userParams.itemByName(str(paramName.name)).expression = str((float(unitsMgr.formatInternalValue(paramName.value, 'in', False))+0.0001)) + ' in'

        #Find new body masses after parameter change
        for j in range(0, root.bRepBodies.count):
            body = root.bRepBodies.item(j)
            physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
            mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
            bodyMassesNew.append(mass)

        #Calculate and display derivative of mass with respect to parameter
        for j in range(0, root.bRepBodies.count):
            BodyDerivatives.append((float(bodyMassesNew[j])-float(bodyMasses[j]))/0.0001)
        #ui.messageBox('Derivative of ' + root.bRepBodies[0].name + ' mass with respect to ' + paramName.name + ' is ' + str(BodyDerivatives[0]) + ' kg/in')
        return BodyDerivatives

def AllDerivatives():
    currentDerivatives = []
    for i in range(0, userParams.count-1):
        currentDerivatives.append(FindDerivative(userParams[i]))
    #ui.messageBox(str(currentDerivatives))
    return currentDerivatives

def GeneratePoints(NumSteps):
    #Create a range of points around the current parameter value with a step size one decade smaller than the parameter value
    p1 = round(userParams[0].value-(NumSteps//2)*(int(math.log10(userParams[0].value))-1), 5)
    p1end = round(userParams[0].value+(NumSteps//2)*(int(math.log10(userParams[0].value))-1), 5)
    list1 = []
    if int(math.log10(userParams[0].value))-1 < 0:
        mult = -1
    elif int(math.log10(userParams[0].value))-1 > 0:
        mult = 1
    else:
        return
    inc = round(mult*10**(int(math.log10(userParams[0].value))-1), 5)
    ui.messageBox("Generating points for " + str(userParams[0].name) + " from " + str(p1) + " to " + str(p1end) + " with increment of " + str(inc))
    while p1 != p1end:
        #ui.messageBox("Generating point at " + str(userParams[0].name) + " = " + str(p))
        userParams.itemByName(str(userParams[0].name)).expression = str(p1) + ' in'
        body = root.bRepBodies.item(0)
        physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
        mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
        
        list1.append([p1, mass])
        p1 = round(p1+inc, 5)

    #ui.messageBox("Generated points: " + str(list1))
    #for i in range(1, NumSteps+1):
        #list1 = map(lambda x: x+inc, range(int(userParams[0].value)-((int(NumSteps)//2)*(int(math.log10(userParams[0].value))-1)), int(userParams[0].value)+((int(NumSteps)//2)*(int(math.log10(userParams[0].value))-1))+1, inc))
        #userParams[0].value+((NumSteps/2)*(int(math.log10(userParams[0].value)-1))), int(math.log10(userParams[0].value))-1
        #ui.messageBox("Value: " + str(int(userParams[0].value)-((int(NumSteps)//2)*(int(math.log10(userParams[0].value))-1))))
        #ui.messageBox("Generating point at " + str(userParams[0].name) + " = " + str(i))
        #userParams.itemByName(str(userParams[0].name)).expression = str(i) + ' in'
        #userParams.itemByName(str(userParams[0].name)).expression = str(float(unitsMgr.formatInternalValue(userParams[0].value, lenUnits, False))+1) + ' in'

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
                # PaletteUpdate()
                #FindDerivative(userParams[1].name)
                #AllDerivatives()
                #iterate()
                GeneratePoints(10)
                PaletteUpdate()
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

    # Sample iterative function to adjust parameter to reach target mass

# def iterate():
#     bodyMasses = []
#     for j in range(0, root.bRepBodies.count):
#         body = root.bRepBodies.item(j)
#         physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
#         mass = unitsMgr.formatInternalValue(physProps.mass, 'kg', False) #Converts mass from document mass units to kg
#         bodyMasses.append(mass)
#     ui.messageBox("Body Masses: " + str(bodyMasses))

#     currentDerivatives = AllDerivatives()
#     power = -1

#     importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated target mass values
#     TargetMasses = LCA_Interaction.TargetMasses() # Get the updated target mass values from the LCA_Interaction file
#     ui.messageBox("Target Masses: " + str(TargetMasses[0]))

#     while abs(TargetMasses[0]-float(bodyMasses[0])) > 0.1:
#         #ui.messageBox("Current derivative: " +  str(currentDerivatives[0][0]))
#         if ((TargetMasses[0]-float(bodyMasses[0])) > 0 and currentDerivatives[0][0] < 0) or ((TargetMasses[0]-float(bodyMasses[0])) < 0 and currentDerivatives[0][0] > 0):
#             while TargetMasses[0] - float(bodyMasses[0]) > 10**power:
#                 ui.messageBox("check 1")
#                 power = int(math.log10(abs(TargetMasses[0] - float(bodyMasses[0]))))
#                 ui.messageBox("Power: " + str(power))
#                 inc = -10**(power-1)/currentDerivatives[0][0]
#                 userParams.itemByName(str(userParams[0].name)).expression = str(float(unitsMgr.formatInternalValue(userParams[0].value, 'in', False))+inc) + ' in'
#                 bodyMasses[0] = unitsMgr.formatInternalValue(physProps.mass, 'kg', False)
#                 currentDerivatives[0][0] = FindDerivative(userParams[0])[0]
#             if TargetMasses[0]-float(bodyMasses[0]) == 0:
#                 ui.messageBox("check 2")
#                 return
#             else:
#                 ui.messageBox("check 3")
#                 ui.messageBox("Target Mass: " + str(TargetMasses[0]) + " Body Mass: " + str(bodyMasses[0]))
#                 power -= 1
#         elif ((TargetMasses[0]-float(bodyMasses[0])) > 0 and currentDerivatives[0][0] > 0) or ((TargetMasses[0]-float(bodyMasses[0])) < 0 and currentDerivatives[0][0] < 0):
#             while abs(TargetMasses[0] - float(bodyMasses[0])) > 10**power:
#                 ui.messageBox("check 4")
#                 #ui.messageBox("Target Mass: " + str(TargetMasses[0]) + " Body Mass: " + str(bodyMasses[0]))
#                 power = int(math.log10(abs(TargetMasses[0] - float(bodyMasses[0]))))
#                 #ui.messageBox("Power: " + str(power))
#                 inc = 10**(power-1)/currentDerivatives[0][0]
#                 #ui.messageBox("Increment: " + str(inc))
#                 #ui.messageBox("Current parameter value: " + str(unitsMgr.formatInternalValue(userParams[0].value, 'in', False)))
#                 #ui.messageBox("New parameter value: " + str(unitsMgr.formatInternalValue(userParams[0].value, 'in', False)))
#                 userParams.itemByName(str(userParams[0].name)).expression = str(float(unitsMgr.formatInternalValue(userParams[0].value, 'in', False)) + inc) + ' in'
#                 #ui.messageBox("Newnew parameter value: " + str(unitsMgr.formatInternalValue(userParams[0].value, 'in', False)))
#                 #ui.messageBox('New mass: ' + str(bodyMasses[0]))
#                 bodyMasses[0] = unitsMgr.formatInternalValue(physProps.mass, 'kg', False)
#                 #time.sleep(1)
#                 ui.messageBox("New parameter value: " + str(unitsMgr.formatInternalValue(userParams[0].value, 'in', False)))
#                 ui.messageBox("Updated Body Mass: " + str(bodyMasses[0]))
#                 currentDerivatives[0][0] = FindDerivative(userParams[0])[0]
#                 power -= 1
#             if TargetMasses[0]-float(bodyMasses[0]) == 0:
#                 ui.messageBox("check 5")
#                 return
#             else:
#                 ui.messageBox("check 6")
#                 ui.messageBox('Parameter updated to ' + unitsMgr.formatInternalValue(userParams[0].value, 'in', True))
#                 ui.messageBox("Target Mass: " + str(TargetMasses[0]) + " Body Mass: " + str(bodyMasses[0]))
#                 power -= 1
#                 return
#     ui.messageBox("check 7")
#     PaletteUpdate()
#     return