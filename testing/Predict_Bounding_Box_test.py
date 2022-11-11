from ij import IJ
import math
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

datapath = "A:/testing_bettercode/beads/test/"

settingsfile = os.path.join(datapath,'dopmsettings.xml') 
settings = readdopmxml(settingsfile)
zstack_microns = int(settings['rawzplanes'])
prism_angle = float(settings['prismangle'])

# THIS CODE FINDS A BOUNDING BOX FOR THE THEORETICAL DIAMOND OF OVERLAP
# You need to have opened a fused volume without a bounding box 

#open fused bead volume image in memory

IJ.run("Fuse", "select="+datapath+"/"+"dataset.xml"+" process_angle=[All angles] process_channel=[Single channel (Select from List)] process_illumination=[All illuminations] process_tile=[Single tile (Select from List)] process_timepoint=[Single Timepoint (Select from List)] processing_channel=[channel 0] processing_tile=[tile 0] processing_timepoint=[Timepoint 0] bounding_box=[All Views] downsampling=1 pixel_type=[16-bit unsigned integer] interpolation=[Linear Interpolation] image=[Precompute Image] interest_points_for_non_rigid=[-= Disable Non-Rigid =-] blend produce=[Each timepoint & channel] fused_image=[Display using ImageJ]");
imp = IJ.getImage()

offset = [imp.getCalibration().xOrigin/imp.getCalibration().pixelWidth, \
          imp.getCalibration().yOrigin/imp.getCalibration().pixelHeight, \
          imp.getCalibration().zOrigin/imp.getCalibration().pixelDepth ]
           
print(offset)

d = round(zstack_microns/imp.getCalibration().pixelDepth)

print d

d_z = round(d / math.cos(2*prism_angle*math.pi/180))
d_y = round(d_z / math.tan(2*prism_angle*math.pi/180))

print d

bb_x = [0 - math.floor(offset[0]),\
           imp.getWidth() - math.ceil(offset[0])]   

bb_y = [imp.getHeight()/2 - math.floor(d_y/2) - math.floor(offset[1]),\
           imp.getHeight()/2 + math.floor(d_y/2) - math.ceil(offset[1])]   
                         
bb_z = [imp.getImageStackSize()/2 - math.floor(d_z/2) - math.floor(offset[2]),\
           imp.getImageStackSize()/2 + math.floor(d_z/2) - math.ceil(offset[2])]
          
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

BB = [[bb_x[0],bb_y[0],bb_z[0]],[bb_x[1],bb_y[1],bb_z[1]]]
BoundingBox=defineboundingbox(datapath=datapath,beadpath=datapath)
BoundingBox.defineBoundingBoxNoInteraction(datapath)
BoundingBox.modifyBoundingBox(datapath,BB)  


#writedopmxml(settingsfile,settings)

