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

import xml.etree.ElementTree as ET
from xml.dom import minidom
from ij import IJ


def readdopmxml(filename):

<<<<<<< HEAD:dopmmvr.py
    tree = ET.parse(filename)
    root = tree.getroot()
    #ET.dump(root)    
    #parameters = root.find('parameters') 
   
    settings = {}
    for elem in tree.iter():
        if elem.text:
            settings.update({elem.tag: elem.text})
=======
    def __init__(self, **kwargs):
        valid_keys = ["datapath","regpath","filepattern","extension","px","py","angle"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))
        self.filepattern_ = self.filepattern
        self.filepattern = self.filepattern+self.extension
        #self.datapath = os.path.abspath(self.datapath)
        #self.regpath = os.path.abspath(self.regpath)
        self.dims = self.GetImageInfo()
        self.dataset = 'dataset.xml'
        self.registration_csv = 'registrations.csv'
        self.calibration_csv = 'calibrations.csv'
        self.calibfile = os.path.normpath(os.path.join(self.datapath,self.calibration_csv))
        self.regfile = os.path.normpath(os.path.join(self.regpath,self.registration_csv))
        
    def GetImageInfo(self):    
            
        if self.filepattern_ == "spim_Time{tttt}_Tile{xxxx}_channel{c}_angle{a}":    
            csplit=3
            tsplit=1
            tilesplit=2
        elif self.filepattern_ == "spim_Time{tttt}_Tile{xxxx}_angle{a}":    
            csplit=-1
            tsplit=1
            tilesplit=2
        else:
            print 'unexpected file pattern'      
            
        results = []
        channels = []
        times = []
        tiles= []
        hyperstack = -1
        
        results += [each for each in os.listdir(self.datapath) if each.endswith(self.extension)]
        times += [ str(int(each.split('_')[tsplit].split('e')[1])) for each in os.listdir(self.datapath) if each.endswith(self.extension)]
        tiles += [ str(int(each.split('_')[tilesplit].split('e')[1])) for each in os.listdir(self.datapath) if each.endswith(self.extension)]

        
        T = set(times)
        T= ','.join(T)

        Tiles = set(tiles)
        Tiles= ','.join(Tiles)
        
        if len(results):
        
            file = os.path.join(self.datapath,results[0])
                
            tiff_names=['.tif','.tiff']

            if any(self.extension==i for i in tiff_names):
                imps = BF.openImagePlus(file)
                imp = imps[0]
                szX = imp.getCalibration().pixelWidth
                szY = imp.getCalibration().pixelHeight
                szZ = imp.getCalibration().pixelDepth
                X=imp.getWidth()
                Y=imp.getHeight()
                Z=imp.getImageStackSize()
                imp.close()
    #            print xVox
    #            print yVox
    #            print zVox
                hyperstack = 0
                print 'processing tif zstacks'
                channels += [ each.split('_')[csplit].split('l')[1] for each in os.listdir(self.datapath) if each.endswith(self.extension)]
                C = set(channels)
                C= ','.join(C)          
                
            elif self.extension=='.nd2':
                # read in and display ImagePlus object(s)
                reader = ImageReader()
                omeMeta = MetadataTools.createOMEXMLMetadata()
                reader.setMetadataStore(omeMeta)
                reader.setId(file)
                #seriesCount = reader.getSeriesCount()
                X=reader.getSizeX()
                Y=reader.getSizeY()
                Z=reader.getSizeZ()
        
                #T=reader.getSizeT() # we dont use this
                # physical calibration - assumes microns
                szX = omeMeta.getPixelsPhysicalSizeX(0).value() # not correct dont use
                szY = omeMeta.getPixelsPhysicalSizeY(0).value() # not correct dont use
                szZ = omeMeta.getPixelsPhysicalSizeZ(0).value() # not correct dont use
                
                if reader.getSizeC()>1 and self.filepattern.find('channel')==-1:
                    print 'processing nd2 hyperstacks'
                    hyperstack = 1
                    C=reader.getSizeC() # we don't use this
                    for c in range(C):
                        channels.append(str(c))
                    C=','.join(channels)
                    
                elif reader.getSizeC()==1 and self.filepattern.find('channel')!=-1:
                    hyperstack = 0
                    print 'processing nd2 zstacks'
                    channels += [ each.split('_')[csplit].split('l')[1] for each in os.listdir(self.datapath) if each.endswith(self.extension)]
                    C = set(channels)
                    C= ','.join(C)
                    
                elif reader.getSizeC()==1 and self.filepattern.find('channel')==-1:
                    print 'processing nd2 hyperstacks'
                    hyperstack = 1
                    C=reader.getSizeC() # we don't use this
                    for c in range(C):
                        channels.append(str(c))
                    C=','.join(channels)
                    
                reader.close()
                
            else:
                print 'error in image format - does not match expected types'   
            
            print [X,Y,Z,T,C,szX,szY,szZ]
            return [X,Y,Z,T,C,szX,szY,szZ,Tiles,hyperstack]
        else:
            print 'error in image format - does not match expected types'  
            return []
        
    def createXMLdataset(self):
        '''
        takes dOPM z-stack parameters and acquisition parameters to create dataset - this can also be done using multiview fusion plugin application in imagej
        uses imagej module IJ to run macro commands applicable to the multiview fusion plugin in imagej and programmatically add in strings for variables that need defining for each setup
        '''
        times = self.dims[3]
        tiles = self.dims[8]
        channels = self.dims[4]
        pz = self.dims[7]
        angles = "0-"+IJ.d2s(4*self.angle,0)+":"+IJ.d2s(4*self.angle,0)
       
        #print pz,py,px
        px = IJ.d2s(self.px,4)
        py = IJ.d2s(self.py,4)
        pz = IJ.d2s(pz,4)
        
        tiff_names=['tif','tiff']
        ext = 'tif'
        
        if any(self.extension==i for i in tiff_names):
            IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (TIFF only, ImageJ Opener)] project_filename=["+self.dataset+"] multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory=["+self.datapath+"] image_file_pattern="+self.filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        elif self.dims[9]==1:
            #print 'dataset from multiple channel per file nd2'
            IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename=["+self.dataset+"] multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (all channels in one file)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory=["+self.datapath+"] image_file_pattern="+self.filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")    
        elif self.dims[9]==0:
            #print 'dataset from one channel per file nd2'
            IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename=["+self.dataset+"] multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory=["+self.datapath+"] image_file_pattern="+self.filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        else:
            print 'wrong image formate during createXMLdataset'
        
    def createFolder(self,newpath):
        #print self.directory
        try:
            if not os.path.exists(newpath):
                os.makedirs(newpath)
        except OSError:
            print ('Error: Creating directory. ' +  newpath)
