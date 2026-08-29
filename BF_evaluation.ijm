// You need the following plugins activated (Help --> Update...)
// CSBDeep, StarDist, Bioformats


run("Close All");
close("Results");
roiManager("reset");
run("Set Measurements...", "area redirect=None decimal=2");
Table.create("Organoids_area");
//run("Table...", "name=[Organoids count results] width=400 height=300 menu");

dir  = getDirectory("Select input directory")
filelist = getFileList(dir) 

for (i = 0; i < lengthOf(filelist); i++) {	
    if (endsWith(filelist[i], ".nd2")) { 
		run("Bio-Formats Importer", "open=" + dir + File.separator + filelist[i] + " color_mode=Composite rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT series_1");
    	//open(dir + File.separator + filelist[i]); 
    	sample = File.nameWithoutExtension();
    	savename=dir + File.nameWithoutExtension(); 
        //rename("image");
        
		run("Z Project...", "start=2 projection=[Min Intensity]");
		run("Duplicate...", "title=processed ");
		run("Invert");
		run("Subtract Background...", "rolling=50");
		
		//Manual selection of ROI (in case there is a lot of debris in image background)
		setTool("oval");
		waitForUser("please mark your area of interest");	
		setBackgroundColor(0, 0, 0);
		run("Clear Outside");
		
		//Segmentation using StarDist	
		run("Command From Macro", "command=[de.csbdresden.stardist.StarDist2D], args=['input':'processed', 'modelChoice':'Versatile (fluorescent nuclei)', 'normalizeInput':'true', 'percentileBottom':'1.0', 'percentileTop':'99.8', 'probThresh':'0.6', 'nmsThresh':'0.5', 'outputType':'Both', 'nTiles':'4', 'excludeBoundary':'2', 'roiPosition':'Automatic', 'verbose':'false', 'showCsbdeepProgress':'false', 'showProbAndDist':'false'], process=[false]");
		roiManager("measure");
		Areas = Table.getColumn("Area");
		//Saving
		roiManager("save", savename + ".zip");

		//clean up for next image
		selectWindow("Organoids_area");
		Table.setColumn(sample, Areas);
		Table.update();
		
		close("Results");
		//updateResults();
		roiManager("reset");
		run("Close All");
}}

selectWindow("Organoids_area");
saveAs("Results", dir + "Area.csv");
close("Area.csv");

print("Done. Get yourself some chocolate!");