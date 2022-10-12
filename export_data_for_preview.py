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

    def __init__(self, **kwargs):
        valid_keys = ["datapath","dataset"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))
        #self.datapath = os.path.abspath(self.datapath)
        #self.regpath = os.path.abspath(self.regpath)
        self.dataset = 'dataset.xml'
    
        
    def createFolder(self):
        #print self.directory
        try:
            if not os.path.exists(self.datapath):
                os.makedirs(self.datapath)
        except OSError:
            print ('Error: Creating directory. ' +  self.datapath)
    
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
       
    def ResaveXMLtoHDF5(self,exportpath):
        '''
        converts the dataset to h5 for faster viewing of data in multiview fusion plugin
        '''
        
        datapath = os.path.join(self.datapath,self.dataset)
        exportpath = os.path.join(exportpath,self.dataset)

        IJ.run("As HDF5", "select=["+datapath+"] resave_angle=[All angles] resave_channel=[All channels] resave_illumination=[All illuminations] resave_tile=[All tiles] resave_timepoint=[All Timepoints] subsampling_factors=[{ {1,1,1}, {2,2,1} }] hdf5_chunk_sizes=[{ {32,16,8}, {16,16,16} }] timepoints_per_partition=1 setups_per_partition=0 use_deflate_compression export_path=["+exportpath+"]")

    def ResaveXMLtoTiff(self,exportpath):
        '''
        converts to tiff i.e. instead of .nd2 and seems a bit faster
        '''

        datapath = os.path.join(self.datapath,self.dataset)
        exportpath = os.path.join(exportpath,self.dataset)
         
        IJ.run("As TIFF", "select=["+datapath+"] resave_angle=[All angles] resave_channel=[All channels] resave_illumination=[All illuminations] resave_tile=[All tiles] resave_timepoint=[All Timepoints] export_path=["+exportpath+"]")


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
            data=MVF(datapath=datapath_)               
            data.ResaveXMLtoHDF5(exportpath_)
        elif Choice == Choices[2]:     
            data=MVF(datapath=datapath_)               
            data.ResaveXMLtoTiff(exportpath_)
        else:
            print 'other methods not implemented yet'       
    
if __name__ in ['__builtin__','__main__']:
     
    main()
