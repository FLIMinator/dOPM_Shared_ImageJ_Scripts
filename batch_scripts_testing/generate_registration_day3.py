# #@ File(label='Choose a directory for the folder of tiff stacks', style='directory') datapath
# #@ File(label='Choose a registration file (only neeeded for applying bead registration', style='file', value='') regfile
# #@ String(label='File Pattern for the tiff stacks i.e. spim_Tile{x}_TL{t}_Channel{c}_Angle{a}.tif', value='') filepattern
# #@ String(label='Channels, give as 0,1,2 or 0-2', value='') channels
# #@ String(label='times, give as 0,1,2 or 0-2', value='') times
# #@ String(label='tiles - give as 0,1,2 or 0-2 tiles are different volumes in x-y', value='') tiles
# #@ Double(label='px - x dimension of pixel', value='') px
# #@ Double(label='py - y dimension of pixel', value='') py
# #@ Double(label='pz - z dimension of voxel', value='') pz
# #@ Integer(label='zplanes - per z stack', value='') zplanes
# #@ Integer(label='ROI_X - size of image in pixels in x-dimension', value='') X
# #@ Integer(label='ROI_Y - size of image in pixels in x-dimension', value='') Y
# #@ Double (label="What is the dOPM mirrored prisms angle?",value='') angle
# #@ String(label='1 - bead dataset, 2 - general dataset no registration, 3 - general dataset use bead registration, 4 - convert to h5', value='') method
# datapath = datapath.getAbsolutePath()

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

folder = r'D:\Data\ColinOrganoidData\Expt_10\Expt_10_Projects\Training\dual_view_channels_and_time_organoids\20220711_115438_911_beads_before'

datapath = os.path.abspath(folder)
#datapath = datapath.replace('\\','/')

#datasetxml = os.path.normpath(os.path.join(datapath,'dataset.xml')
#datasetxml = datasetxml.replace('\\','/')

calibrationfile = os.path.normpath(os.path.join(datapath,'calibrations.csv'))
calibrationfile = calibrationfile.replace('\\','/')


regfile = os.path.normpath(os.path.join(datapath,'registrations.csv'))
regfile = regfile.replace('\\','/')

filepattern = 'spim_Time000{t}_Tile0000_channel{c}_angle{a}.nd2'
channels = '0,1,2,3,4'
times = '0'
tiles = '0'
px = 0.35
py = 0.35
pz = 1
zplanes = 101
X = 512
Y = 512
angle = 17.5
bounding_box = 'All Views'
bounding_box_limits = '50,106,-43,443,473,241' # comma separated list
binning = '2'
methods = '1' # comma separated list, runs comma separated list of methods see _main_ below
flip = 0

# in princple most of the above parameters can be automatically derived from the folder of tiffs 
# also the script parameter method could be replaced with hardcoded variables at top of script which would be good for record keeping and rerunning stuff

######### IMAGEJ SCRIPT PARAMETERS AUTOMATICALLY PROMPTS USER WITH A GUI FOR ENTERING THE VALUES ######
######### CODE EXPECTS 2 DOPM VIEWS SO WILL NOT WORK PROPERLY IF OTHERWISE ######

'''
A batch opener using os.walk()
This code is part of the Jython tutorial at the ImageJ wiki.
http://imagej.net/Jython_Scripting#A_batch_opener_using_os.walk.28.29
'''

# We do only include the module os,
# as we can use os.path.walk()
# to access functions of the submodule.

######### FUNCTION DEFINITIONS GO AT TOP IN THIS JYTHON CODE ######

def createFolder(directory):
    print directory
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)


def csvtoarray(csv,type_):
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

def getCalibrations(datapath):
    """
    this function takes a mvf dataset xml config file and just extracts the voxel calibration registration information
    """
    
    dataset = 'dataset.xml' # expects this name for xml
    file = os.path.join(datapath,dataset) 
    
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

    registration_csv = 'calibrations.csv'
    savepath = os.path.split(file)[0]
    savepath = os.path.normpath(os.path.join(savepath,registration_csv))
    savepath = savepath.replace('\\','/')
            
    with open(savepath, "wb") as csv_file:
            writer = csv.writer(csv_file)
            for line in affine_list:
                #print line
                writer.writerow(line.split())
    csv_file.close()

