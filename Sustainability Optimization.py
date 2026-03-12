### Live code, check below for test code
import adsk.core, traceback, adsk.fusion #, adsk.cam
import json, os
import math, csv #math is used for the log10 function, csv is used to write to an intermediate CSV file for data storage

### File directory setup - adjust the filepath as needed for your system. The current setup is for a fixed filepath to cloud storage using Box tools, but the commented-out option can be used for a relative filepath to the CSV file (using the active directory).
#script_dir = os.path.dirname(os.path.abspath(__file__)) #For a relative filepath to the CSV file (uses active directory)
script_dir = "C:/Users/pksc8/Box/Mabey Research Group Files/CAD Sustainability Optimization" #For a fixed filepath to cloud storage using Box tools
filepath = os.path.join(script_dir, "Coffee_cup_data.csv") #Name of the CSV file to be created with parameter values and body masses

### Specifying units
lenUnits = 'in'  # inches (can be changed to 'mm' for millimeters, etc.)
massUnits = 'kg'  # kilograms (can be changed to 'g' for grams, etc.)

### Parameters to be changed in optimization process
ParamEdits = ["Y", "Y", "Y", "N"] # Marking parameters to be changed with "Y" and parameters to be held constant with "N". The order of the parameters is determined by the order of the parameters in the Fusion model. In this case, the first three parameters in the Fusion model will be changed and the fourth parameter will be held constant.
#ui.messageBox("Number of parameters being edited: " + str(ParamEdits.count("Y"))) # Display the number of parameters to be edited when starting the add-in, for confirmation

### Global variables
handlers = []
app = adsk.core.Application.get()
ui  = app.userInterface
des = adsk.fusion.Design.cast(app.activeProduct)
unitsMgr = des.unitsManager
userParams = des.userParameters
root = des.rootComponent
Combos = [[]] 
mult = []
Center = []

### Palette setup
palette = ui.palettes.add('partMasses', 'Part Masses', 'palette.html', False, True, True, 300, 200, True)
# The True/Falses control whether the palette is visible, if a 'Close' button is shown, and if the palette can be resized
palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
palette.isVisible = True

### Palette Update Function
# Function to update the palette with the current body masses, called after points are generated for the updated parameter values.
def PaletteUpdate():
    # Initialize variables to blanks.
    bodyMasses = []
    massesStrText = ""

    # Determine mass of each body in the component
    for j in range(0, root.bRepBodies.count): # For each body in the component...
        body = root.bRepBodies.item(j) # Get the body
        physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties) # Get the physical properties of the body, which includes mass, volume, etc.
        mass = unitsMgr.formatInternalValue(physProps.mass, massUnits, False) #Converts mass from document mass units to desired mass units
        bodyMasses.append(mass) # Add the mass of the current body to the list of body masses
        # ui.messageBox('Body' + str(j+1) + ' has a mass of ' + str(bodyMasses[j]) + " kg") # Display the mass of the current body in a message box (for confirmation)
        massesStrText += '<b>' + root.bRepBodies[j].name + ' mass:</b> ' + str(bodyMasses[j]) + ' ' + str(massUnits) + "<br />" # Format text display for HTML, which is used by the palette
        palette.sendInfoToHTML('send', massesStrText) # Send the formatted text to the palette to be displayed

for i in range(0, userParams.count): # For each user parameter in the Fusion model...
    Combos[0].append(unitsMgr.formatInternalValue(userParams[i].value, lenUnits, False)) # Add the current parameter value to the Combos list, converting from document units to desired length units
    mult.append(0)
ui.messageBox("Combos: " + str(Combos)) # Display the initial parameter values (for confirmation)

