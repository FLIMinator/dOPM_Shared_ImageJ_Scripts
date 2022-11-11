import xml.etree.ElementTree as ET
from xml.dom import minidom
from ij import IJ

# xml.etree.ElementTree.SubElement(parent, tag, attrib={}, **extra)
# create the file structure
filename = "A:/testing_bettercode/filenamepretty.xml"
  
data = ET.Element('dOPMconfig')
items = ET.SubElement(data, 'parameters')
pixel = ET.SubElement(items, 'pixelsize').text ='0.175'
prismangle = ET.SubElement(items, 'prismangle').text ='17.5'
extension = ET.SubElement(items, 'extension') .text ='.nd2'
filepattern = ET.SubElement(items, 'filepattern').text ='spim_Time{tttt}_Tile{xxxx}_angle{a}'
boundingbox = ET.SubElement(items, 'BoundingBoxes')
BoundingBoxDefinition = ET.SubElement(boundingbox, 'BoundingBoxDefinition') #.set('name',"My Bounding Box")
boundingboxmin = ET.SubElement(BoundingBoxDefinition, 'min').text = ' '.join(['0','0','0'])
boundingboxmax = ET.SubElement(BoundingBoxDefinition, 'max').text = ' '.join(['1','1','1'])
BoundingBoxDefinition.set('name',"My Bounding Box")

xmlstr = minidom.parseString(ET.tostring(data)).toprettyxml(indent="   ",encoding='UTF-8')
with open(filename, "w") as f:
    f.write(xmlstr)
    
###### test reading this xml

tree = ET.parse(filename)

root = tree.getroot()
ET.dump(root)