def getAffineTransformations(datapath):
    """
    this function takes a mvf dataset xml config file and just extracts all the registration information
    """
    
    dataset = 'dataset.xml' # expects this name for xml
    file = os.path.join(datapath,dataset) 
    
    root = ET.parse(file).getroot()
    affine_list = []
    new_setupid_spacer = 'NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN'
    for node in root.findall('./ViewRegistrations/ViewRegistration'):
        #print node
        #print node[0].find('affine').text
        for i in node:
            #elem  = i.find('affine').text.replace(' ',',')
            elem  = i.find('affine').text
            affine_list.append(elem) # 
            #print elem
        affine_list = affine_list[:-1] # remove calibration entry as already in registration
        affine_list.append(new_setupid_spacer)
        #print new_setupid_spacer 

    registration_csv = 'registrations.csv'
    savepath = os.path.split(file)[0]
    savepath = os.path.normpath(os.path.join(savepath,registration_csv))
    savepath = savepath.replace('\\','/')
         
    with open(savepath, "wb") as csv_file:
            writer = csv.writer(csv_file)
            for line in affine_list:
                #print line
                writer.writerow(line.split())
    csv_file.close()
    
    
def createXMLdataset(px,py,pz,channels,angle,datapath,filepattern,times,tiles):
    '''
    takes dOPM z-stack parameters and acquisition parameters to create dataset - this can also be done using multiview fusion plugin application in imagej
    uses imagej module IJ to run macro commands applicable to the multiview fusion plugin in imagej and programmatically add in strings for variables that need defining for each setup
    '''
    dataset = 'dataset.xml' # expects this name for xml
    angles = "0-"+IJ.d2s(4*angle,0)+":"+IJ.d2s(4*angle,0)
    #print pz,py,px
    px = IJ.d2s(px,4)
    py = IJ.d2s(py,4)
    pz = IJ.d2s(pz,4)
    if tiles=='0':
        #IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (TIFF only, ImageJ Opener)] project_filename="+dataset+" multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[NO (one tile)] image_file_directory="+datapath+" image_file_pattern="+filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename="+dataset+" multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[NO (one tile)] image_file_directory="+datapath+" image_file_pattern="+filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        #IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename="+dataset+" multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[NO (one tile)] image_file_directory="+datapath+" "+filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
    else:
        #IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (TIFF only, ImageJ Opener)] project_filename="+dataset+" multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory="+datapath+" image_file_pattern="+filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
        IJ.run("Define Multi-View Dataset", "define_dataset=[Manual Loader (Bioformats based)] project_filename="+dataset+" multiple_timepoints=[YES (one file per time-point)] multiple_channels=[YES (one file per channel)] _____multiple_illumination_directions=[NO (one illumination direction)] multiple_angles=[YES (one file per angle)] multiple_tiles=[YES (one file per tile)] image_file_directory="+datapath+" image_file_pattern="+filepattern+" timepoints_="+times+" channels_="+channels+" acquisition_angles_="+angles+" tiles_="+tiles+" calibration_type=[Same voxel-size for all views] calibration_definition=[Load voxel-size(s) from file(s) and display for verification] imglib2_data_container=[ArrayImg (faster)] pixel_distance_x="+px+" pixel_distance_y="+py+" pixel_distance_z="+pz+" pixel_unit=microns")
          
