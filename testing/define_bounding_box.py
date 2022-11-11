#@ PrefService prefs 
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

from dopmmvr import defineboundingbox

def main():
    # Create an instance of GenericDialog
    gui = GenericDialogPlus("Define bounding box for dataset")
    gui.addDirectoryOrFileField("apply bounding box to dataset:", prefs.get(None, "datapath_",""))
    gui.addDirectoryOrFileField("get bounding box from bead dataset:", prefs.get(None, "beadpath_",""))
    methodchoice = ["define box","use existing box","automatic based dopm geometry"]
    gui.addChoice("Reuse a bounding box definition or make a new one?", methodchoice, methodchoice[0]) #
    gui.showDialog() # dont forget to actually display the dialog at some point

    if gui.wasOKed():
        
        datapath_ = gui.getNextString()
        beadpath_ = gui.getNextString()
        choice =gui.getNextChoice()
        prefs.put(None, "datapath_", datapath_)
        prefs.put(None, "beadpath_", beadpath_)
         
        BoundingBox=defineboundingbox() 
        # BoundingBox.deleteBoundingBox(beadpath_)
        
        if methodchoice[0] == choice:
            # define bounding box based on corresponding bead volume
            BoundingBox.defineBoundingBox(beadpath_)
            BB = BoundingBox.getXMLBoundingBox(beadpath_)
            # apply bead volume defined bounding box to data
            BoundingBox.defineBoundingBoxNoInteraction(datapath_)
            BoundingBox.modifyBoundingBox(datapath_,BB)                
        elif methodchoice[2] == choice:
            BB = BoundingBox.OptimalBoundingBox(beadpath_)
            BoundingBox.defineBoundingBoxNoInteraction(beadpath_)
            BoundingBox.modifyBoundingBox(beadpath_,BB)  
            BoundingBox.defineBoundingBoxNoInteraction(datapath_)
            BoundingBox.modifyBoundingBox(datapath_,BB)  
        else:
            BB = BoundingBox.getXMLBoundingBox(beadpath_)
            # apply bead volume defined bounding box to data
            BoundingBox.defineBoundingBoxNoInteraction(datapath_)
            BoundingBox.modifyBoundingBox(datapath_,BB)            
      
    
if __name__ in ['__builtin__','__main__']:
     
    main()
    IJ.log("Finished")
    