>>>>>>> parent of c7b79d3 (filters out non 'spim' prefix  '.nd2' files):make_multiview_reconstruction_dataset.py
    
    filterstrings = ['extension','boundingboxmin','boundingboxmax','filepattern','pixelsize','prismangle','rawzplanes']
    
    settings = {k:v for k,v in settings.iteritems() if k in filterstrings}
    
    IJ.log('settings read:')
    IJ.log(str(settings)) 
    
    return settings

def writedopmxml(filename,settings):
    """
   settings = {'extension':'.nd2',\
                'BoundingBoxDefinition':'My Bounding Box',\
                'boundingboxmin':'0 0 0',\
                'boundingboxmax':'1 1 1',\
                'filepattern':'spim_Time{tttt}_Tile{xxxx}_angle{a}',\
                'pixelsize':'0.35',\
                'prismangle':'17.5'
                'rawzplanes':'100'}
    """
    
    data = ET.Element('dOPMconfig')
    items = ET.SubElement(data, 'parameters')
    pixel = ET.SubElement(items, 'pixelsize').text = settings.get("pixelsize")
    pixel = ET.SubElement(items, 'rawzplanes').text = settings.get("rawzplanes")
    prismangle = ET.SubElement(items, 'prismangle').text = settings.get("prismangle")
    extension = ET.SubElement(items, 'extension') .text = settings.get("extension")
    filepattern = ET.SubElement(items, 'filepattern').text = settings.get("filepattern")
    boundingbox = ET.SubElement(items, 'BoundingBoxes')
    
    if settings.get("BoundingBoxDefinition") is not None:
        BoundingBoxDefinition = ET.SubElement(boundingbox, 'BoundingBoxDefinition')
        boundingboxmin = ET.SubElement(BoundingBoxDefinition, 'boundingboxmin').text = settings.get("boundingboxmin")
        boundingboxmax = ET.SubElement(BoundingBoxDefinition, 'boundingboxmax').text = settings.get("boundingboxmax")
        BoundingBoxDefinition.set('name',"My Bounding Box")

    xmlstr = minidom.parseString(ET.tostring(data)).toprettyxml(indent="   ",encoding='UTF-8')
    #print xmlstr
    with open(filename, "w") as f:
        f.write(xmlstr)    
        
    IJ.log('settings written:')
    IJ.log(str(settings))    
    
