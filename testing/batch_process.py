#@ PrefService prefs 
#@ File[] (label="Select some directories", style="directories") listdirs
from fiji.util.gui import GenericDialogPlus 
from ij import IJ
import os
from  os.path import isfile
from sys import path
from java.lang.System import getProperty

code_path = 'C:/Users/CRICKOPMuser/Documents/GitHub/dOPM_Shared_ImageJ_Scripts/testing'
#code_path = getProperty('fiji.dir') + '/plugins/Scripts/dOPM'

# Delete the compiled class file otherwise we can not dynamically update the imported module
ScriptPath = code_path+"/dopmmvr$py.class"
path.append(code_path)

if isfile(ScriptPath):
	os.remove(ScriptPath)

from dopmmvr import mvrsetup

def checkdataset(pathname):
	if os.path.isdir(pathname):
		if os.path.exists(pathname+os.path.sep+"dataset.xml"):
			return True
	return False
    
def main():

    choices =["yes","no"]
   
    # Create an instance of GenericDialog
    gui = GenericDialogPlus("dOPM data processing with Multi-view fusion plugin")
    
    gui.addDirectoryOrFileField("Choose directory to batch over", prefs.get(None, "datadir",""))
    
    gui.addChoice("Do you want to apply bead registration?", choices, choices[0])
    gui.addToSameRow()
    gui.addDirectoryOrFileField("Choose bead dataset folder", prefs.get(None, "beadpath",""))
    
    gui.addChoice("Do you want to crop the data based on the bead dataseta bounding box definition?", choices, choices[0])
       
    gui.showDialog() 
    
    datadir = gui.getNextString()
    beaddpath = gui.getNextString()
    
    regfrombeads = gui.getNextChoice()
    cropfrombeads = gui.getNextChoice()
    
    base = str(datadir)
    files = os.listdir(base)
    files = [ base+"/"+f for f in files]
    
    IJ.log(base)
     
    [x for x in files if x != beaddpath]
    
    for file in files:
         IJ.log(file)

    datafolders= filter(checkdataset, files)
    print(datafolders) 

    # for folder in datafolders:

        # print("Processing Folder "+folder)
        
        # sample=mvrsetup(\
        # datapath=datapath_, \
        # regpath= beadpath_, \
        # filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
        # extension=extension_, \ 
        # px=pixel_, \ 
        # py=pixel_, \ 
        # angle=angle_)      

        # sample.createXMLdataset()
        # sample.getCalibrations()
        # sample.ApplyCalibration()
        
        # # ######## go grab most recent bead reg info
        # beads=mvrsetup(\
        # datapath=beadpath_, \
        # regpath= r'', \
        # filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
        # extension=extension_, \ 
        # px=pixel_, \ 
        # py=pixel_, \ 
        # angle=angle_)     
        # beads.getAffineTransformations()
        # # ######## go grab most recent bead reg info


if __name__ in ['__builtin__','__main__']:
    
    main()
    IJ.log("Finished")