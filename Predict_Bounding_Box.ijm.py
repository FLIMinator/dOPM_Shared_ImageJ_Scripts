#@ Float(label = "zstack_microns", value = 100, perist=False) zstack_microns
#@ Float(label = "prism_angle", value = 17.5, perist=False) prism_angle

# zstack_microns = 100.0;
# prism_angle = 17.5

from ij import IJ
import math

# THIS CODE FINDS A BOUNDING BOX FOR THE THEORETICAL DIAMOND OF OVERLAP

# You need to have opened a fused volume without a bounding box 
imp = IJ.getImage()

print(imp.getCalibration())
print(imp.getCalibration().xOrigin)
print(imp.getCalibration().yOrigin)
print(imp.getCalibration().zOrigin)
print(imp.getCalibration().pixelWidth)
print(imp.getCalibration().pixelHeight)
print(imp.getCalibration().pixelDepth)
print(imp.getWidth())
print(imp.getHeight())
print(imp.getImageStackSize())

offset = [round(imp.getCalibration().xOrigin/imp.getCalibration().pixelWidth), \
           round(imp.getCalibration().yOrigin/imp.getCalibration().pixelHeight), \
           round(imp.getCalibration().zOrigin/imp.getCalibration().pixelDepth) ]
           
print(offset)

d = round(zstack_microns/imp.getCalibration().pixelDepth)

print d

d_z = round(d / math.cos(2*prism_angle*math.pi/180))
d_y = round(d_z / math.tan(2*prism_angle*math.pi/180))

print d

bb_di_y = [imp.getHeight()/2 - round(d_y/2) - offset[1],\
           imp.getHeight()/2 + round(d_y/2) - offset[1]]   
                         
bb_di_z = [imp.getImageStackSize()/2 - round(d_z/2) - offset[2],\
           imp.getImageStackSize()/2 + round(d_z/2) - offset[2]]
          
bb_di_y2 = [imp.getHeight()/2 - round(d_y/4) - offset[1],\
           imp.getHeight()/2 + round(d_y/4) - offset[1]]   
                         
bb_di_z2 = [imp.getImageStackSize()/2 - round(d_z/4) - offset[2],\
           imp.getImageStackSize()/2 + round(d_z/4) - offset[2]]
                         
IJ.log("=========================================================")
IJ.log("recommended bounding box for diamond for y range is: ")
IJ.log(str(bb_di_y))
IJ.log("recommended bounding box for diamond for z range is: ")
IJ.log(str(bb_di_z))
IJ.log("--------------------------------------------------------")
IJ.log("recommended bounding box for half-diamond for y range is: ")
IJ.log(str(bb_di_y2))
IJ.log("recommended bounding box for half-diamond for z range is: ")
IJ.log(str(bb_di_z2))
IJ.selectWindow("Log");
IJ.log("Finished")