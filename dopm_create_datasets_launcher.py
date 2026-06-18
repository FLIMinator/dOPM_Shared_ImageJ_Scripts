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
    create_rows_for_selected_wells,
    write_manifest,
    normpath,
    normalize_angle,
    expected_second_angle,
)


def run_create(datapath, extension, filepattern, pixel, prism_angle,
               wells_text, dataset_mode, single_angle,
               registration_choice, bead_xml, manifest_folder):
    summary = detect_dataset_summary(datapath, extension)
    log_summary(summary)
    selected_wells = parse_well_selection(wells_text, summary['wells'])
    IJ.log("Selected wells: " + format_well_list(selected_wells))

    if dataset_mode == 'single_view':
        single_angle = normalize_angle(single_angle)
        if single_angle is None:
            raise ValueError("Single-view mode requires angle 0 or " + expected_second_angle(prism_angle))
    else:
        single_angle = None

    if registration_choice == 'none':
        registration_mode = 'none'
        bead_xml = None
    elif registration_choice == 'copy predefined bead XML':
        registration_mode = 'copy_bead_xml'
        if bead_xml is None or str(bead_xml).strip() == "":
            raise ValueError("Please choose the predefined/manual bead registration XML.")
        bead_xml = normpath(bead_xml)
    else:
        raise ValueError("Unknown registration choice: " + str(registration_choice))

    rows = create_rows_for_selected_wells(
        datapath, extension, filepattern, pixel, prism_angle,
        selected_wells, dataset_mode,
        single_view_angle=single_angle,
        registration_mode=registration_mode,
        bead_xml=bead_xml
    )

    if manifest_folder is None or str(manifest_folder).strip() == "":
        manifest_folder = datapath
    manifest_path = os.path.join(normpath(manifest_folder), MANIFEST_NAME)
    write_manifest(manifest_path, rows)
    return rows


def main():
    extension_choices = [".nd2", ".tif", ".tiff"]
    dataset_modes = ["two_view", "single_view"]
    registration_choices = ["none", "copy predefined bead XML"]

    gui = GenericDialogPlus("dOPM create datasets launcher")
    gui.addDirectoryOrFileField("Input data folder", prefs.get(None, "launcher_datapath_", ""))
    gui.addChoice("Image file extension", extension_choices, prefs.get(None, "launcher_extension_", extension_choices[0]))
    gui.addStringField("File pattern", prefs.get(None, "launcher_filepattern_", DEFAULT_FILE_PATTERN), 40)
    gui.addNumericField("Pixel size XY (um)", prefs.getFloat(None, "launcher_pixel_", 0.0), 4)
    gui.addNumericField("Prism angle (degrees)", prefs.getFloat(None, "launcher_prism_angle_", 17.5), 2)
    gui.addStringField("Wells to process: all, WellF5, or WellF5,WellG5", prefs.get(None, "launcher_wells_", "all"), 30)
    gui.addChoice("Dataset mode", dataset_modes, prefs.get(None, "launcher_dataset_mode_", dataset_modes[0]))
    gui.addStringField("Single-view angle, e.g. 0 or 70", prefs.get(None, "launcher_single_angle_", "70"), 8)
    gui.addChoice("Registration", registration_choices, prefs.get(None, "launcher_registration_choice_", registration_choices[0]))
    gui.addFileField("Predefined/manual bead registration XML", prefs.get(None, "launcher_bead_xml_", ""))
    gui.addDirectoryField("Manifest output folder", prefs.get(None, "launcher_manifest_folder_", ""))
    gui.showDialog()

    if not gui.wasOKed():
        return

    datapath = gui.getNextString()
    extension = gui.getNextChoice()
    filepattern = gui.getNextString()
    pixel = gui.getNextNumber()
    prism_angle = gui.getNextNumber()
    wells_text = gui.getNextString()
    dataset_mode = gui.getNextChoice()
    single_angle = gui.getNextString()
    registration_choice = gui.getNextChoice()
    bead_xml = gui.getNextString()
    manifest_folder = gui.getNextString()

    prefs.put(None, "launcher_datapath_", datapath)
    prefs.put(None, "launcher_extension_", extension)
    prefs.put(None, "launcher_filepattern_", filepattern)
    prefs.put(None, "launcher_pixel_", pixel)
    prefs.put(None, "launcher_prism_angle_", prism_angle)
    prefs.put(None, "launcher_wells_", wells_text)
    prefs.put(None, "launcher_dataset_mode_", dataset_mode)
    prefs.put(None, "launcher_single_angle_", single_angle)
    prefs.put(None, "launcher_registration_choice_", registration_choice)
    prefs.put(None, "launcher_bead_xml_", bead_xml)
    prefs.put(None, "launcher_manifest_folder_", manifest_folder)

    run_create(datapath, extension, filepattern, pixel, prism_angle,
               wells_text, dataset_mode, single_angle,
               registration_choice, bead_xml, manifest_folder)


if __name__ in ['__builtin__', '__main__']:
    main()
    IJ.log("dOPM create datasets launcher finished")
