import os
from ij import IJ
from ij.plugin import FolderOpener
from ij.plugin import HyperStackConverter
from ij.plugin import ZProjector

tiles = 50;

root_path  = r"D:/Data/MaddyParsonLab/230510_first_timelapse_pos_neg/new Projects/Project/dOPM_acquisition_timelapse/20230510_184522_293/processed"

data_sub = "view_1_binning_2"
save_sub = data_sub + "_MIP"
datapath = os.path.join(root_path,data_sub)
datapath = datapath.replace(os.sep,'/')

#for i in range(0,tiles):
for i in range(11,tiles):
    
    # DO STUFF
    print(i)
    save_file = "MAX_tile_"+str(i)+".tif"
    savepath = os.path.join(root_path,save_sub,save_file)
    savepath = savepath.replace(os.sep, '/')
    print(datapath)
    print(savepath)

    imp = FolderOpener.open(datapath, " filter=(tile_"+str(i)+"_fused"+")");
    imp = HyperStackConverter.toHyperStack(imp, 3, 371, 48, "xyzct", "Color");
    imp = ZProjector.run(imp,"max all");
    
    # SAVE STUFF
    IJ.saveAs(imp, "Tiff",savepath);
    IJ.run("Close All", "");





