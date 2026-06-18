#@ PrefService prefs
from fiji.util.gui import GenericDialogPlus
from ij import IJ
from java.lang.System import getProperty
from sys import path
import os

code_path = getProperty('fiji.dir') + '/plugins/Scripts/dOPM'
if code_path not in path:
    path.append(code_path)

from dopm_launcher_utils import (
    DEFAULT_FILE_PATTERN,
    MANIFEST_NAME,
    detect_dataset_summary,
    log_summary,
    parse_well_selection,
    format_well_list,
    create_dataset_for_well,
    create_rows_for_selected_wells,
    write_manifest,
    read_manifest,
    split_dataset_path,
    normpath,
    find_dataset_xmls,
)


def create_and_register_bead_dataset(bead_folder, extension, filepattern, pixel, prism_angle, wells_text, manifest_folder):
    summary = detect_dataset_summary(bead_folder, extension)
    log_summary(summary)
    selected_wells = parse_well_selection(wells_text, summary['wells'])
    if len(selected_wells) != 1:
        raise ValueError("Bead registration launcher expects one bead well/no-well group. Selected: " + format_well_list(selected_wells))

    row = create_dataset_for_well(
        bead_folder, extension, filepattern, pixel, prism_angle,
        selected_wells[0], 'two_view', target_angle=None,
        registration_mode='register_beads', bead_xml=None,
        dataset_suffix='beads'
    )

    if manifest_folder is None or str(manifest_folder).strip() == "":
        manifest_folder = bead_folder
    manifest_path = os.path.join(normpath(manifest_folder), MANIFEST_NAME)
    write_manifest(manifest_path, [row])
    IJ.log("Bead XML ready for manual inspection/optimisation: " + row['xml_path'])
    return row


def transfer_predefined_bead_xml_to_manifest(bead_xml, manifest_path):
    bead_xml = normpath(bead_xml)
    split_dataset_path(bead_xml)
    rows = read_manifest(manifest_path)
    for row in rows:
        xmlpath = row.get('xml_path', '')
        if xmlpath == '' or not os.path.exists(xmlpath):
            raise IOError("Manifest row XML not found: " + str(xmlpath))
        datapath, dataset = split_dataset_path(xmlpath)
        from dopmmvr import mvrsetup
        # Use a lightweight helper object without running mvrsetup.__init__,
        # because registration transfer only needs datapath, dataset, and XML helper methods.
        helper = mvrsetup.__new__(mvrsetup)
        helper.datapath = datapath
        helper.dataset = dataset
        IJ.log("Applying predefined bead XML to sample XML: " + xmlpath)
        helper.CopyBeadRegistrationXMLGlobal(bead_xml, source_timepoint="0", source_tile="0")
    IJ.log("Finished applying predefined bead XML to manifest XMLs")


def transfer_predefined_bead_xml_to_folder(bead_xml, xml_folder, xml_name_filter):
    bead_xml = normpath(bead_xml)
    split_dataset_path(bead_xml)
    xmls = find_dataset_xmls(xml_folder, name_filter=xml_name_filter)
    if len(xmls) == 0:
        raise ValueError("No target XMLs found in folder with filter: " + str(xml_name_filter))
    from dopmmvr import mvrsetup
    for xmlpath in xmls:
        datapath, dataset = split_dataset_path(xmlpath)
        helper = mvrsetup.__new__(mvrsetup)
        helper.datapath = datapath
        helper.dataset = dataset
        IJ.log("Applying predefined bead XML to sample XML: " + xmlpath)
        helper.CopyBeadRegistrationXMLGlobal(bead_xml, source_timepoint="0", source_tile="0")


def main():
    mode_choices = [
        "create and auto-register bead XML",
        "apply predefined/manual bead XML to manifest XMLs",
        "apply predefined/manual bead XML to XMLs in folder"
    ]
    extension_choices = [".nd2", ".tif", ".tiff"]

    gui = GenericDialogPlus("dOPM registration launcher")
    gui.addChoice("Mode", mode_choices, mode_choices[0])
    gui.showDialog()
    if not gui.wasOKed():
        return
    mode = gui.getNextChoice()

    if mode == mode_choices[0]:
        gui = GenericDialogPlus(mode)
        gui.addDirectoryOrFileField("Bead data folder", prefs.get(None, "launcher_bead_folder_", ""))
        gui.addChoice("Image file extension", extension_choices, prefs.get(None, "launcher_extension_", extension_choices[0]))
        gui.addStringField("File pattern", prefs.get(None, "launcher_filepattern_", DEFAULT_FILE_PATTERN), 40)
        gui.addNumericField("Pixel size XY (um)", prefs.getFloat(None, "launcher_pixel_", 0.0), 4)
        gui.addNumericField("Prism angle (degrees)", prefs.getFloat(None, "launcher_prism_angle_", 17.5), 2)
        gui.addStringField("Bead well to use: all if only one, no_well, or WellF5", prefs.get(None, "launcher_bead_well_", "all"), 30)
        gui.addDirectoryField("Manifest output folder", prefs.get(None, "launcher_manifest_folder_", ""))
        gui.showDialog()
        if not gui.wasOKed():
            return
        bead_folder = gui.getNextString()
        extension = gui.getNextChoice()
        filepattern = gui.getNextString()
        pixel = gui.getNextNumber()
        prism_angle = gui.getNextNumber()
        wells_text = gui.getNextString()
        manifest_folder = gui.getNextString()
        create_and_register_bead_dataset(bead_folder, extension, filepattern, pixel, prism_angle, wells_text, manifest_folder)

    elif mode == mode_choices[1]:
        gui = GenericDialogPlus(mode)
        gui.addFileField("Predefined/manual bead registration XML", prefs.get(None, "launcher_bead_xml_", ""))
        gui.addFileField("Sample manifest CSV", prefs.get(None, "launcher_manifest_path_", ""))
        gui.showDialog()
        if not gui.wasOKed():
            return
        bead_xml = gui.getNextString()
        manifest_path = gui.getNextString()
        transfer_predefined_bead_xml_to_manifest(bead_xml, manifest_path)

    elif mode == mode_choices[2]:
        gui = GenericDialogPlus(mode)
        gui.addFileField("Predefined/manual bead registration XML", prefs.get(None, "launcher_bead_xml_", ""))
        gui.addDirectoryField("Folder containing sample XMLs", prefs.get(None, "launcher_xml_folder_", ""))
        gui.addStringField("Optional XML filename filter, e.g. angle70", prefs.get(None, "launcher_xml_filter_", ""), 20)
        gui.showDialog()
        if not gui.wasOKed():
            return
        bead_xml = gui.getNextString()
        xml_folder = gui.getNextString()
        xml_filter = gui.getNextString()
        transfer_predefined_bead_xml_to_folder(bead_xml, xml_folder, xml_filter)


if __name__ in ['__builtin__', '__main__']:
    main()
    IJ.log("dOPM registration launcher finished")
