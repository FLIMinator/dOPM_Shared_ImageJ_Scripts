import xml.etree.ElementTree as ET
from xml.dom import minidom
from ij import IJ


def readdopmxml(filename):

    tree = ET.parse(filename)
    root = tree.getroot()
    #ET.dump(root)    
    #parameters = root.find('parameters') 
   
    settings = {}
    for elem in tree.iter():
        if elem.text:
            settings.update({elem.tag: elem.text})
    
    filterstrings = ['extension','boundingboxmin','boundingboxmax','filepattern','pixelsize','prismangle']
    
    settings = {k:v for k,v in settings.iteritems() if k in filterstrings}
    
    IJ.log('settings read:')
    IJ.log(str(settings)) 
    
    return settings

def writedopmxml(filename,settings):
      
    data = ET.Element('dOPMconfig')
    items = ET.SubElement(data, 'parameters')
    pixel = ET.SubElement(items, 'pixelsize').text = settings.get("pixelsize")
    prismangle = ET.SubElement(items, 'prismangle').text = settings.get("prismangle")
    extension = ET.SubElement(items, 'extension') .text = settings.get("extension")
    filepattern = ET.SubElement(items, 'filepattern').text = settings.get("filepattern")
    boundingbox = ET.SubElement(items, 'BoundingBoxes')
    
    if settings.get("BoundingBoxDefinition") is not None:
        BoundingBoxDefinition = ET.SubElement(boundingbox, 'BoundingBoxDefinition')
        boundingboxmin = ET.SubElement(BoundingBoxDefinition, 'boundingboxmin').text = settings.get("boundingboxmin")
        boundingboxmax = ET.SubElement(BoundingBoxDefinition, 'boundingboxmax').text = settings.get("boundingboxmax")
        BoundingBoxDefinition.set('name',"My Bounding Box")

    xmlstr = minidom.parseString(ET.tostring(data)).toprettyxml(indent="   ",encoding='UTF-8')
    #print xmlstr
    with open(filename, "w") as f:
        f.write(xmlstr)    
        
    IJ.log('settings written:')
    IJ.log(str(settings))    

def main(filename):

    settings = {'extension':'.nd2',\
                'BoundingBoxDefinition':'My Bounding Box',\
                'boundingboxmin':'0 0 0',\
                'boundingboxmax':'1 1 1',\
                'filepattern':'spim_Time{tttt}_Tile{xxxx}_angle{a}',\
                'pixelsize':'0.35',\
                'prismangle':'17.5'}
                
    print 'writing xml'
    writedopmxml(filename,settings)
    print 'reading xml'
    readdomxml(filename)

if __name__ in ['__builtin__','__main__']:
    main("A:/testing_bettercode/filenamepretty.xml")
    IJ.log("Finished")