def transformXMLdataset(px,py,pz,zplanes,X,Y,angle,datapath,times,channels,flip):
    '''
    takes dOPM z-stack parameters and performs affine transformations to deshear, flip, rotate and scale the z-stacks and get them ready for registration in microscope xyz coordinates
    uses imagej module IJ to run macro commands applicable to the multiview fusion plugin in imagej and programmatically add in strings for variables that need defining for each setup
    the macro commands have slightly different text depending on whether the dataset is single channel, single time, multiple channel, multiple time and so on which is a headache - this is why there are mutliple cases below
    '''
    dataset = 'dataset.xml' # expects this name for xml
    xdim = X
    ydim = Y
    pix = IJ.d2s(px,4)
    piy = IJ.d2s(py,4)
    piz = IJ.d2s(pz,4)

    Angle_ = 2*angle
    Angle = IJ.d2s(4*angle,0)
    #Angle = "70";
    #Angle_ = 35;
                   
    zdim = math.floor(zplanes*pz/px)
    mirror_angle = (math.pi/180)*angle
    tan0 = math.tan(mirror_angle)
    ydim_deskewed = math.floor(ydim + zdim*tan0);
    zdim_correct_shift = math.floor(zdim/math.cos(mirror_angle));
    ydim_flip_shift = ydim;
    tan0 = IJ.d2s(tan0,6); 
    datapath = datapath+"/"+dataset
    
    if len(times)==1 and len(channels)!=1:
        print('single time, multiple channel')
        ############################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
        if flip == 1:
             # flip all volumes done 
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]")
            string = IJ.d2s(ydim_flip_shift,0)
            IJ.run("Apply Transformations", "select="+datapath+" apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[0,"+string+",0]")
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
       
    elif len(times)==1 and len(channels)==1:
        print('single time, single channel')    
        ############################################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
        if flip == 1:
             # flip all volumes done 
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select="+datapath+" apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[0,0,"+string+"]")
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

    elif len(times)!='1' and len(channels)!=1:
        print('multiple time, multiple channel - NOT IMPLEMENTED') 
        """
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
         """    
    elif times!='1' and len(channels)!=1:
        print('multiple time, multiple channel - NOT IMPLEMENTED') 
        """
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
        """
    else:
        print('incorrect format')
    
def ResaveXMLtoHDF5(datapath):
    '''
    converts the dataset to h5 for faster viewing of data in multiview fusion plugin
    '''
    dataset = 'dataset.xml' # expects this name for xml
    dataset = os.path.join(datapath,dataset)
    IJ.run("As HDF5", "select=["+dataset+"] resave_angle=[All angles] resave_channel=[All channels] resave_illumination=[All illuminations] resave_tile=[All tiles] resave_timepoint=[All Timepoints] subsampling_factors=[{ {1,1,1}, {2,2,1} }] hdf5_chunk_sizes=[{ {32,16,8}, {16,16,16} }] timepoints_per_partition=1 setups_per_partition=0 use_deflate_compression export_path=["+dataset+"]")

def RegisterDataset(datapath):
    '''
    uses the multiview fusion plugin macro commands to register dataset - assumes it is a single bead volume with multiple colors (channels) and two views (angles)
    '''
    dataset = 'dataset.xml' # expects this name for xml
    #signal_strength = "[Very weak & small (beads)]"
    signal_strength = "[Weak & small (beads)]" # this can be changed - see plugin application gui
    #signal_strength = "[Comparable to Sample & small (beads)]"
    #signal_strength = "[Strong & small (beads)]"
    dataset = os.path.join(datapath,dataset)
    IJ.run("Detect Interest Points for Registration", "select=["+dataset+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] type_of_interest_point_detection=Difference-of-Gaussian label_interest_points=beads subpixel_localization=[3-dimensional quadratic fit] interest_point_specification="+signal_strength+" downsample_xy=1x downsample_z=1x compute_on=[CPU (Java)]")
    IJ.run("Register Dataset based on Interest Points", "select=["+dataset+"] process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] registration_algorithm=[Fast descriptor-based (rotation invariant)] registration_in_between_views=[Only compare overlapping views (according to current transformations)] interest_points=beads fix_views=[Fix first view] map_back_views=[Do not map back (use this if views are fixed)] transformation=Affine regularize_model model_to_regularize_with=Rigid lamba=0.10 redundancy=0 significance=10 allowed_error_for_ransac=5 number_of_ransac_iterations=Normal")

