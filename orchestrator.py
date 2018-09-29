import os
import sys
import time
import numpy as np
import shutil
from subprocess import call

#
# Function to adjust input.dat
def edit_input(n):
    input_data = []
    with open('input_template', 'r') as f:
        for line in f:
            input_data.append(line)
    for i in range(len(input_data)):
        word = [x.strip() for x in input_data[i].split('=')]
        if word[0] == 'crack_length':
            input_data[i] = word[0] + ' = ' + str(float(word[1]) + n*0.25)
    with open('_next_input','w') as f:
        for a in input_data:
            f.write("%s"%a)
    return

#
# Main loop for Parametric study 
#
Ncases = 3
t0 = time.time()
for n in range (Ncases):
    #
    # 1. configures rid and new folder name
    run_id = "%4.4d"%(n)
    run_folder = 'rid'+run_id
    #
    # 2. makes a new folder or stop here
    try:
        os.makedirs(run_folder)
        print("making a folder", run_folder)
    except OSError:
        print("Run_id folder exists. Stops here")
        sys.exit()
    #
    # 3. copy abaqus script
    shutil.copy2('fracture.py', run_folder)
    #
    # 4. makes new input.data and moves it to the new folder
    edit_input(n)
    shutil.move('_next_input', run_folder+'/input.dat')
    #
    # 5. Runs Abaqus scripting
    print('Abaqus script runs at ', run_folder)
    os.chdir(run_folder)
    call_result = call("abaqus cae nogui=fracture",shell=True)
    if (call_result !=0):
        print("Abaqus failed at %d rid. Stops here\n"%n)
        sys.exit()
    else:
        print("rid%4.4d is completed\n"%n)
    os.chdir('..')

print ("Loops are done. Tested cases are %d and wall time = %.1f sec"
       %(n, time.time() - t0))