class mvrsetup:

    def __init__(self, **kwargs):
        valid_keys = ["datapath","regpath","filepattern","extension","px","py","angle"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))
        self.filepattern_ = self.filepattern
        self.filepattern = self.filepattern+self.extension
        #self.datapath = os.path.abspath(self.datapath)
        #self.regpath = os.path.abspath(self.regpath)
        self.dims = self.GetImageInfo()
        self.dataset = 'dataset.xml'
        self.registration_csv = 'registrations.csv'
        self.calibration_csv = 'calibrations.csv'
        self.calibfile = os.path.normpath(os.path.join(self.datapath,self.calibration_csv))
        self.regfile = os.path.normpath(os.path.join(self.regpath,self.registration_csv))
        
    def GetImageInfo(self):    
            
        if self.filepattern_ == "spim_Time{tttt}_Tile{xxxx}_channel{c}_angle{a}":    
            csplit=3
            tsplit=1
            tilesplit=2
        elif self.filepattern_ == "spim_Time{tttt}_Tile{xxxx}_angle{a}":    
            csplit=-1
            tsplit=1
            tilesplit=2
        else:
            print 'unexpected file pattern'      
            
        results = []
        channels = []
        times = []
        tiles= []
        hyperstack = -1
        
        results += [each for each in os.listdir(self.datapath) if each.endswith(self.extension) and each.startswith('spim')]
        times += [ str(int(each.split('_')[tsplit].split('e')[1])) for each in os.listdir(self.datapath) if each.endswith(self.extension) and each.startswith('spim')]
        tiles += [ str(int(each.split('_')[tilesplit].split('e')[1])) for each in os.listdir(self.datapath) if each.endswith(self.extension) and each.startswith('spim')]

        
        T = set(times)
        T= ','.join(T)

        Tiles = set(tiles)
        Tiles= ','.join(Tiles)
        
        print results
        
        if len(results):
        
            file = os.path.join(self.datapath,results[0])
            
            print file 
            tiff_names=['.tif','.tiff']

            if any(self.extension==i for i in tiff_names):
                #file.replace(r"\\",r"/") ffs 2311273
                file.replace('\\','/')
                #imps = BF.openImagePlus(file) ffs 2311273, bioformats not working....
                imp = IJ.openImage(file)
                #imp = imps[0]
                szX = imp.getCalibration().pixelWidth # not correct dont use
                szY = imp.getCalibration().pixelHeight # not correct dont use
                szZ = imp.getCalibration().pixelDepth
                X=imp.getWidth()
                Y=imp.getHeight()
                Z=imp.getImageStackSize()
                imp.close()
    #            print xVox
    #            print yVox
    #            print zVox
                hyperstack = 0
                print 'processing tif zstacks'
                channels += [ each.split('_')[csplit].split('l')[1] for each in os.listdir(self.datapath) if each.endswith(self.extension)]
                C = set(channels)
                C= ','.join(C)          
                
            elif self.extension=='.nd2':
                # read in and display ImagePlus object(s)
                reader = ImageReader()
                omeMeta = MetadataTools.createOMEXMLMetadata()
                reader.setMetadataStore(omeMeta)
                reader.setId(file)
                #seriesCount = reader.getSeriesCount()
                X=reader.getSizeX()
                Y=reader.getSizeY()
                Z=reader.getSizeZ()
        
                #T=reader.getSizeT() # we dont use this
                # physical calibration - assumes microns
                szX = omeMeta.getPixelsPhysicalSizeX(0).value() # not correct dont use
                szY = omeMeta.getPixelsPhysicalSizeY(0).value() # not correct dont use
                szZ = omeMeta.getPixelsPhysicalSizeZ(0).value() # not correct dont use
                
                if reader.getSizeC()>1 and self.filepattern.find('channel')==-1:
                    print 'processing nd2 hyperstacks'
                    hyperstack = 1
                    C=reader.getSizeC() # we don't use this
                    for c in range(C):
                        channels.append(str(c))
                    C=','.join(channels)
                    
                elif reader.getSizeC()==1 and self.filepattern.find('channel')!=-1:
                    hyperstack = 0
                    print 'processing nd2 zstacks'
                    channels += [ each.split('_')[csplit].split('l')[1] for each in os.listdir(self.datapath) if each.endswith(self.extension)]
                    C = set(channels)
                    C= ','.join(C)
                    
                elif reader.getSizeC()==1 and self.filepattern.find('channel')==-1:
                    print 'processing nd2 hyperstacks'
                    hyperstack = 1
                    C=reader.getSizeC() # we don't use this
                    for c in range(C):
                        channels.append(str(c))
                    C=','.join(channels)
                    
                reader.close()
                
            else:
                print 'error in image format - does not match expected types'   
            
            print [X,Y,Z,T,C,szX,szY,szZ]
            return [X,Y,Z,T,C,szX,szY,szZ,Tiles,hyperstack]
        else:
            print 'error in image format - does not match expected types'  
            return []
        
    def createXMLdataset(self):
        '''
        takes dOPM z-stack parameters and acquisition parameters to create dataset - this can also be done using multiview fusion plugin application in imagej
        uses imagej module IJ to run macro commands applicable to the multiview fusion plugin in imagej and programmatically add in strings for variables that need defining for each setup
        '''
        times = self.dims[3]
        tiles = self.dims[8]
        channels = self.dims[4]
        pz = self.dims[7]
        angles = "0-"+IJ.d2s(4*self.angle,0)+":"+IJ.d2s(4*self.angle,0)
       
        #print pz,py,px
        px = IJ.d2s(self.px,4)
        py = IJ.d2s(self.py,4)
        pz = IJ.d2s(pz,4)
        
        tiff_names=['tif','tiff']
        ext = 'tif'
        
        if any(self.extension==i for i in tiff_names):
            IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (TIFF only, ImageJ Opener)] project_filename=["+self.dataset+"] multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory=["+self.datapath+"] image_file_pattern="+self.filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        elif self.dims[9]==1:
            #print 'dataset from multiple channel per file nd2'
            IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename=["+self.dataset+"] multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (all channels in one file)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory=["+self.datapath+"] image_file_pattern="+self.filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")    
        elif self.dims[9]==0:
            #print 'dataset from one channel per file nd2'
            IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename=["+self.dataset+"] multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory=["+self.datapath+"] image_file_pattern="+self.filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        else:
            print 'wrong image formate during createXMLdataset'
        
    def createFolder(self,newpath):
        #print self.directory
        try:
            if not os.path.exists(newpath):
                os.makedirs(newpath)
        except OSError:
            print ('Error: Creating directory. ' +  newpath)
    
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

    def getCalibrations(self):
        """
        this function takes a mvf dataset xml config file and just extracts the voxel calibration registration information
        """
        
        file = os.path.join(self.datapath,self.dataset) 
        
        root = ET.parse(file).getroot()
        affine_list = []
        new_setupid_spacer = 'NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN'
        for node in root.findall('./ViewRegistrations/ViewRegistration'):
            #print node
            #print node[0].find('affine').text
            for i in node:
                #elem  = i.find('affine').text.replace(' ',',')
                elem  = i.find('affine').text
                
            affine_list.append(elem) # only use the last entry which I know to be calibration
                #print elem
            #affine_list = affine_list[:-1] # remove calibration entry as already in registration
            affine_list.append(new_setupid_spacer)
            #print new_setupid_spacer 
            
        savepath = os.path.split(file)[0]
        savepath = os.path.normpath(os.path.join(savepath,self.calibration_csv))
        savepath = savepath.replace('\\','/')
                
        with open(savepath, "wb") as csv_file:
                writer = csv.writer(csv_file)
                for line in affine_list:
                    #print line
                    writer.writerow(line.split())
        csv_file.close()

    def getAffineTransformations(self):
        """
        this function takes a mvf dataset xml config file and just extracts all the registration information
        """
        file = os.path.join(self.datapath,self.dataset) 
        root = ET.parse(file).getroot()
        affine_list = []
        new_setupid_spacer = 'NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN'
        
        for node in root.findall('./ViewRegistrations/ViewRegistration'):
            print node
            #print node[0].find('affine').text
            for i in node:
                #elem  = i.find('affine').text.replace(' ',',')
                elem  = i.find('affine').text
                affine_list.append(elem) # 
                #print elem
            affine_list = affine_list[:-1] # remove calibration entry as already in registration
            affine_list.append(new_setupid_spacer)
            #print new_setupid_spacer 

        savepath = os.path.split(file)[0]
        savepath = os.path.normpath(os.path.join(savepath,self.registration_csv))
        savepath = savepath.replace('\\','/')
             
        with open(savepath, "wb") as csv_file:
                writer = csv.writer(csv_file)
                for line in affine_list:
                    #print line
                    writer.writerow(line.split())
        csv_file.close()

    def transformXMLdataset(self):
        '''
        takes dOPM z-stack parameters and performs affine transformations to deshear, rotate and scale the z-stacks and get them ready for registration in microscope xyz coordinates
        uses imagej module IJ to run macro commands applicable to the multiview fusion plugin in imagej and programmatically add in strings for variables that need defining for each setup
        the macro commands have slightly different text depending on whether the dataset is single channel, single time, multiple channel, multiple time and so on which is a headache - this is why there are mutliple cases below
        '''
        #times = '0'
        #print dims
        times = self.dims[3]
        channels = self.dims[4]
        zplanes = self.dims[2]
        xdim = self.dims[0]
        ydim = self.dims[1]
        pz = self.dims[7]


        pix = IJ.d2s(self.px,4)
        piy = IJ.d2s(self.py,4)
        piz = IJ.d2s(pz,4)

        Angle_ = 2*self.angle
        Angle = IJ.d2s(4*self.angle,0)
        #Angle = "70";
        #Angle_ = 35;
                       
        zdim = math.floor(zplanes*pz/self.px)
        mirror_angle = (math.pi/180)*self.angle
        tan0 = math.tan(mirror_angle)
        ydim_deskewed = math.floor(ydim + zdim*tan0);
        zdim_correct_shift = math.floor(zdim/math.cos(mirror_angle));
        tan0 = IJ.d2s(tan0,6); 
        #datapath = self.datapath+"/"+self.dataset
        datapath = os.path.join(self.datapath,self.dataset)
          
        if  (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))>1):
            print('single time, multiple channel')
            ############################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
            # shear all volumes done 
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            # flip view 2 done#
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            # translated after flip view 2 done
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            # translate all for rotations done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            # rotate view 1 + angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_channels axis_timepoint_"+times+"_all_channels_illumination_0_angle_0=x-axis rotation_timepoint_"+times+"_all_channels_illumination_0_angle_0="+string+"")
            # rotate view 2 - angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_channels axis_timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=x-axis rotation_timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=-"+string+"")
            # translate all back done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")
           
        elif (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))==1):
            print('single time, single channel')    
            ############################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
            # shear all volumes done 
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            # flip view 2 done#
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            # translated after flip view 2 done
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            # translate all for rotations done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            # rotate view 1 + angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] axis_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_0=x-axis rotation_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_0="+string+"")
             # rotate view 2 - angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] axis_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=x-axis rotation_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=-"+string+"")
            # translate all back done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")

        elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))==1):
            print('multiple time, single channel') 
            ############################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
            
            # shear all volumes done 
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            
            # flip view 2 done#
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
           
            # translated after flip view 2 done
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            
            # translate all for rotations done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            
            # rotate view 1 + angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints axis_all_timepoints_channel_"+channels+"_illumination_0_angle_0=x-axis rotation_all_timepoints_channel_"+channels+"_illumination_0_angle_0="+string+"")
            
             # rotate view 2 - angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints axis_all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=x-axis rotation_all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=-"+string+"")

            # translate all back done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")
        
        elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))>1):
            print('multiple time, multiple channel')
            ############################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
            # shear all volumes done 
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
                   
            # flip view 2 done#
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
                
            # translated after flip view 2 done
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
      
            # translate all for rotations done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
             
            # rotate view 1 + angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles axis_all_timepoints_all_channels_illumination_0_angle_0=x-axis rotation_all_timepoints_all_channels_illumination_0_angle_0="+string+"")
            
             # rotate view 2 - angle/2 done
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles axis_all_timepoints_all_channels_illumination_0_angle_"+Angle+"=x-axis rotation_all_timepoints_all_channels_illumination_0_angle_"+Angle+"=-"+string+"")
            
            # translate all back done
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")
        else:
            print('incorrect format')
        
    def ResaveXMLtoHDF5(self,exportpath):
        '''
        converts the dataset to h5 for faster viewing of data in multiview fusion plugin
        '''
        
        datapath = os.path.join(self.datapath,self.dataset)
        exportpath = os.path.join(exportpath,'hdf5')
        self.createFolder(exportpath)
        exportpath = os.path.join(exportpath,self.dataset)
        IJ.run("As HDF5", "select=["+datapath+"] resave_angle=[All angles] resave_channel=[All channels] resave_illumination=[All illuminations] resave_tile=[All tiles] resave_timepoint=[All Timepoints] subsampling_factors=[{ {1,1,1}, {2,2,1} }] hdf5_chunk_sizes=[{ {32,16,8}, {16,16,16} }] timepoints_per_partition=1 setups_per_partition=0 use_deflate_compression export_path=["+exportpath+"]")

    def RegisterDataset(self):
        '''
        uses the multiview fusion plugin macro commands to register dataset - assumes it is a single bead volume with multiple colors (channels) and two views (angles)
        '''

        #signal_strength = "[Very weak & small (beads)]"
        signal_strength = "[Weak & small (beads)]" # this can be changed - see plugin application gui
        #signal_strength = "[Comparable to Sample & small (beads)]"
        #signal_strength = "[Strong & small (beads)]"
        datapath = os.path.join(self.datapath,self.dataset)
        IJ.run("Detect Interest Points for Registration", "select=["+datapath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] type_of_interest_point_detection=Difference-of-Gaussian label_interest_points=beads subpixel_localization=[3-dimensional quadratic fit] interest_point_specification="+signal_strength+" downsample_xy=1x downsample_z=1x compute_on=[CPU (Java)]")
        IJ.run("Register Dataset based on Interest Points", "select=["+datapath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] registration_algorithm=[Fast descriptor-based (rotation invariant)] registration_in_between_views=[Only compare overlapping views (according to current transformations)] interest_points=beads fix_views=[Fix first view] map_back_views=[Do not map back (use this if views are fixed)] transformation=Affine regularize_model model_to_regularize_with=Rigid lamba=0.10 redundancy=0 significance=10 allowed_error_for_ransac=5 number_of_ransac_iterations=Normal")

    def ApplyCalibration(self):
        """ 
        uses csv file
        """
        channels = self.dims[4]
        times = self.dims[3]
        tiles = self.dims[8]
        
        # [X,Y,Z,T,C,szX,szY,szZ,Tiles]
        
        dataset = os.path.join(self.datapath,self.dataset)
       
        registration_list=[]
        Reader = csv.reader(open(self.calibfile), delimiter=' ', quotechar='|')    
        
        for registration in Reader:
            registration_list.append(registration[0])
            
        registration = registration_list[0] # just applies the first row of the registrations 
        
        #print (times.find('-')==-1 and times.find(',')==-1) and (len(csvtoarray(channels,'int'))==1)
        
        if (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))==1):
            # single time, single channels
            print 'a'
            if len(self.csvtoarray(tiles,'int'))==1:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=["+registration+"]");
            else:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_angles same_transformation_for_all_tiles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=["+registration+"]");
            
        elif (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))>1):
            # single time, multiple channels
            print 'b'
            if len(self.csvtoarray(tiles,'int'))==1:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=["+registration+"]");
            else:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles timepoint_"+times+"_all_channels_illumination_0_all_angles=["+registration+"]");
        
        elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))==1):
            # multiple time, single channels
            print 'c'
            if len(self.csvtoarray(tiles,'int'))==1:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=["+registration+"]");
            else:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_channel_"+channels+"_illumination_0_all_angles=["+registration+"]");
        
        elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))>1):
            # multiple time, multiple channels
            print 'd'
            if len(self.csvtoarray(tiles,'int'))==1:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)]  same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles all_timepoints_all_channels_illumination_0_all_angles=["+registration+"]");
            else:
                IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)]  same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=["+registration+"]");

    def ApplyBeadRegCSV(self):
        #(datapath path,angle - double,times str,tiles str,regfile file)
        '''
        uses a csv file to determine affine transoformations to register two views. Is derived from bead datasets using the RegisterDataset(datapath) functions
        going from registered bead dataset to the csv file is a work in progress at the moment. I have a matlab file that can read the xml file to get the affine transformations.
        without a matlab license I now need to write some code in imagej jython to do the same job as the matlab code at reading the xml file to extrat the affine transformations.
        '''
        # [X,Y,Z,T,C,szX,szY,szZ,Tiles]
        times = self.dims[3]
        tiles = self.dims[8]
        channels = self.dims[4]
        
        dataset = os.path.join(self.datapath,self.dataset) 
        angles = [IJ.d2s(0,0),IJ.d2s(4*self.angle,0)]
        Reader = csv.reader(open(self.regfile), delimiter=' ', quotechar='|')    
        idx = 1
        registration_list=[]
        k=0
        
        for registration in Reader: # read row file at a time and add to registration list of rows
            k=k+1
            #print k
            row_ = self.csvtoarray(registration[0],'string')    
            registration_list.append(registration[0])
              
            if row_[0]=='NaN': # if element of row is NaN end of list of transformations, time to assign to angle/channel
                
                channel = IJ.d2s(int(math.floor((idx-1)/2)),0)
                #print 'channel'
                #print channel
                registration_list = registration_list[:-1] # remove NaN row as its not a transformation
                
                if idx%2==0: # if set of transformations is even then view 2
                    view = 2 
                    print 'view 2'
                    angle_str = angles[1]
                else:
                    view = 1
                    print 'view 1'
                    angle_str = angles[0]
                    
                for registration_ in reversed(registration_list):
                    print registration_
                    print angle_str
                    if (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))==1):
                    # single time, single channels
                        print 'single time, single channels'
                        if len(self.csvtoarray(tiles,'int'))==1:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]");
                        else:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_tiles timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]") 
                        
                    elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))==1):
                    # multiple time, single channels
                        print 'multiple time, single channels'
                        if len(self.csvtoarray(tiles,'int'))==1:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")
                        else:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] same_transformation_for_all_tiles transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")
                    
                    elif (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))>1):
                    # single time, multiple channels
                        print 'single time, multiple channels'
                        if len(self.csvtoarray(tiles,'int'))==1:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")
     
                        else:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_tiles timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")
                    
                    elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))>1):
                    # multiple time, multiple channels
                        print 'multiple time, multiple channels'
                        if len(self.csvtoarray(tiles,'int'))==1:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")

                        else:
                            IJ.run("Apply Transformations", "select=["+dataset+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_tiles same_transformation_for_all_timepoints all_timepoints_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")     
                            
                       
                idx +=1 
                registration_list=[] # clear the registration list and start again for the next view/channel etc

class mvrgetvolumes:
    
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
        return [True, sorted(times_chosen),sorted(tiles_chosen)]

class defineboundingbox:

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
       
    def defineBoundingBox(self,datapath):    
                
        datasepath = os.path.join(datapath,self.dataset) 
        IJ.run("Define Bounding Box", "select=["+datasepath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Define using the BigDataViewer interactively] bounding_box_name=[My Bounding Box]");
       
    def defineBoundingBoxNoInteraction(self,datapath):
        datapath = os.path.join(datapath,self.dataset) 
        IJ.run("Define Bounding Box", "select=["+datapath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Maximal Bounding Box spanning all transformed views] bounding_box_name=[My Bounding Box] minimal_x=0 minimal_y=0 minimal_z=0 maximal_x=100 maximal_y=100 maximal_z=100");

    def modifyBoundingBox(self,datapath,BB):
        datapath = os.path.join(datapath,self.dataset) 
        IJ.run("Define Bounding Box", "select=["+datapath+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Modify pre-defined Bounding Box] bounding_box_name=[My Bounding Box] bounding_box_title=[My Bounding Box] minimal_x="+BB[0][0]+" minimal_y="+BB[0][1]+" minimal_z="+BB[0][2]+" maximal_x="+BB[1][0]+" maximal_y="+BB[1][1]+" maximal_z="+BB[1][2]+"");

    def OptimalBoundingBox(self,datapath):
    
        settingsfile = os.path.join(datapath,'dopmsettings.xml')
        settings = readdopmxml(settingsfile)
        zstack_microns = int(settings['rawzplanes'])
        prism_angle = float(settings['prismangle'])
        
        datapath_ = os.path.join(datapath,self.dataset) 
        IJ.run("Fuse", "select="+datapath_+" process_angle=[All angles] process_channel=[Single channel (Select from List)] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_channel=[channel 0] processing_tile=[tile 0] processing_timepoint=[Timepoint 0] bounding_box=[All Views] downsampling=1 pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Display using ImageJ]");
        imp = IJ.getImage()

        offset = [imp.getCalibration().xOrigin/imp.getCalibration().pixelWidth, \
                  imp.getCalibration().yOrigin/imp.getCalibration().pixelHeight, \
                  imp.getCalibration().zOrigin/imp.getCalibration().pixelDepth ]
                   
        print(offset)

        d = round(zstack_microns/imp.getCalibration().pixelDepth)
        d_z = round(d / math.cos(2*prism_angle*math.pi/180))
        #d_y = round(d_z / math.tan(2*prism_angle*math.pi/180))


        bb_x = [0 - math.floor(offset[0]),\
                   imp.getWidth() - math.ceil(offset[0])]   

        #bb_y = [(imp.getHeight()/2 - math.floor(d_y/2)) - math.floor(offset[1]),\
        #          (imp.getHeight()/2 + math.floor(d_y/2)) - math.ceil(offset[1])]   

        bb_y = [- math.floor(offset[1]), imp.getHeight()- math.floor(offset[1])]
                   
        bb_z = [(imp.getImageStackSize()/2 - math.floor(d_z/2)) - math.floor(offset[2]),\
                   (imp.getImageStackSize()/2 + math.floor(d_z/2)) - math.ceil(offset[2])]
                  
        imp.close();

        bb_x = [str(x) for x in bb_x]
        bb_y = [str(x) for x in bb_y]
        bb_z = [str(x) for x in bb_z]

        IJ.log("=========================================================")
        IJ.log("recommended bounding box for diamond for x range is: ")
        IJ.log(' '.join(bb_x))
        IJ.log("recommended bounding box for diamond for y range is: ")
        IJ.log(' '.join(bb_y))
        IJ.log("recommended bounding box for diamond for z range is: ")
        IJ.log(' '.join(bb_z))
        IJ.log("--------------------------------------------------------")

        settings['BoundingBoxDefinition']='My Bounding Box'
        settings['boundingboxmin']=' '.join([bb_x[0],bb_y[0],bb_z[0]])
        settings['boundingboxmax']=' '.join([bb_x[1],bb_y[1],bb_z[1]])

        print settings
        
        settingsfile = os.path.join(datapath,'dopmsettings.xml') 
        writedopmxml(settingsfile,settings)
        
        BB = [[bb_x[0],bb_y[0],bb_z[0]],[bb_x[1],bb_y[1],bb_z[1]]]
        
        return BB
  
class exportalldata:

    def __init__(self, **kwargs):
        valid_keys = ["datapath","dataset"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))
        #self.datapath = os.path.abspath(self.datapath)
        #self.regpath = os.path.abspath(self.regpath)
        self.dataset = 'dataset.xml'
       
    def createFolder(self,datapath):
        #print self.directory
        try:
            if not os.path.exists(datapath):
                os.makedirs(datapath)
        except OSError:
            print ('Error: Creating directory: ' +  datapath)
    
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

         
if __name__ in ['__builtin__','__main__']:
    
    IJ.log("Finished")