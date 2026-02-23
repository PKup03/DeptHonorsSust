import os
script_dir = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(script_dir, "output.csv")

# while csvlen == len(Combos) and csvlen != 0:
#                     with open(filepath, 'r') as file:
#                         my_reader = csv.reader(file, delimiter=',')
#                         csvlen = len(list(my_reader))
#                         ui.messageBox(str(csvlen) + " vs " + str(len(Combos)))
#                     if csvlen != len(Combos) and csvlen != 0:
#                         GeneratePoints(27, 9)
#                         ui.messageBox("Data generation complete. Generated " + str(len(Combos)) + " points.")

open(filepath, 'w').close()