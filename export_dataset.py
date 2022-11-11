#@ PrefService prefs 
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

from dopmmvr import exportalldata

def main():
    Choices = ["none","hdf5","tiff"]
    gui = GenericDialogPlus("dOPM data processing with Multi-view fusion plugin")
    gui.addMessage("Select dOPM data processing option")
    gui.addChoice("Resave/export_data format?", Choices, Choices[0])
    gui.addMessage("Select dOPM data")
    gui.addDirectoryOrFileField("Choose data folder", prefs.get(None, "datapath_",""))
    gui.addDirectoryOrFileField("Choose export folder", prefs.get(None, "exportpath_",""))
    gui.showDialog() # dont forget to actually display the dialog at some point
 
    if gui.wasOKed():
    
        Choice = gui.getNextChoice()  
        datapath_ = gui.getNextString()
        exportpath_ = gui.getNextString() 
        
        prefs.put(None, "datapath_", datapath_)
        prefs.put(None, "exportpath_", exportpath_) 
        
        if Choice == Choices[1]:     
            data=exportalldata(datapath=datapath_)               
            data.ResaveXMLtoHDF5(exportpath_)
        elif Choice == Choices[2]:     
            data=exportalldata(datapath=datapath_)               
            data.ResaveXMLtoTiff(exportpath_)
        else:
            print 'other methods not implemented yet'       
    
if __name__ in ['__builtin__','__main__']:
     
    main()
    IJ.log("Finished")
