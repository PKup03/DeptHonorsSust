import os, csv
script_dir = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(script_dir, "output.csv")

## Initializing variables
csvlen = len(list(csv.reader(open(filepath, 'r', delimiter=','))))
counter = 1 #Variable to count the number of iterations, limiting the number of iterations

## Define OpenLCA function here

## Iteration logic
# while counter == 1 or csvlen == len(Output) and csvlen != 0:
#     if counter == 10: #Checks to see if the loop has iterated enough times
#         open(filepath, 'w').close() #To clear the file
#         break
#     with open(filepath, 'r') as file:
#         my_reader = csv.reader(file, delimiter=',')
#         csvlen = len(list(my_reader))
#     if csvlen != len(Output) and csvlen != 0:
#         OpenLCAFunction() #Function that generates the sustainability data and provides an Output to output.csv
#         counter += 1 #Increments the counter, representing one iteration of the full loop

open(filepath, 'w').close()