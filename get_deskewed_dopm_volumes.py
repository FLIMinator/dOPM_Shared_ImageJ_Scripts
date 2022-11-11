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

from dopmmvr import mvrgetvolumes
      
def main():
    view_choices = ["0","1"]
    crop_choices = ["no","yes"]
    choices =["fused","single view","single view both"]
    binning_choices = ["1","2","4","8","16"]
    # Create an instance of GenericDialog
    gui = GenericDialogPlus("Extract deskewed dOPM data using multi-view reconstruction plugin as tiff zstacks")
    gui.addChoice("How do you want to extract the tiff stacks", choices, choices[0])
    gui.addChoice("Do you want to apply a bounding box?",crop_choices,crop_choices[0])
    #gui.addHelp(r"https://imagej.net/Generic_dialog") # clicking the help button will open the provided URL in the default browser
    gui.showDialog() # dont forget to actually display the dialog at some point

    if gui.wasOKed():
        inChoice = gui.getNextChoice() # one could alternatively call the getNextChoiceIndex too
        cropChoice = gui.getNextChoice() 
        
        if cropChoice == crop_choices[1]: # global variable used in class instances
            BB = "My Bounding Box"
        else:  
            BB = 'All Views'      
        
        mvrgetvolumes.BB = BB
           
        if inChoice == choices[0]: #"fusion"
            gui = GenericDialogPlus(inChoice) 
            gui.addDirectoryField("Select xml dataset", prefs.get(None, "datapath_",""))
            gui.addDirectoryField("Select save path", prefs.get(None, "savepath_",""))
            gui.addChoice("Choose voxel binning factor", binning_choices, binning_choices[0])
            gui.showDialog()      
            
            if gui.wasOKed(): 
                datapath_ = gui.getNextString()
                savepath_ = gui.getNextString()
                binning_ = gui.getNextChoice()
                # Save in memory using PrefService 
                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "savepath_", savepath_)
                prefs.put(None, "binning_", binning_) 
           
                data=mvrgetvolumes(\
                datapath=datapath_, \
                savepath=savepath_, \
                binning= binning_)   
                
                gui = GenericDialogPlus("Do you want to process a subset?") 
                subset_choices = ["no","yes"]
                gui.addChoice("Do you want to process a subset of times and tiles?" , subset_choices, subset_choices[0])
                gui.showDialog()  
                
                if gui.wasOKed():
                    if gui.getNextChoice() == subset_choices[1]: # do subset
                        gui = GenericDialogPlus("processing a subset") 
                        [tiles,times,angles]=data.getXMLinfo()
                        tiles = [str(x) for x in tiles] 
                        times = [str(x) for x in times] 
                        gui.addChoice("tiles found", tiles, str(tiles[0]))
                        gui.addToSameRow()
                        gui.addStringField("Enter tiles as csv '1,2' or hyphen '1-2':", "")
                        gui.addChoice("times found", times, str(times[0]))
                        gui.addToSameRow()
                        gui.addStringField("Enter times as csv '1,2' or hyphen '1-2':", "")
                        gui.showDialog() 
                        if gui.wasOKed():
                            tiles_chosen = gui.getNextString()
                            times_chosen = gui.getNextString()
                            selection = data.CheckTimesTilesSubsets(tiles_chosen,times_chosen)
                            if selection:
                                print 'fusing subset'                               
                                data.getFusedVolumesSubset(selection[1],selection[2])
                    else:
                        print 'fusing entire dataset'
                        data.getFusedVolumes()
                        
                                                                                                                                  
        elif inChoice == choices[1]:#"single view"
            gui = GenericDialogPlus(inChoice) 
            gui.addDirectoryField("Select xml dataset", prefs.get(None, "datapath_",""))
            gui.addDirectoryField("Select save path", prefs.get(None, "savepath_","")) 
            gui.addChoice("Choose voxel binning factor", binning_choices, binning_choices[0])
            gui.addChoice("Choose view", view_choices, view_choices[0])
            gui.showDialog()      
            if gui.wasOKed(): 
                datapath_ = gui.getNextString()
                savepath_ = gui.getNextString()
                binning_ = gui.getNextChoice()
                view_ = gui.getNextChoice()
                # Save in memory using PrefService 
                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "savepath_", savepath_)
                prefs.put(None, "binning_", binning_) 
                prefs.put(None, "view_", view_) 
                
                data=mvrgetvolumes(\
                datapath=datapath_, \
                savepath=savepath_, \
                binning= binning_)   
                
                gui = GenericDialogPlus("Do you want to process a subset?") 
                subset_choices = ["no","yes"]
                gui.addChoice("Do you want to process a subset of times and tiles?" , subset_choices, subset_choices[0])
                gui.showDialog() 
                
                if gui.wasOKed():
                    if gui.getNextChoice() == subset_choices[1]: # do subset
                        gui = GenericDialogPlus("processing a subset") 
                        [tiles,times,angles]=data.getXMLinfo()
                        tiles = [str(x) for x in tiles] 
                        times = [str(x) for x in times] 
                        gui.addChoice("tiles found", tiles, str(tiles[0]))
                        gui.addToSameRow()
                        gui.addStringField("Enter tiles as csv '1,2' or hyphen '1-2':", "")
                        gui.addChoice("times found", times, str(times[0]))
                        gui.addToSameRow()
                        gui.addStringField("Enter times as csv '1,2' or hyphen '1-2':", "")
                        gui.showDialog() 
                        if gui.wasOKed():
                            tiles_chosen = gui.getNextString()
                            times_chosen = gui.getNextString()
                            selection = data.CheckTimesTilesSubsets(tiles_chosen,times_chosen)
                            if selection:
                                print 'fusing subset'                               
                                data.getSingleViewSubset(view_,selection[1],selection[2])
                    else:
                        print 'fusing entire dataset'
                        data.getSingleView(view_)
                
        elif inChoice == choices[2]:#"both single views"
            gui = GenericDialogPlus(inChoice) 
            gui.addDirectoryField("Select xml dataset", prefs.get(None, "datapath_",""))
            gui.addDirectoryField("Select save path", prefs.get(None, "savepath_","")) 
            gui.addChoice("Choose voxel binning factor", binning_choices, binning_choices[0])
            gui.showDialog()      
            if gui.wasOKed(): 
                datapath_ = gui.getNextString()
                savepath_ = gui.getNextString()
                binning_ = gui.getNextChoice()
                # Save in memory using PrefService 
                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "savepath_", savepath_)
                prefs.put(None, "binning_", binning_) 
                
                data=mvrgetvolumes(\
                datapath=datapath_, \
                savepath=savepath_, \
                binning= binning_)                   
                
                gui = GenericDialogPlus("Do you want to process a subset?") 
                subset_choices = ["no","yes"]
                gui.addChoice("Do you want to process a subset of times and tiles?" , subset_choices, subset_choices[0])
                gui.showDialog()
                
                if gui.wasOKed():
                    if gui.getNextChoice() == subset_choices[1]: # do subset
                        gui = GenericDialogPlus("processing a subset") 
                        [tiles,times,angles]=data.getXMLinfo()
                        tiles = [str(x) for x in tiles] 
                        times = [str(x) for x in times] 
                        gui.addChoice("tiles found", tiles, str(tiles[0]))
                        gui.addToSameRow()
                        gui.addStringField("Enter tiles as csv '1,2' or hyphen '1-2':", "")
                        gui.addChoice("times found", times, str(times[0]))
                        gui.addToSameRow()
                        gui.addStringField("Enter times as csv '1,2' or hyphen '1-2':", "")
                        gui.showDialog() 
                        if gui.wasOKed():
                            tiles_chosen = gui.getNextString()
                            times_chosen = gui.getNextString()
                            selection = data.CheckTimesTilesSubsets(tiles_chosen,times_chosen)
                            if selection:
                                print 'fusing subset'                               
                                data.getSingleViewSubset("0",selection[1],selection[2])
                                data.getSingleViewSubset("1",selection[1],selection[2])
                    else:
                        print 'fusing entire dataset'
                        data.getSingleView("0")                
                        data.getSingleView("1")  
        else :
            print 'not implemented yet'
    

if __name__ in ['__builtin__','__main__']:
     
    main()
    IJ.log("Finished")
