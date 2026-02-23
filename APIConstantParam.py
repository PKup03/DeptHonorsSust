### Live code, check below for test code
import adsk.core, traceback, adsk.fusion, importlib
import json, os, adsk.cam
import math, time, csv
from .LCA_Interaction import Parameters
from .LCA_Interaction import TargetMasses

#File stuff
script_dir = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(script_dir, "output.csv")

# global set of event handlers to keep them referenced
handlers = []
app = adsk.core.Application.get()
ui  = app.userInterface
des = adsk.fusion.Design.cast(app.activeProduct)
unitsMgr = des.unitsManager
userParams = des.userParameters
root = des.rootComponent

# Specifying units
lenUnits = 'in'  # inches (can be changed to 'mm' for millimeters, etc.)
massUnits = 'kg'  # kilograms (can be changed to 'g' for grams, etc.)

ParamEdits = ["Y", "Y", "Y", "N"].count("Y") # Number of parameters to be edited by the user
ui.messageBox("Number of parameters being edited: " + str(ParamEdits))

palette = ui.palettes.add('partMasses', 'Part Masses', 'palette.html', False, True, True, 300, 200, True)
# The True/Falses control whether the palette is visible, if a 'Close' button is shown, and if the palette can be resized
palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
palette.isVisible = True

def PaletteUpdate():
    # Code to react to the event.
    bodyMasses = []
    massesStrText = ""

    if userParams:
        #Determine mass of each body in the component
        for j in range(0, root.bRepBodies.count):
            body = root.bRepBodies.item(j)
            physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
            mass = unitsMgr.formatInternalValue(physProps.mass, massUnits, False) #Converts mass from document mass units to selected mass units
            bodyMasses.append(mass)
            # ui.messageBox('Body' + str(j+1) + ' has a mass of ' + str(bodyMasses[j]) + " kg")
            massesStrText += '<b>' + root.bRepBodies[j].name + ' mass:</b> ' + str(bodyMasses[j]) + ' ' + str(massUnits) + "<br />" #The ending is for HTML line breaks
            #massesStrText += '<b>Body ' + str(j+1) + '</b> mass: ' + str(bodyMasses[j]) + ' kg' + "<br />" #The ending is for HTML line breaks
            palette.sendInfoToHTML('send', massesStrText)

    else:
        ui.messageBox('Global parameter not found.')

Combos = [[]]
mult = []
for i in range(0, userParams.count):
    Combos[0].append(unitsMgr.formatInternalValue(userParams[i].value, lenUnits, False))
    mult.append(0)
ui.messageBox("Combos: " + str(Combos))

