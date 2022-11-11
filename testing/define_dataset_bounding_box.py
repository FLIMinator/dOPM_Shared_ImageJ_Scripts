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
        valid_keys = ["datapath","beadpath"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))
        self.dataset = 'dataset.xml'
    
    def getXMLBoundingBox(self,datapath):
        """
        this function takes a mvf dataset xml config file and just extracts all the registration information
        """
        
        file = os.path.join(datapath,self.dataset) 
        root = ET.parse(file).getroot()
        
        for boundingbox in root.find('./BoundingBoxes'):
            if boundingbox.get('name') == 'My Bounding Box':
                min = boundingbox.find('min').text.split(' ')
                max = boundingbox.find('max').text.split(' ')
                print min
                print max
                #print boundingbox
                return [min,max]
    '''             
    def deleteBoundingBox(self,datapath): # do not use
    
        file = os.path.join(datapath,self.dataset) 
        tree = ET.parse(file)
        root = tree.getroot()
        #print root.BoundingBoxes
        
        
        ##for bb in root.find('./BoundingBoxes/'):
        
        for bb in root.iter('BoundingBoxes'):    
            print bb
            for child in list(bb):
                print child
                bb.remove(child)
        tree.write(file) 
    '''
       
    def defineBoundingBox(self,datapath):    
                
        datasepath = os.path.join(datapath,self.dataset) 
        IJ.run("Define Bounding Box", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Define using the BigDataViewer interactively] bounding_box_name=[My Bounding Box]");
       
    def defineBoundingBoxNoInteraction(self,datapath):
        datasepath = os.path.join(datapath,self.dataset) 
        IJ.run("Define Bounding Box", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Maximal Bounding Box spanning all transformed views] bounding_box_name=[My Bounding Box] minimal_x=0 minimal_y=0 minimal_z=0 maximal_x=100 maximal_y=100 maximal_z=100");

    def modifyBoundingBox(self,datapath,BB):
        datasepath = os.path.join(datapath,self.dataset) 
        IJ.run("Define Bounding Box", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Modify pre-defined Bounding Box] bounding_box_name=[My Bounding Box] bounding_box_title=[My Bounding Box] minimal_x="+BB[0][0]+" minimal_y="+BB[0][1]+" minimal_z="+BB[0][2]+" maximal_x="+BB[1][0]+" maximal_y="+BB[1][1]+" maximal_z="+BB[1][2]+"");
    
def main():
    # Create an instance of GenericDialog
    gui = GenericDialogPlus("Define bounding box for dataset")
    gui.addDirectoryOrFileField("apply bounding box to dataset:", prefs.get(None, "datapath_",""))
    gui.addDirectoryOrFileField("get bounding box from bead dataset:", prefs.get(None, "beadpath_",""))
    methodchoice = ["define box","use existing box"]
    gui.addChoice("Reuse a bounding box definition or make a new one?", methodchoice, methodchoice[0]) #
    gui.showDialog() # dont forget to actually display the dialog at some point

    if gui.wasOKed():
        
        datapath_ = gui.getNextString()
        beadpath_ = gui.getNextString()
        
        prefs.put(None, "datapath_", datapath_)
        prefs.put(None, "beadpath_", beadpath_)
         
        BoundingBox=MVF(datapath=datapath_,beadpath=beadpath_) 
        # BoundingBox.deleteBoundingBox(beadpath_)
        if methodchoice[0] == gui.getNextChoice():
            # define bounding box based on corresponding bead volume
            BoundingBox.defineBoundingBox(beadpath_)
   
        BB = BoundingBox.getXMLBoundingBox(beadpath_)
        
        # apply bead volume defined bounding box to data
        BoundingBox.defineBoundingBoxNoInteraction(datapath_)
        BoundingBox.modifyBoundingBox(datapath_,BB)
        
    
if __name__ in ['__builtin__','__main__']:
     
    main()
    IJ.log("Finished")
    