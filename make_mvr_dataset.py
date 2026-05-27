#@ PrefService prefs
from fiji.util.gui import GenericDialogPlus
from ij import IJ
import os
from os.path import isfile
from sys import path
from java.lang.System import getProperty

code_path = getProperty('fiji.dir') + '/plugins/Scripts/dOPM'

ScriptPath = code_path + "/dopmmvr$py.class"
path.append(code_path)

if isfile(ScriptPath):
    os.remove(ScriptPath)

from dopmmvr import mvrsetup, defineboundingbox


def suffix_to_name(well_suffix):
    if well_suffix is None:
        return "default"
    return str(well_suffix)


def log_detected_groups(label, items):
    pretty = []
    for s in items:
        if s is None:
            pretty.append("no well suffix")
        else:
            pretty.append(str(s))
    IJ.log(label + ": " + ", ".join(pretty))


def make_dataset_basename(well_suffix):
    if well_suffix is None:
        return "dataset"
    return "dataset_" + str(well_suffix)


def split_dataset_path(xmlpath_):
    datapath_ = os.path.dirname(xmlpath_)
    dataset_ = os.path.basename(xmlpath_)

    if dataset_ == '':
        raise ValueError("Please select a dataset XML file, not just a folder.")

    if not dataset_.lower().endswith('.xml'):
        raise ValueError("Selected file is not an XML dataset: " + xmlpath_)

    if not os.path.exists(xmlpath_):
        raise ValueError("Selected dataset XML does not exist: " + xmlpath_)

    return datapath_, dataset_


def build_settings_dict(extension_, filepattern_, pixel_, angle_, zplanes):
    return {
        'extension': extension_,
        'BoundingBoxDefinition': None,
        'boundingboxmin': '0 0 0',
        'boundingboxmax': '1 1 1',
        'filepattern': filepattern_,
        'pixelsize': str(pixel_),
        'prismangle': str(angle_),
        'rawzplanes': str(zplanes)
    }


def get_single_bead_well_info(datapath_, extension_):
    tails = mvrsetup.detect_well_tails(datapath_, extension_)
    if len(tails) == 0:
        raise ValueError("No valid bead files were found in: " + datapath_)

    log_detected_groups("Detected bead well groups", tails)

    if len(tails) > 1:
        raise ValueError(
            "Bead folder contains multiple well groups. "
            "Please provide a bead folder containing only one well or no well suffix. "
            "Found: " + str(tails)
        )

    tail = tails[0]

    if tail is None:
        suffix = None
    else:
        suffix = tail.lstrip('_')

    return suffix, tail


def get_data_well_info_list(datapath_, extension_):
    tails = mvrsetup.detect_well_tails(datapath_, extension_)
    if len(tails) == 0:
        raise ValueError("No valid data files were found in: " + datapath_)

    log_detected_groups("Detected data well groups", tails)

    out = []
    for tail in tails:
        if tail is None:
            suffix = None
        else:
            suffix = tail.lstrip('_')
        out.append((suffix, tail))
    return out


def process_beads(datapath_, extension_, filepattern_, pixel_, angle_):
    bead_well_suffix, bead_well_tail = get_single_bead_well_info(datapath_, extension_)

    beads = mvrsetup(
        datapath=datapath_,
        regpath=r'',
        filepattern=filepattern_,
        extension=extension_,
        px=pixel_,
        py=pixel_,
        angle=angle_,
        well_suffix=bead_well_suffix,
        well_tail=bead_well_tail,
        dataset_basename=make_dataset_basename(bead_well_suffix)
    )

    if not beads.dims:
        raise ValueError("No valid bead files matched the expected pattern in: " + datapath_)

    beads.createXMLdataset()
    beads.ApplyCalibrationFromXML()
    beads.transformXMLdataset()
    beads.RegisterDataset()
    beads.ResaveXMLtoHDF5(datapath_)

    BoundingBox = defineboundingbox(dataset=beads.dataset, rawzplanes=beads.dims[2], prismangle=angle_)
    BB = BoundingBox.OptimalBoundingBox(datapath_)
    BoundingBox.defineBoundingBoxNoInteraction(datapath_)
    BoundingBox.modifyBoundingBox(datapath_, BB)

    IJ.log("Finished bead processing for well group: " + suffix_to_name(bead_well_suffix))


def process_data_with_beads(bead_xml_, datapath_, extension_, filepattern_, pixel_, angle_):
    bead_xml_datapath, bead_xml_dataset = split_dataset_path(bead_xml_)

    IJ.log("Using bead registration XML: " + bead_xml_)

    data_infos = get_data_well_info_list(datapath_, extension_)

    for data_well_suffix, data_well_tail in data_infos:
        IJ.log("Processing data well group: " + suffix_to_name(data_well_suffix))

        sample = mvrsetup(
            datapath=datapath_,
            regpath=bead_xml_datapath,
            filepattern=filepattern_,
            extension=extension_,
            px=pixel_,
            py=pixel_,
            angle=angle_,
            well_suffix=data_well_suffix,
            well_tail=data_well_tail,
            dataset_basename=make_dataset_basename(data_well_suffix),
            registration_source_xml=bead_xml_
        )

        if not sample.dims:
            raise ValueError("No valid data files matched the expected pattern in: " + datapath_)

        sample.createXMLdataset()
        sample.ApplyCalibrationFromXML()
        sample.transformXMLdataset()
        sample.CopyBeadRegistrationXMLGlobal(bead_xml_, source_timepoint="0", source_tile="0")

        IJ.log("Finished data well group: " + suffix_to_name(data_well_suffix))


