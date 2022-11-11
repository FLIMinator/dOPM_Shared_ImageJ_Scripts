#@ PrefService prefs 
#@ String (visibility=MESSAGE, value=":)", required=false) msg
#@ File[] (label="Select list of dOPM folders for batch processing", style="directories") folders

from fiji.util.gui import GenericDialogPlus 
from ij import IJ
import os
from  os.path import isfile
from sys import path
from java.lang.System import getProperty

#code_path = 'C:/Users/CRICKOPMuser/Documents/GitHub/dOPM_Shared_ImageJ_Scripts/testing'
code_path = getProperty('fiji.dir') + '/bin'



# Delete the compiled class file otherwise we can not dynamically update the imported module
ScriptPath = code_path+"/dopmmvr$py.class"
path.append(code_path)

if isfile(ScriptPath):
	os.remove(ScriptPath)

from dopmmvr import *
   
def main():

    IJ.log("chosen list of folders to batch over") 
    for folder in folders:
        IJ.log(str(folder))

    cropchoices =["yes","no"]
    binning_choices = ["1","2","4","8","16"]

    # Create an instance of GenericDialog
    gui = GenericDialogPlus("dOPM data processing with Multi-view fusion plugin")         
    gui.addDirectoryOrFileField("Choose bead dataset folder", prefs.get(None, "beadpath_",""))       
    gui.addChoice("Choose voxel binning factor", binning_choices, binning_choices[0])
    gui.addChoice("Do you want to crop the data?", cropchoices, cropchoices[0])
    gui.showDialog() 

    if gui.wasOKed():
    
        beadpath_ = gui.getNextString()
        binning_ = gui.getNextChoice()
        cropchoice = gui.getNextChoice()
        
        prefs.put(None, "beadpath_", beadpath_)
        prefs.put(None, "binning_", binning_) 
             
        if cropchoice == cropchoices[0]: # global variable used in class instances
            BB = "My Bounding Box"
        else:  
            BB = 'All Views'      
        
        mvrgetvolumes.BB = BB
        
        BoundingBox=defineboundingbox() 
        BB_ = BoundingBox.getXMLBoundingBox(beadpath_)
                      
        for folder in folders:
            datapath_ = str(folder)
            print("Processing Folder: "+ datapath_)
            savepath_ = os.path.join(datapath_,"processed")     
            BoundingBox.defineBoundingBoxNoInteraction(datapath_)
            BoundingBox.modifyBoundingBox(datapath_,BB_) 
            
            data=mvrgetvolumes(\
            datapath=datapath_, \
            savepath=savepath_, \
            binning= binning_)     
            data.getFusedVolumes()
            
if __name__ in ['__builtin__','__main__']:
    main()
    IJ.log("Finished")
    
    