def ApplyCalibration(datapath,regfile):
    """ 
    uses csv file
    """
    dataset = 'dataset.xml' # expects this name for xml
    dataset = os.path.join(datapath,dataset)
   
    registration_list=[]
    Reader = csv.reader(open(regfile), delimiter=' ', quotechar='|')    
    
    for registration in Reader:
        registration_list.append(registration[0])
        
    registration = registration_list[0] # just applies the first row of the registrations 
   
    IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_0_all_channels_illumination_0_all_angles=["+registration+"]");
    
def ApplyBeadRegCSV(datapath,angle,times,tiles,regfile):
    #(datapath path,angle - double,times str,tiles str,regfile file)
    '''
    uses a csv file to determine affine transoformations to register two views. Is derived from bead datasets using the RegisterDataset(datapath) functions
    going from registered bead dataset to the csv file is a work in progress at the moment. I have a matlab file that can read the xml file to get the affine transformations.
    without a matlab license I now need to write some code in imagej jython to do the same job as the matlab code at reading the xml file to extrat the affine transformations.
    '''
    dataset = 'dataset.xml' # expects this name for xml
    dataset = os.path.join(datapath,dataset) 
    angles = [IJ.d2s(0,0),IJ.d2s(4*angle,0)]
    Reader = csv.reader(open(regfile), delimiter=' ', quotechar='|')    
    idx = 1
    registration_list=[]
    k=0
    for registration in Reader:
        k=k+1
        print k
        row_ = csvtoarray(registration[0],'string')    
        registration_list.append(registration[0])
          
        if row_[0]=='NaN':
            
            registration_list = registration_list[:-1]       
            
            if idx%2==0: 
                view = 2
                print view
                for registration_ in reversed(registration_list):
                    #print 'apply transformation'
                    #print angle[1]  
                    #print channel
                    angle_str = angles[1]
                    channel = IJ.d2s(int(math.floor((idx-1)/2)),0)
                    registration_ = registration_
                    print registration_
                    if tiles=='0':
                        print 'yes'
                        IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]") 
                    else:
                        if len(times)==1:
                            print 'yes'
                            IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_tiles timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")      
                        else:
                            print 'yes'
                            IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_tiles all_timepoints_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")
                        
            else:
                view = 1
                print view
                for registration_ in reversed(registration_list):
                    #print 'apply transformation'
                    #print angle[1]  
                    #print channel
                    angle_str = angles[0]
                    channel = IJ.d2s(int(math.floor((idx-1)/2)),0)
                    registration_ = registration_
                    print registration_
                    if tiles=='0':
                        print 'yes'
                        IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]") 
                    else:
                        if len(times)==1:
                            print 'yes'
                            IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_tiles timepoint_"+times+"_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")      
                        else:
                            print 'yes'
                            IJ.run("Apply Transformations", "select="+dataset+" apply_to_angle=[Single angle (Select from List)] apply_to_channel=[Single channel (Select from List)] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+angle_str+"] processing_channel=[channel "+channel+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_tiles all_timepoints_channel_"+channel+"_illumination_0_angle_"+angle_str+"=["+registration_+"]")
                   
            idx +=1 
            registration_list=[]

def DefineBoundingBox(datapath,BB):
    BB = csvtoarray(bounding_box_limits,'string')
    dataset = 'dataset.xml'
    dataset = os.path.join(datapath,dataset)
    IJ.run("Define Bounding Box", "select="+dataset+" process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=[Maximal Bounding Box spanning all transformed views] bounding_box_name=[My Bounding Box] minimal_x="+BB[0]+" minimal_y="+BB[1]+" minimal_z="+BB[2]+" maximal_x="+BB[3]+" maximal_y="+BB[4]+" maximal_z="+BB[5]+"");


