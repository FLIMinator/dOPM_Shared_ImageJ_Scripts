#@ PrefService prefs 
#@ String (visibility=MESSAGE, value=":)", required=false) msg
#@ File[] (label="Select list of dOPM folders for batch processing", style="directories") folders

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

from dopmmvr import *
   
def main():

    IJ.log("chosen list of folders to batch over") 
    for folder in folders:
        IJ.log(str(folder))

    choices =["yes","no"]
   
    # Create an instance of GenericDialog
    gui = GenericDialogPlus("dOPM data processing with Multi-view fusion plugin")
    
    #gui.addChoice("Do you want to apply bead registration?", choices, choices[0])
         
    filepatternchoices = ["spim_Time{tttt}_Tile{xxxx}_angle{a}","spim_Time{tttt}_Tile{xxxx}_channel{c}_angle{a}"]
    extenstionchoices = [".nd2",".tif",".tiff"]   
    
    gui.addDirectoryOrFileField("Choose bead dataset folder", prefs.get(None, "beadpath_",""))       
    gui.addChoice("Image file extension", extenstionchoices, extenstionchoices[0]) 
    gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0]) 
    gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2) 
    gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2) 
    gui.addChoice("Do you want to export the data to hdf5?", choices, choices[0])
    gui.showDialog() 

    
    if gui.wasOKed():
    
        beadpath_ = gui.getNextString()
        extension_ = gui.getNextChoice()
        filepattern_ = gui.getNextChoice()
        pixel_ = gui.getNextNumber()
        angle_ = gui.getNextNumber()
        exportdata = gui.getNextChoice()
        
        # ######## go grab most recent bead reg info
        beads=mvrsetup(\
        datapath=beadpath_, \
        regpath= r'', \
        filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
        extension=extension_, \ 
        px=pixel_, \ 
        py=pixel_, \ 
        angle=angle_)     
        beads.getAffineTransformations()
        # ######## go grab most recent bead reg info    
         
        for folder in folders:

            print("Processing Folder: "+str(folder))
            
            sample=mvrsetup(\
            datapath=str(folder), \
            regpath= beadpath_, \
            filepattern=filepattern_, \ 
            extension=extension_, \ 
            px=pixel_, \ 
            py=pixel_, \ 
            angle=angle_)      

            sample.createXMLdataset()
            sample.getCalibrations()
            sample.ApplyCalibration()       
            sample.ApplyBeadRegCSV()

            if exportdata == choices[0]:          
                sample=exportalldata(datapath=str(folder)) 
                exportpath = os.path.join(str(folder),'hdf5') 
                sample.createFolder(exportpath)           
                sample.ResaveXMLtoHDF5(exportpath)
            
if __name__ in ['__builtin__','__main__']:
    main()
    IJ.log("Finished")