# dOPM_Shared_ImageJ_Scripts
Sharing dOPM data processing scripts based in ImageJ and relying mainly on Multiview Reconstruction plugin https://imagej.net/plugins/multiview-reconstruction

## Instructions
 - Put these scripts in fiji subfolder -> path-to-fiji\Fiji.app\plugins\Scripts\dOPM
 - Stop using this version of Fiji (all others maybe not compatible) -> ~~https://imperialcollegelondon.box.com/s/555qs9ufjrrh8b43ocry4gp4x0yhh36a~~
 
## updates
 - Start using this version (all others maybe not compatible) -> https://imperialcollegelondon.app.box.com/s/2pc9iiusvuh36uc8arceoutrwxi193ul/file/1364388978888
     - as compatible with ClIJ - https://imagej.net/plugins/clij
     - good for doing fast image processing, use it for MIPS to summarise data - see dOPM plugin menu - MIPs
 - added testing method for geometric prediction of bounding box in z direction based on dOPM remote scanning parallelepiped volumes, can cut data footprint down by 20% or more - useful at TB scale
     - STILL TESTING, not user friendly, does not work headless, - using the 'define bounding box for dataset' dOPM menu item
         - to use you first need to define bounding box - see dOPM menu, run this on bead data after you have setup the bead dataset
         - use 'geometric prediction'
         - it extracts a fused bead image gets real world coordinates, gets dimensions of full resolution fused volume, applies predicted bounding box to bead dataset and calls it 'My Bounding Box'
         - then setup sample data dataset and apply bounding box to it using the 'define bounding box for dataset' dOPM menu item
         - above is a bit confusion because all options are available on one GUI prompt, i.e. you cannot apply a bounding box from the bead dataset until it has been created, 
 - as above works with CLIJ - see get MIPS menu option, gives quick summary of data as MIPS, I used this a lot 
  
  