def getFusedVolumes(datapath,binning,tiles,channels,times,bounding_box):
    dataset = 'dataset.xml'
    datasepath = os.path.join(datapath,dataset)
    
    #print fusedpath
    
    if bounding_box == "My Bounding Box":
        BB = "My Bounding Box"
    else:
        BB = 'All Views'
        
    #BB = "My Bounding Box"
     
    if tiles =='0':
        fusedfolder = 'fused_binning_'+binning
        fusedpath = os.path.join(datapath,fusedfolder)
        createFolder(fusedpath)
        IJ.run("Fuse", "select="+datasepath+" process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[All tiles] process_timepoint=[All Timepoints] bounding_box=["+BB+"] downsampling="+binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory="+fusedpath+" filename_addition=tile_"+tiles+"");

    else:
        if times =='0':
            fusedfolder = 'fused_binning_'+binning
            fusedpath = os.path.join(datapath,fusedfolder)
            createFolder(fusedpath)
            splits=tiles.split('-')
            for tile in range(int(splits[0]),int(splits[1])+1):
                IJ.run("Fuse", "select="+datasepath+" process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[All Timepoints] processing_tile=[tile "+str(tile)+"] bounding_box=["+BB+"] downsampling="+binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory="+fusedpath+" filename_addition=tile_"+str(tile)+"");          
                
        else:
            splits=tiles.split('-')
            tsplits=times.split('-')
            fusedfolder = 'fused_binning_'+binning
            fusedpath = os.path.join(datapath,fusedfolder)
            createFolder(fusedpath)
            for time in range(int(tsplits[0]),int(tsplits[1])+1): 
                for tile in range(int(splits[0]),int(splits[1])+1):
                    IJ.run("Fuse", "select="+datasepath+" process_angle=[All angles] process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_tile=[tile "+str(tile)+"] processing_timepoint=[Timepoint "+str(time)+"] bounding_box=["+BB+"] downsampling="+binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory="+fusedpath+" filename_addition=tile_"+str(tile)+"");
                    #IJ.run("Fuse", "select="+datasepath+" process_channel=[All channels] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[All Timepoints] processing_tile=[tile "+str(tile)+"] bounding_box=[All Views] downsampling="+binning+" pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Save as (compressed) TIFF stacks] output_file_directory="+fusedpath+" filename_addition=tile_"+str(tile)+"");
                
if __name__ in ['__builtin__','__main__']:
    # Run the code mofo
    
    methods = csvtoarray(methods,'string')
    
    for method in methods:
    
        if method == '1': # make bead dataset
            createXMLdataset(px,py,pz,channels,angle,datapath,filepattern,times,tiles)
            getCalibrations(datapath)
            ApplyCalibration(datapath,calibrationfile)
            #ResaveXMLtoHDF5(datapath)
            transformXMLdataset(px,py,pz,zplanes,X,Y,angle,datapath,times,channels,flip)
            RegisterDataset(datapath)
            #ResaveXMLtoHDF5(datapath)
            getAffineTransformations(datapath)
            
        if method == '2': # make general dataset with no registration
            createXMLdataset(px,py,pz,channels,angle,datapath,filepattern,times,tiles)
            getCalibrations(datapath)
            ApplyCalibration(datapath,calibrationfile)
            #ResaveXMLtoHDF5(datapath)
            transformXMLdataset(px,py,pz,zplanes,X,Y,angle,datapath,times,channels,flip)
            
            
        if method == '3':  # make general dataset with registration information from beads
            createXMLdataset(px,py,pz,channels,angle,datapath,filepattern,times,tiles)
            ApplyBeadRegCSV(datapath,angle,times,tiles,regfile)

        if method == '4': # make bead dataset
            getAffineTransformations(datapath)       
            
        if method == '5': # resave the dataset as h5
            ResaveXMLtoHDF5(datapath)

        if method == '6': # define bounding box
            DefineBoundingBox(datapath,bounding_box_limits)
            
        if method == '7': # get fused volumes
            getFusedVolumes(datapath,binning,tiles,channels,times,bounding_box)
            
        if method == '8': # test
            createXMLdataset(px,py,pz,channels,angle,datapath,filepattern,times,tiles)
            

     
    '''
    print datapath
    print channels
    print angle
    print tiles
    print filepattern
    print regfile
    '''
