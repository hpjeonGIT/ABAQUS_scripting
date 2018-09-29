import os
import sys                                                          
import time
import numpy as np
import shutil
from subprocess import call

def extract_data():
    # 1. Extract crack length
    input_data = []
    crack_length = None
    with open('input.dat', 'r') as f:
        for line in f:
            input_data.append(line)
    for i in range(len(input_data)):
        word = [x.strip() for x in input_data[i].split('=')]
        if word[0] == 'crack_length':
            crack_length = float(word[1])
    # 2. Extract fracture parameters
    K1 = None; K2 = None; J = None; T = None
    with open('summary_fracture.dat', 'r') as f:
        for line, n in zip(f,range(8)):
            word = line.split(' ')
            if(n==1):
                K1 = np.mean(map(float,word[0:-1]))
            if(n==3):
                K2 = np.mean(map(float,word[0:-1]))
            if(n==5):
                J = np.mean(map(float,word[0:-1]))
            if(n==7):
                T = np.mean(map(float,word[0:-1]))
    return crack_length, K1, K2, J, T

if __name__=="__main__":
    target_folder = []
    CWD = os.getcwd()
    if len(sys.argv)> 1:
        DEST = sys.argv[1]
    else:
        DEST = os.getcwd()

    print("DEST folder = ", DEST)
    f0_list = []
    for subds, dirs, files in os.walk(DEST):
        for d0 in dirs:
            if len(d0) > 3:
                if (d0[0:3] == 'rid'):
                    target_folder.append(d0)
                    
    ##
    pic_file = 'mesh_01.png'
    pic_folder = 'GIF'
    try:
        os.makedirs(pic_folder)
    except IOError:
        print(pic_folder, " exists")    
    target_folder.sort()
    #
    rid_list = []
    cl_list = []; K1_list = []; K2_list = []; J_list = []; T_list = []
    for dirname in target_folder:
        rid = int(dirname[3:])
        os.chdir(DEST+'/'+dirname)
        try:
            shutil.copy2(pic_file,'../'+pic_folder+'/'+dirname+'.png')
        except OSError:
            print(pic_file, " doesn't exisit")
        ans = extract_data()
        if ans[0] == None:
            print('input error at %4.4d'%(rid))
        elif ans[1] == None:
            print('Fracture result error at %4.4d'%(rid))
        else:
            print('Results returned from %4.4d'%(rid))
            rid_list.append(rid)
            cl_list.append(ans[0])
            K1_list.append(ans[1])
            K2_list.append(ans[2])
            J_list.append( ans[3])
            T_list.append( ans[4])
        
            
    os.chdir(CWD+'/'+pic_folder)
    call_result = call("convert -delay 50 -loop 0 rid*.png ani.gif", shell=True)
    os.chdir(CWD)
    with open('all_results.dat','w') as f:
        f.write('# rid, crack_length, K1,K2,J,T\n')
        for rid, cl, K1, K2, J, T in zip(rid_list, cl_list, K1_list, K2_list, 
                                         J_list, T_list):
            f.write("%d, %.4e, %.4e, %.4e, %.4e, %.4e\n"%(rid, cl, K1, K2, J, T))