### Generate Points Function
# Function that creates a range of points around the current parameter value with a step size one decade smaller than the parameter value
def GeneratePoints(NumPoints, SelectedCombo):
    # Make the global variables accessible within the function
    global Combos
    global mult
    global csvlen
    global writer

    # Identify the central (current) parameter values for the parameters being edited, which will be used as the basis for generating points around them. This is determined by the SelectedCombo variable, which is the index of the row in the Combos list that contains the current parameter values.
    for i in range(0, userParams.count): # For each user parameter in the Fusion model...
        if ParamEdits[i] == "Y":
            Center.append(float(Combos[SelectedCombo][i])) # Add the parameter values for the selected design to the Center list, which will be used as the basis for generating points around it

    # 
    NumSteps = NumPoints**(1/ParamEdits.count("Y")) # Number of points to be generated for each parameter, adjusted for number of parameters being edited
    p1 = round(Center[0]+round(NumSteps//2)*10**(int(math.log10(Center[0]))-1), 5) # Starting point for first parameter, which is the center value plus half the number of steps (to generate points above and below the center value)
    p1end = round(Center[0]-round(NumSteps//2)*10**(int(math.log10(Center[0]))-1), 5) # End point for first parameter, which is the center value minus half the number of steps
    #Combos = [[str(userParams[0].name), str(userParams[1].name), str(userParams[2].name), 'Mass_cup', 'Mass_lid', 'Mass_packaging']]
    ## Setting the column headers for the CSV file to be the parameter names and mass names.
    Combos = [[]] #Reset Combos
    for i in range(0, int(userParams.count)): # For all parameters...
        if ParamEdits[i] == "Y": # If the parameter is being edited...
            Combos[0].append(str(userParams[i].name)) # Add the parameter name to the header
    for i in range(0, int(root.bRepBodies.count)): # For all bodies...
        Combos[0].append("Mass_"+str(root.bRepBodies.item(i).name)) # Add the mass name to the header
    ## Logic to determine if the center value is less than 10, which would require a smaller step size to generate points that are not the same due to rounding. If the center value is less than 10, the increment will be negative, meaning points will be generated by subtracting from the center value. If the center value is greater than 10, the increment will be positive, meaning points will be generated by adding to the center value.
    if int(math.log10(Center[0]))-1 < 0:
        mult[0] = -1
    elif int(math.log10(Center[0]))-1 > 0:
        mult[0] = 1
    else:
        return
    inc = round(int(mult[0])*10**(int(math.log10(Center[0]))-1), 5) # Define initial increment for generating points
    while p1 != p1end and p1 > 0: # While the current point value is not equal to the end point value and is greater than 0 (to avoid generating negative parameter values)...
        userParams.itemByName(str(userParams[0].name)).expression = str(p1) + ' ' + str(lenUnits) # Set the parameter value in Fusion to the current point value, converting to a string and adding the chosen units for the expression
        
        p2 = round(Center[1]+round(NumSteps//2)*10**(int(math.log10(Center[1]))-1), 5) # Starting point for second parameter, which is the center value plus half the number of steps (to generate points above and below the center value)
        p2end = round(Center[1]-round(NumSteps//2)*10**(int(math.log10(Center[1]))-1), 5) # End point for second parameter, which is the center value minus half the number of steps
        if int(math.log10(Center[1]))-1 < 0:
            mult[1] = -1
        elif int(math.log10(Center[1]))-1 > 0:
            mult[1] = 1
        else:
            return
        while p2 != p2end and p2 > 0:
            userParams.itemByName(str(userParams[1].name)).expression = str(p2) + ' in' # Set the parameter value in Fusion to the current point value, converting to a string and adding the chosen units for the expression

            p3 = p1 # Starting point for third parameter, which is the same as the first parameter (this is because the top of the coffee cup shouldn't be smaller than the bottom)
            while p3 >= p1 and p3 <= p1+1:  # While the third parameter value is between the first parameter value and the first parameter value plus 1 (this is to avoid generating points where the top of the coffee cup is smaller than the bottom, which would not be a valid design)...
                userParams.itemByName(str(userParams[2].name)).expression = str(p3) + ' ' + str(lenUnits) # Set the parameter value in Fusion to the current point value, converting to a string and adding the chosen units for the expression

                masses = [] # Clear the masses list to store the new body masses for the current parameter values
                for i in range(0, int(root.bRepBodies.count)): # For each body in the component...
                    body = root.bRepBodies.item(i) # Define the body
                    physProps = adsk.fusion.PhysicalProperties.cast(body.physicalProperties) # Get the physical properties of the body, which includes mass, volume, etc.
                    mass = unitsMgr.formatInternalValue(physProps.mass, massUnits, False) #Converts mass from document mass units to selected mass units
                    masses.append(mass) # Store the mass of the current body in the masses list
                Combos.append([p1, p2, p3] + masses) # Add the current parameter values and body masses to the Combos list as a new row, concatenated to form a single list for the row
                p3 = round(p3+0.1, 5) # Increment the third parameter by 0.1
            inc = round(int(mult[1])*10**(int(math.log10(Center[1]))-1), 5) # Define the increment for the second parameter, which is based on the order of magnitude of the center value for that parameter and whether the points are being generated in the positive or negative direction
            p2 = round(p2+inc, 5) # Increment the second parameter by the defined increment
        inc = round(int(mult[0])*10**(int(math.log10(Center[0]))-1), 5) # Define the increment for the first parameter, which is based on the order of magnitude of the center value for that parameter and whether the points are being generated in the positive or negative direction
        p1 = round(p1+inc, 5) # Increment the first parameter by the defined increment

    ## After generating points for all parameter combinations, write the Combos list to the CSV file. Each row in the Combos list will be a row in the CSV file, with the parameter values and body masses as columns.
    with open(filepath, 'w+', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(Combos)
        csvlen = len(Combos) # Store the length of the CSV file (number of rows) in a variable to be used for comparison with the length of the Combos list in the palette update function, to determine when the palette has been updated to move to the next iteration.


### Event handler for the cameraChanged event to remove the palette, allowing for the Add-In to be re-run without restarting Fusion 360.
class MyCameraMovedHandler(adsk.core.CameraEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Code to react to the event.
        app.log('In MyDocumentSavedHandler event handler.')
        palette.deleteMe()

### Event handler for the incomingFromHTML event, which is fired from the palette when the "Generate Points" button is clicked. This will trigger the generation of points and updating of the palette with the new body masses.
class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        global csvlen, Combos, writer
        try:
            htmlArgs = adsk.core.HTMLEventArgs.cast(args)
            Firing = json.loads(htmlArgs.data)
            if Firing == 'Firing':
            # data = json.loads(htmlArgs.data)
            # msg = "An event has been fired from the html to Fusion with the following data:\n"
            # msg += '    Command: {}\n    arg1: {}\n    arg2: {}'.format(htmlArgs.action, data['arg1'], data['arg2'])
                GeneratePoints(1000, 0) # Generate ~1000 points around the current parameter values (off due to the third parameter not flexibly changing size)
                PaletteUpdate() # Update the palette with the new body masses for the generated points
                #ui.messageBox("Check 1") # For confirmation that the process is complete
                ui.messageBox(str(csvlen) + " vs " + str(len(Combos))) # Display the length of the CSV file and the length of the Combos list for confirmation that they match, which determines when the palette has been updated to move to the next iteration.
                ## Iterative logic to check when the CSV file has been updated, which will be the baseline for the next iteration.
                # while csvlen == len(Combos) and csvlen != 0: # While the length of the CSV file is equal to the length of the Combos list and the CSV file is not empty (which can be used to indicate the process is complete)...
                #     with open(filepath, 'r') as file: # Read the CSV file to check its length
                #         my_reader = csv.reader(file, delimiter=',')
                #         csvlen = len(list(my_reader))
                #         ui.messageBox(str(csvlen) + " vs " + str(len(Combos)))
                #     if csvlen != len(Combos) and csvlen != 0: # If the length of the CSV file has changed (and is not empty)...
                #         #Logic will have to be added here to read the selected solution and compare versus the Combos list to find the index of the selected solution in the Combos list, which will be used as the SelectedCombo variable for the next iteration of point generation around the new parameter values.
                #         GeneratePoints(1000, ^see note above) # Generate a new dataset of points around the new parameter values based on the selected solution, which will be determined in the above line.
                #         PaletteUpdate() # Update the palette with the new body masses for the generated points
                #         ui.messageBox("Data generation complete. Generated " + str(len(Combos)) + " points.") # For confirmation that the process is complete and to display the number of points generated in the new dataset.
                del Firing
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    try:
        ### Handler that fires when the document is saved.
        # onDocumentSaved = MyDocumentSavedHandler()
        # app.documentSaved.add(onDocumentSaved)
        # handlers.append(onDocumentSaved)

        ### Handler the fires when the palette triggers an event (which happens when the "Click to Begin Optimization" button is clicked)
        onHTMLEvent = MyHTMLEventHandler()
        palette.incomingFromHTML.add(onHTMLEvent)   
        handlers.append(onHTMLEvent)

        ### Handler that fires when the camera is moved, which deletes the palette to allow for the Add-In to be re-run without restarting Fusion 360.
        onCameraMoved = MyCameraMovedHandler()
        app.cameraChanged.add(onCameraMoved)
        handlers.append(onCameraMoved)
    except:
        app.log('AddIn Start Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        pass
    except:
        app.log('AddIn Stop Failed: {}'.format(traceback.format_exc()))