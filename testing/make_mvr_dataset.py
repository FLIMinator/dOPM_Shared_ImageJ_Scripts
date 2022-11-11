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

from dopmmvr import *

def main():
    choices =["Transform & register beads", "Transform & register data","Transform two-view data without registering","Transform one-view data"]
    # Create an instance of GenericDialog
    gui = GenericDialogPlus("dOPM data processing with Multi-view fusion plugin")
    gui.addMessage("Select dOPM data processing option")
    gui.addChoice("Choose one option among a list", choices, choices[0])
    #gui.addHelp(r"https://imagej.net/Generic_dialog") # clicking the help button will open the provided URL in the default browser
    gui.showDialog() # dont forget to actually display the dialog at some point
    # If the GUI is closed by clicking OK, then recover the inputs in order of "appearance"
    
    if gui.wasOKed():
        filepatternchoices = ["spim_Time{tttt}_Tile{xxxx}_angle{a}","spim_Time{tttt}_Tile{xxxx}_channel{c}_angle{a}"]
        extenstionchoices = [".nd2",".tif",".tiff"]
        inChoice = gui.getNextChoice() # one could alternatively call the getNextChoiceIndex too
        if inChoice == choices[0]: #"Transform & register beads"
            gui = GenericDialogPlus(inChoice) 
            gui.addDirectoryOrFileField("Bead data folder", prefs.get(None, "datapath_",""))
            gui.addChoice("Image file extension", extenstionchoices, extenstionchoices[0]) #
            gui.addToSameRow()
            #gui.addFileField("Scan folder to check file type", prefs.get(None, "datapath_",""))
            gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0]) #
            gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2) 
            gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2) 
            gui.showDialog()      
            
            if gui.wasOKed(): 
            
                datapath_ = gui.getNextString()
                extension_ = gui.getNextChoice()
                #blank = gui.getNextString()
                filepattern_ = gui.getNextChoice()
                pixel_ = gui.getNextNumber()
                angle_ = gui.getNextNumber()
                # Save in memory using PrefService 
                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "extension_", extension_) 
                prefs.put(None, "filepattern_", filepattern_)
                prefs.put(None, "pixel_", pixel_) 
                prefs.put(None, "angle_", angle_)             
           
                beads=mvrsetup(\
                datapath=datapath_, \
                regpath= r'', \
                filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
                extension=extension_, \ 
                px=pixel_, \ 
                py=pixel_, \ 
                angle=angle_)     
                
                zplanes = beads.GetImageInfo()[2]
                settings = {'extension':extension_,\
                             'BoundingBoxDefinition':None,\
                             'boundingboxmin':'0 0 0',\
                             'boundingboxmax':'1 1 1',\
                             'filepattern':filepattern_,\
                             'pixelsize':str(pixel_),\
                             'prismangle':str(angle_),\
                             'rawzplanes':str(zplanes)}
                             
                settingsfile = os.path.join(datapath_,'dopmsettings.xml') 
                writedopmxml(settingsfile,settings)                
                      
                beads.createXMLdataset()
                beads.getCalibrations()
                beads.ApplyCalibration()
                beads.transformXMLdataset()
                beads.RegisterDataset()
                beads.getAffineTransformations()
                beads.ResaveXMLtoHDF5(datapath_)
                
                BoundingBox=defineboundingbox()
                BB = BoundingBox.OptimalBoundingBox(datapath_)
                BoundingBox.defineBoundingBoxNoInteraction(datapath_)
                BoundingBox.modifyBoundingBox(datapath_,BB)                  
                
        elif inChoice == choices[1]:# Transform & register data"
            gui = GenericDialogPlus(inChoice) 
            gui.addDirectoryOrFileField("Bead data folder", prefs.get(None, "beadpath_",""))
            gui.addDirectoryOrFileField("Data folder", prefs.get(None, "datapath_",""))
            gui.addChoice("Image file extension", extenstionchoices, extenstionchoices[0]) #
            gui.addToSameRow()
            #gui.addFileField("Scan folder to check file type", prefs.get(None, "datapath_",""))
            gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0]) #
            gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2) 
            gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2) 
            gui.showDialog()      
            if gui.wasOKed(): 
                beadpath_ = gui.getNextString()
                datapath_ = gui.getNextString()
                extension_ = gui.getNextChoice()
                #blank = gui.getNextString()
                filepattern_ = gui.getNextChoice()
                pixel_ = gui.getNextNumber()
                angle_ = gui.getNextNumber()
                # Save in memory using PrefService 
                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "beadpath_", beadpath_)
                prefs.put(None, "extension_", extension_) 
                prefs.put(None, "filepattern_", filepattern_)
                prefs.put(None, "pixel_", pixel_) 
                prefs.put(None, "angle_", angle_) 
           
                sample=mvrsetup(\
                datapath=datapath_, \
                regpath= beadpath_, \
                filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
                extension=extension_, \ 
                px=pixel_, \ 
                py=pixel_, \ 
                angle=angle_)      

                sample.createXMLdataset()
                sample.getCalibrations()
                sample.ApplyCalibration()
                
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
              
                sample.ApplyBeadRegCSV()
                
                                          
        elif inChoice == choices[2]:#"Transform two-view data without registering"
            gui = GenericDialogPlus(inChoice) 
            gui.addDirectoryOrFileField("Data folder", prefs.get(None, "datapath_",""))
            gui.addChoice("Image file extension", extenstionchoices, extenstionchoices[0]) #
            gui.addToSameRow()
            #gui.addFileField("Scan folder to check file type", prefs.get(None, "datapath_",""))
            gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0]) #
            gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2) 
            gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2) 
            gui.showDialog()      
            if gui.wasOKed(): 
                datapath_ = gui.getNextString()
                extension_ = gui.getNextChoice()
                #blank = gui.getNextString()
                filepattern_ = gui.getNextChoice()
                pixel_ = gui.getNextNumber()
                angle_ = gui.getNextNumber()
                # Save in memory using PrefService 
                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "extension_", extension_) 
                prefs.put(None, "filepattern_", filepattern_)
                prefs.put(None, "pixel_", pixel_) 
                prefs.put(None, "angle_", angle_) 
           
                sample=mvrsetup(\
                datapath=datapath_, \
                regpath= r'', \
                filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
                extension=extension_, \ 
                px=pixel_, \ 
                py=pixel_, \ 
                angle=angle_)        
                      
                sample.createXMLdataset()
                sample.getCalibrations()
                sample.ApplyCalibration()
                sample.transformXMLdataset()
            
        elif inChoice == choices[3]:#"Transform one-view data"
            print 'not implemented yet'

    
if __name__ in ['__builtin__','__main__']:
    
    main()
    IJ.log("Finished")