def GeneratePoints(NumPoints, SelectedCombo):
    #Create a range of points around the current parameter value with a step size one decade smaller than the parameter value
    global Combos
    global mult
    global csvlen
    global writer
    p1Center = float(Combos[SelectedCombo][0])
    p2Center = float(Combos[SelectedCombo][1])
    NumSteps = NumPoints**(1/ParamEdits) # Number of points to be generated for each parameter, adjusted for number of parameters being edited
    p1 = round(p1Center+round(NumSteps//2)*10**(int(math.log10(p1Center))-1), 5)
    p1end = round(p1Center-round(NumSteps//2)*10**(int(math.log10(p1Center))-1), 5)
    Combos = [[str(userParams[0].name), str(userParams[1].name), str(userParams[2].name), 'Body 1', 'Body 2', 'Body 3']]
    if int(math.log10(p1Center))-1 < 0:
        mult[0] = -1
    elif int(math.log10(p1Center))-1 > 0:
        mult[0] = 1
    else:
        return
    inc = round(int(mult[0])*10**(int(math.log10(p1Center))-1), 5)
    #ui.messageBox("Generating points for " + str(userParams[0].name) + " from " + str(p1) + " to " + str(p1end) + " with increment of " + str(inc))
    while p1 != p1end and p1 > 0:
        #ui.messageBox("Generating points at " + str(userParams[0].name) + " = " + str(p1))
        userParams.itemByName(str(userParams[0].name)).expression = str(p1) + ' ' + str(lenUnits)
        
        p2 = round(p2Center+round(NumSteps//2)*10**(int(math.log10(p2Center))-1), 5)
        p2end = round(p2Center-round(NumSteps//2)*10**(int(math.log10(p2Center))-1), 5)
        if int(math.log10(p2Center))-1 < 0:
            mult[1] = -1
        elif int(math.log10(p2Center))-1 > 0:
            mult[1] = 1
        else:
            return
        #ui.messageBox("Generating points for " + str(userParams[1].name) + " from " + str(p2) + " to " + str(p2end) + " with increment of " + str(inc))
        while p2 != p2end and p2 > 0:
            #ui.messageBox("Generating point at " + str(userParams[1].name) + " = " + str(p2))
            userParams.itemByName(str(userParams[1].name)).expression = str(p2) + ' in'

            p3 = p1
            while p3 >= p1 and p3 <= p1+1:
                userParams.itemByName(str(userParams[2].name)).expression = str(p3) + ' ' + str(lenUnits)

                masses = []
                for i in range(0, int(root.bRepBodies.count)):
                    body = root.bRepBodies.item(i)
                    physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
                    mass = unitsMgr.formatInternalValue(physProps.mass, massUnits, False) #Converts mass from document mass units to selected mass units
                    masses.append(mass)

                # Combos.append([p1, p2, p3])
                Combos.append([p1, p2, p3] + masses)
                p3 = round(p3+0.1, 5)
            inc = round(int(mult[1])*10**(int(math.log10(p2Center))-1), 5)
            p2 = round(p2+inc, 5)
        inc = round(int(mult[0])*10**(int(math.log10(p1Center))-1), 5)
        p1 = round(p1+inc, 5)
    #ui.messageBox("Generated points: " + str(Combos))
    with open(filepath, 'w+', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(Combos)
        csvlen = len(Combos)


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
        global csvlen, Combos, writer
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
                GeneratePoints(27, 0)
                PaletteUpdate()
                ui.messageBox("Check 1")
                ui.messageBox(str(csvlen) + " vs " + str(len(Combos)))
                while csvlen == len(Combos) and csvlen != 0:
                    with open(filepath, 'r') as file:
                        my_reader = csv.reader(file, delimiter=',')
                        csvlen = len(list(my_reader))
                        ui.messageBox(str(csvlen) + " vs " + str(len(Combos)))
                    if csvlen != len(Combos) and csvlen != 0:
                        GeneratePoints(27, 9)
                        ui.messageBox("Data generation complete. Generated " + str(len(Combos)) + " points.")
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


    #Sample function to find the derivative of mass with respect to a parameter
# def FindDerivative(paramName):
#         bodyMasses = []
#         bodyMassesNew = []
#         BodyDerivatives = []
#         # ## Set the new value for the global parameter
#         # importlib.reload(LCA_Interaction) # Reload the LCA_Interaction file to get updated parameter values
#         # Parameters = LCA_Interaction.Parameters() # Get the updated parameter values from the LCA_Interaction file
#         # userParams.itemByName(str(paramName.name)).expression = str(paramName.value) + ' in'
#         #Find initial mass of each body in the component
#         for j in range(0, root.bRepBodies.count):
#             body = root.bRepBodies.item(j)
#             physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
#             mass = unitsMgr.formatInternalValue(physProps.mass, massUnits, False) #Converts mass from document mass units to selected mass units
#             bodyMasses.append(mass)
#         #Set the new value for the global parameter
#         userParams.itemByName(str(paramName.name)).expression = str((float(unitsMgr.formatInternalValue(paramName.value, lenUnits, False))+0.0001)) + ' ' + str(lenUnits)
#         #Find new body masses after parameter change
#         for j in range(0, root.bRepBodies.count):
#             body = root.bRepBodies.item(j)
#             physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties)
#             mass = unitsMgr.formatInternalValue(physProps.mass, massUnits, False) #Converts mass from document mass units to selected mass units
#             bodyMassesNew.append(mass)
#         #Calculate and display derivative of mass with respect to parameter
#         for j in range(0, root.bRepBodies.count):
#             BodyDerivatives.append((float(bodyMassesNew[j])-float(bodyMasses[j]))/0.0001)
#         #ui.messageBox('Derivative of ' + root.bRepBodies[0].name + ' mass with respect to ' + paramName.name + ' is ' + str(BodyDerivatives[0]) + ' kg/in')
#         return BodyDerivatives


    #Sample function to find derivative of mass for all bodies with respect to parameters being changed
# def AllDerivatives():
#     currentDerivatives = []
#     for i in range(0, userParams.count-1):
#         currentDerivatives.append(FindDerivative(userParams[i]))
#     #ui.messageBox(str(currentDerivatives))
#     return currentDerivatives


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