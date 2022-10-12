#@ File(label='Choose a directory for the folder of tiff stacks', style='directory') datapath
datapath = datapath.getAbsolutePath()

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
from ij.plugin import ZProjector
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from net.haesleinhuepf.clij2 import CLIJ2;
import os
from os import listdir
from os.path import isfile, join
import glob

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
        
def getStackList(stackdir):
    #print stackdir
    files = glob.glob(stackdir+'/'+"*.tif")
    #print(files) 
    tiff_set=[]
    for a_string in files:
        new_string = a_string.replace(os.sep, '/')
        tiff_set.append(new_string)
    #print(tiff_set)
    return tiff_set

def getPathParts(path):
    path = os.path.normpath(path)
    out=path.split(os.sep)
    drive, path_and_file = os.path.splitdrive(path)
    path, file = os.path.split(path_and_file)
    #print drive, path, file
    return [drive, path, file]

def getMIPsonFolder(datapath):

    MIPfolder = 'MIP'
    pathname = os.path.join(datapath,MIPfolder)
    createFolder(pathname)
    
    stackdir = datapath.replace(os.sep, '/')
    tiff_set = getStackList(stackdir)
    
    for tiff_stack in tiff_set:

        #print tiff_stack
        clij2 = CLIJ2.getInstance();
        imp = IJ.openImage(tiff_stack)
        dims = imp.getDimensions() # x,y,c,z,t
        imageInput = clij2.push(imp);
        #imageOutput = clij2.create([imageInput.getWidth(), imageInput.getHeight()], imageInput.getNativeType());
        imageOutput1 = clij2.create([dims[0], dims[1]], imageInput.getNativeType());
        clij2.maximumZProjection(imageInput, imageOutput1);
        #clij2.show(imageOutput, "output");
        outputZ=clij2.pull(imageOutput1);
        imageOutput2 = clij2.create([dims[3], dims[1]], imageInput.getNativeType());
        clij2.maximumXProjection(imageInput, imageOutput2);
        #clij2.show(imageOutput, "output");
        outputX=clij2.pull(imageOutput2);
        imageOutput3 = clij2.create([dims[0], dims[3]], imageInput.getNativeType());
        clij2.maximumYProjection(imageInput, imageOutput3);
        #clij2.show(imageOutput, "output");
        outputY=clij2.pull(imageOutput3);
        #print filename + 'XY.tif'

        imageOutput4 = clij2.create([dims[0]+dims[3], dims[1]], imageInput.getNativeType());
        clij2.combineHorizontally(imageOutput1,imageOutput2,imageOutput4);
        imageOutput5 = clij2.create([dims[3], dims[1]], imageInput.getNativeType());
        imageOutput6 = clij2.create([dims[0]+dims[3], dims[1]], imageInput.getNativeType());
        clij2.combineHorizontally(imageOutput3,imageOutput5,imageOutput6);       
        imageOutput7 = clij2.create([dims[0]+dims[3], dims[1]+dims[1]], imageInput.getNativeType());        
        clij2.combineVertically(imageOutput4,imageOutput6,imageOutput7);
        
 
        imageOutput7=clij2.pull(imageOutput7);
        
        pathparts = getPathParts(tiff_stack)
        fname = pathparts[2].split('.',1)
        filename = os.path.join(pathname,fname[0])
        
        FileSaver(imageOutput7).saveAsTiff(filename + '.tif')
        
        clij2.clear()
        
        #print filename
                    
if __name__ in ['__builtin__','__main__']:
    # Run the code mofo
    getMIPsonFolder(datapath)

