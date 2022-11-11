#@ File[] (label="Select some files", style="files") listfiles
#@ File[] (label="Select some directories", style="directories") listdirs

print(listfiles)
print(listdirs)

from fiji.util.gui import GenericDialogPlus
 
# Create an instance of GenericDialogPlus
gui = GenericDialogPlus("an enhanced GenericDialog")

# The GenericDialogPlus also allows to select files, folder or both using a browse button
gui.addFileField("Some_file path", "DefaultFilePath")
gui.addDirectoryField("Some_folder path", "DefaultFolderPath")
gui.addDirectoryOrFileField("Some_Path", "DefaultPath")
 
gui.showDialog()