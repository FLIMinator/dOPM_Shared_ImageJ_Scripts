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


class dOPMMVF:

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
           
                beads=dOPMMVF(\
                datapath=datapath_, \
                regpath= r'', \
                filepattern=filepattern_, \ #'spim_Time000{t}_Tile000{x}_channel{c}_angle{a}'
                extension=extension_, \ 
                px=pixel_, \ 
                py=pixel_, \ 
                angle=angle_)     
                      
                beads.createXMLdataset()
                beads.getCalibrations()
                beads.ApplyCalibration()
                beads.transformXMLdataset()
                beads.RegisterDataset()
                beads.getAffineTransformations()
                beads.ResaveXMLtoHDF5(datapath_)
                                                                    
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
           
                sample=dOPMMVF(\
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
                beads=dOPMMVF(\
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
           
                sample=dOPMMVF(\
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