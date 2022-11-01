#@ PrefService prefs 
from fiji.util.gui import GenericDialogPlus 
import os
from ij import IJ
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.formats import MetadataTools
from loci.formats import ImageReader
from array import array
from ij.io import FileSaver
import math
import csv
from  os.path import isfile
import shutil
from ij.plugin import FolderOpener
from ij.plugin import HyperStackConverter
from xml.etree import ElementTree as ET
from ome.units import UNITS


class MVF:
    
    BB = 'All Views' 
    
    def __init__(self, **kwargs):
        valid_keys = ["datapath","savepath","binning"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))
        self.dataset = 'dataset.xml'
        info = self.getXMLinfo()
        self.xml_tiles = info[0]
        self.xml_times = info[1] 
        self.xml_angles = info[2]        
        
    def createFolder(self,fusedpath):
        #print self.directory
        try:
            if not os.path.exists(fusedpath):
                os.makedirs(fusedpath)
        except OSError:
            print ('Error: Creating directory. ' +  self.savepath)
     
    def csvtoarray(self,csv,type_):
        '''
        takes a string with comma delimeters and returns desired format
        '''
        csv = csv.split(',')
        csv_ = []
        for i in csv:
            if type_=='int':
                csv_.append(int(i))
            if type_=='float':
                csv_.append(float(i))
            if type_=='string':
                csv_.append(str(i))
            # print(csv_)
        return csv_   	

    def getXMLinfo(self):
        """
        this function takes a mvf dataset xml config file and just extracts all the registration information
        """
        
        file = os.path.join(self.datapath,self.dataset) 
        root = ET.parse(file).getroot()
        tile_list = []
        times_list = []
        angle_list = []
    
        for node in root.findall('./SequenceDescription/Timepoints'):
             times_list.append(node.find('integerpattern').text)
        times_list = self.csvtoarray(times_list[0],'int')
        times_list.sort()
        print 'times'
        print times_list
         
        for node in root.findall('./SequenceDescription/ViewSetups/ViewSetup/attributes'):
            elem = node.find('tile').text
            tile_list.append(elem)

        for node in root.findall('./SequenceDescription/ViewSetups/Attributes/Angle/name'):
            print node.text
            angle_list.append(node.text)
        print 'angles'   
        print angle_list     
              
        for i in range(len(tile_list)):
            tile_list[i]=int(tile_list[i])   
        tile_list = list(set(tile_list))  
        print 'tiles'
        print tile_list
        
        return [tile_list,times_list,angle_list]     
    
    def getFusedVolumes(self):
        """
        this function takes a mvf dataset and extracts fused volumes
        """
        binning = self.binning
        
        datasepath = os.path.join(self.datapath,self.dataset)        
            
        #BB = 'All Views'
        
        fusedfolder = 'fused_binning_'+self.binning
        fusedpath = os.path.join(self.savepath,fusedfolder)
        print fusedpath
        self.createFolder(fusedpath)
        
        tiles = self.xml_tiles
        times = self.xml_times
        
        if len(tiles)==1:
            print 'a'
            IJ.run("Fuse", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tiles[0])+"");
        else:
        
            if len(times)==1:
                for tile in tiles:
                    print 'b'
                    IJ.run("Fuse", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[All Timepoints] processing_tile=[tile "+str(tile)+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tile)+"");  
            else:
                for time in times: 
                    print 'c'
                    for tile in tiles:
                        print 'd'
                        IJ.run("Fuse", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_tile=[tile "+str(tile)+"] processing_timepoint=[Timepoint "+str(time)+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tile)+"");

    def getSingleView(self,view):
        """
        this function takes a mvf dataset and extracts fused volumes
        """
        binning = self.binning
        
        datasepath = os.path.join(self.datapath,self.dataset)        
            
        #BB = 'All Views'
        
        fusedfolder = 'view_'+str(int(view)+1)+'_binning_'+self.binning
        fusedpath = os.path.join(self.savepath,fusedfolder)
        print fusedpath
        self.createFolder(fusedpath)
         
        tiles = self.xml_tiles
        times = self.xml_times
        
        if len(tiles)==1:
            print 'a'
            IJ.run("Fuse", "select=["+datasepath+"] process_angle=[Single angle (Select from List)] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] processing_angle=[angle "+self.xml_angles[int(view)]+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tiles[0])+"");
        else:
        
            if len(times)==1:
                for tile in tiles:
                    print 'b'
                    IJ.run("Fuse", "select=["+datasepath+"] process_angle=[Single angle (Select from List)] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[All Timepoints] processing_angle=[angle "+self.xml_angles[int(view)]+"] processing_tile=[tile "+str(tile)+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tile)+"");  
   
            else:
                for time in times: 
                    print 'c'
                    for tile in tiles:
                        print 'd'
                        IJ.run("Fuse", "select=["+datasepath+"] process_angle=[Single angle (Select from List)] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_angle=[angle "+self.xml_angles[int(view)]+"] processing_tile=[tile "+str(tile)+"] processing_timepoint=[Timepoint "+str(time)+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tile)+"");

    def getSingleViewSubset(self,view,times,tiles):
        """
        this function takes a mvf dataset and extracts fused volumes
        """
        binning = self.binning
        
        datasepath = os.path.join(self.datapath,self.dataset)        
            
        #BB = 'All Views'
        
        fusedfolder = 'subset_view_'+str(int(view)+1)+'_binning_'+self.binning
        fusedpath = os.path.join(self.savepath,fusedfolder)
        print fusedpath
        self.createFolder(fusedpath)
         
        for time in times: 
            for tile in tiles:
                print time
                print tile
                IJ.run("Fuse", "select=["+datasepath+"] process_angle=[Single angle (Select from List)] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_angle=[angle "+self.xml_angles[int(view)]+"] processing_tile=[tile "+str(tile)+"] processing_timepoint=[Timepoint "+str(time)+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tile)+"");
                        
    def getFusedVolumesSubset(self,times,tiles):

        """
        this function takes a mvf dataset and extracts fused volumes
        """
        binning = self.binning
        
        datasepath = os.path.join(self.datapath,self.dataset)        
            
        #BB = 'All Views'
        
        fusedfolder = 'subset_fused_binning_'+self.binning
        fusedpath = os.path.join(self.savepath,fusedfolder)
        print fusedpath
        self.createFolder(fusedpath)
         
        for time in times: 
            for tile in tiles:
                print time
                print tile
                IJ.run("Fuse", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_tile=[tile "+str(tile)+"] processing_timepoint=[Timepoint "+str(time)+"] bounding_box=["+self.BB+"] downsampling="+self.binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory=["+fusedpath+"] filename_addition=tile_"+str(tile)+""); 
                
    def ResaveXMLtoHDF5(self):
        '''
        converts the dataset to h5 for faster viewing of data in multiview fusion plugin
        '''
        datapath = os.path.join(self.datapath,self.dataset)
        IJ.run("As HDF5", "select=["+datapath+"] resave_angle=[All angles] resave_channel=[All channels] resave_illumination=[All illuminations] resave_tile=[All tiles] resave_timepoint=[All Timepoints] subsampling_factors=[{ {1,1,1}, {2,2,1} }] hdf5_chunk_sizes=[{ {32,16,8}, {16,16,16} }] timepoints_per_partition=1 setups_per_partition=0 use_deflate_compression export_path=["+datapath+"]") 

    def CheckTimesTilesSubsets(self,tiles_chosen,times_chosen):
       
        tiles = self.xml_tiles 
        times = self.xml_times    
             
        if "-" in tiles_chosen:
            tiles_chosen = tiles_chosen.split('-')
            tiles_chosen = range(int(tiles_chosen[0]),int(tiles_chosen[1])+1,1)
            if set(tiles_chosen)<=set(tiles):
                tiles_chosen = list(set(tiles_chosen))
            else:
                print 'no valid tiles chosen aborting'  
                return
        elif "," in tiles_chosen:
            tiles_chosen = tiles_chosen.split(',')
            tiles_chosen = [int(x) for x in tiles_chosen] 
            if set(tiles_chosen)<=set(tiles):
                tiles_chosen = list(set(tiles_chosen))
                print tiles_chosen
            else:
                print 'no valid tiles chosen aborting'  
                return  
        elif tiles_chosen:
            if not isinstance(tiles_chosen,list):
                tiles_chosen = [int(tiles_chosen)]
            if set(tiles_chosen)<=set(tiles):
                tiles_chosen = list(set(tiles_chosen))
                print tiles_chosen
            else:
                print 'no valid tiles chosen aborting'  
                return 
        else:
            print 'no valid tiles chosen aborting' 
            return
            
        if "-" in times_chosen:
            times_chosen = times_chosen.split('-')
            times_chosen = range(int(times_chosen[0]),int(times_chosen[1])+1,1)
            if set(times_chosen)<=set(times):
                times_chosen = list(set(times_chosen))
            else:
                print 'no valid times chosen aborting'  
                return
        elif "," in times_chosen:
            times_chosen = times_chosen.split(',')
            times_chosen = [int(x) for x in times_chosen] 
            if set(times_chosen)<=set(times):
                times_chosen = list(set(times_chosen))
                print times_chosen
            else:
                print 'no valid times chosen aborting'  
                return  
        elif times_chosen:
            if not isinstance(times_chosen,list):
                times_chosen = [int(times_chosen)]
            if set(times_chosen)<=set(times):
                times_chosen = list(set(times_chosen))
                print times_chosen
            else:
                print 'no valid times chosen aborting'  
                return 
        else:
            print 'no valid times chosen aborting' 
            return
        print 'times and tiles valid starting processing.....'
        return [True, sorted(times_chosen),sorted(tiles_chosen)]
        
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
        
        MVF.BB = BB
           
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
           
                data=MVF(\
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
                
                data=MVF(\
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
                
                data=MVF(\
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