def process_data_without_beads(datapath_, extension_, filepattern_, pixel_, angle_):
    data_infos = get_data_well_info_list(datapath_, extension_)

    for data_well_suffix, data_well_tail in data_infos:
        IJ.log("Processing data well group: " + suffix_to_name(data_well_suffix))

        sample = mvrsetup(
            datapath=datapath_,
            regpath=r'',
            filepattern=filepattern_,
            extension=extension_,
            px=pixel_,
            py=pixel_,
            angle=angle_,
            well_suffix=data_well_suffix,
            well_tail=data_well_tail,
            dataset_basename=make_dataset_basename(data_well_suffix)
        )

        if not sample.dims:
            raise ValueError("No valid data files matched the expected pattern in: " + datapath_)

        sample.createXMLdataset()
        sample.ApplyCalibrationFromXML()
        sample.transformXMLdataset()

        IJ.log("Finished data well group: " + suffix_to_name(data_well_suffix))


def main():
    choices = [
        "Transform & register beads",
        "Transform & register data",
        "Transform two-view data without registering",
        "Transform one-view data"
    ]

    gui = GenericDialogPlus("dOPM data processing with Multi-view fusion plugin")
    gui.addMessage("Select dOPM data processing option")
    gui.addChoice("Choose one option among a list", choices, choices[0])
    gui.showDialog()

    if gui.wasOKed():
        # Use the single canonical dOPM pattern. Channel handling is inferred:
        # multi-channel ND2 = all channels in one file; TIFF/single-channel ND2 =
        # channel 0 unless a future importer explicitly reintroduces channel files.
        filepatternchoices = [
            "spim_Time{tttt}_Tile{xxxx}_angle{a}"
        ]
        extensionchoices = [".nd2", ".tif", ".tiff"]

        inChoice = gui.getNextChoice()

        if inChoice == choices[0]:
            gui = GenericDialogPlus(inChoice)
            gui.addDirectoryOrFileField("Bead data folder", prefs.get(None, "datapath_", ""))
            gui.addChoice("Image file extension", extensionchoices, extensionchoices[0])
            gui.addToSameRow()
            gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0])
            gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2)
            gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2)
            gui.showDialog()

            if gui.wasOKed():
                datapath_ = gui.getNextString()
                extension_ = gui.getNextChoice()
                filepattern_ = gui.getNextChoice()
                pixel_ = gui.getNextNumber()
                angle_ = gui.getNextNumber()

                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "extension_", extension_)
                prefs.put(None, "filepattern_", filepattern_)
                prefs.put(None, "pixel_", pixel_)
                prefs.put(None, "angle_", angle_)

                process_beads(datapath_, extension_, filepattern_, pixel_, angle_)

        elif inChoice == choices[1]:
            gui = GenericDialogPlus(inChoice)
            gui.addFileField("Optimised bead/reference dataset XML", prefs.get(None, "bead_xml_", ""))
            gui.addDirectoryOrFileField("Data folder", prefs.get(None, "datapath_", ""))
            gui.addChoice("Image file extension", extensionchoices, extensionchoices[0])
            gui.addToSameRow()
            gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0])
            gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2)
            gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2)
            gui.showDialog()

            if gui.wasOKed():
                bead_xml_ = gui.getNextString()
                datapath_ = gui.getNextString()
                extension_ = gui.getNextChoice()
                filepattern_ = gui.getNextChoice()
                pixel_ = gui.getNextNumber()
                angle_ = gui.getNextNumber()

                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "bead_xml_", bead_xml_)
                prefs.put(None, "extension_", extension_)
                prefs.put(None, "filepattern_", filepattern_)
                prefs.put(None, "pixel_", pixel_)
                prefs.put(None, "angle_", angle_)

                process_data_with_beads(
                    bead_xml_,
                    datapath_,
                    extension_,
                    filepattern_,
                    pixel_,
                    angle_
                )

        elif inChoice == choices[2]:
            gui = GenericDialogPlus(inChoice)
            gui.addDirectoryOrFileField("Data folder", prefs.get(None, "datapath_", ""))
            gui.addChoice("Image file extension", extensionchoices, extensionchoices[0])
            gui.addToSameRow()
            gui.addChoice("File pattern", filepatternchoices, filepatternchoices[0])
            gui.addNumericField("pixel size (um)", prefs.getFloat(None, "pixel_", 0), 2)
            gui.addNumericField("prism angle (degrees)", prefs.getFloat(None, "angle_", 0), 2)
            gui.showDialog()

            if gui.wasOKed():
                datapath_ = gui.getNextString()
                extension_ = gui.getNextChoice()
                filepattern_ = gui.getNextChoice()
                pixel_ = gui.getNextNumber()
                angle_ = gui.getNextNumber()

                prefs.put(None, "datapath_", datapath_)
                prefs.put(None, "extension_", extension_)
                prefs.put(None, "filepattern_", filepattern_)
                prefs.put(None, "pixel_", pixel_)
                prefs.put(None, "angle_", angle_)

                process_data_without_beads(
                    datapath_,
                    extension_,
                    filepattern_,
                    pixel_,
                    angle_
                )

        elif inChoice == choices[3]:
            print 'not implemented yet'


if __name__ in ['__builtin__', '__main__']:
    main()
    IJ.log("Finished")