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
    detect_dataset_summary,
    log_summary,
    parse_well_selection,
    filter_rows_for_well_angle,
    validate_complete_combinations,
    format_well_list,
    normalize_angle,
    expected_second_angle,
    make_dataset_basename,
    well_suffix_from_tail,
)


def preview_outputs(selected_wells, dataset_mode, single_angle):
    IJ.log("Predicted dataset XML names:")
    for tail in selected_wells:
        suffix = well_suffix_from_tail(tail)
        if dataset_mode == 'single_view':
            root = make_dataset_basename(suffix, single_angle)
        else:
            root = make_dataset_basename(suffix)
        IJ.log("  " + root + ".xml")


def run_preflight(datapath, extension, wells_text, dataset_mode, single_angle, prism_angle):
    summary = detect_dataset_summary(datapath, extension)
    log_summary(summary)

    if len(summary['rows']) == 0:
        raise ValueError("No valid input files detected.")

    selected_wells = parse_well_selection(wells_text, summary['wells'])
    IJ.log("Selected wells: " + format_well_list(selected_wells))

    if dataset_mode == 'single_view':
        single_angle = normalize_angle(single_angle)
        if single_angle is None:
            raise ValueError("Single-view preflight requires angle 0 or " + expected_second_angle(prism_angle))
        IJ.log("Selected single-view angle: angle" + single_angle)
    else:
        single_angle = None

    for tail in selected_wells:
        rows = filter_rows_for_well_angle(summary['rows'], tail, single_angle)
        label = "well " + str(well_suffix_from_tail(tail))
        if tail is None:
            label = "no well suffix"
        IJ.log("Checking " + label + ": " + str(len(rows)) + " matching files")
        warnings = validate_complete_combinations(rows, label)
        for w in warnings:
            IJ.log("Warning: " + w)

    preview_outputs(selected_wells, dataset_mode, single_angle)


def main():
    extension_choices = [".nd2", ".tif", ".tiff"]
    dataset_modes = ["two_view", "single_view"]

    gui = GenericDialogPlus("dOPM preflight")
    gui.addDirectoryOrFileField("Input data folder", prefs.get(None, "launcher_datapath_", ""))
    gui.addChoice("Image file extension", extension_choices, prefs.get(None, "launcher_extension_", extension_choices[0]))
    gui.addStringField("Wells to process: all, WellF5, or WellF5,WellG5", prefs.get(None, "launcher_wells_", "all"), 30)
    gui.addChoice("Dataset mode", dataset_modes, prefs.get(None, "launcher_dataset_mode_", dataset_modes[0]))
    gui.addStringField("Single-view angle, e.g. 0 or 70", prefs.get(None, "launcher_single_angle_", "70"), 8)
    gui.addNumericField("Prism angle (degrees)", prefs.getFloat(None, "launcher_prism_angle_", 17.5), 2)
    gui.showDialog()

    if not gui.wasOKed():
        return

    datapath = gui.getNextString()
    extension = gui.getNextChoice()
    wells_text = gui.getNextString()
    dataset_mode = gui.getNextChoice()
    single_angle = gui.getNextString()
    prism_angle = gui.getNextNumber()

    prefs.put(None, "launcher_datapath_", datapath)
    prefs.put(None, "launcher_extension_", extension)
    prefs.put(None, "launcher_wells_", wells_text)
    prefs.put(None, "launcher_dataset_mode_", dataset_mode)
    prefs.put(None, "launcher_single_angle_", single_angle)
    prefs.put(None, "launcher_prism_angle_", prism_angle)

    run_preflight(datapath, extension, wells_text, dataset_mode, single_angle, prism_angle)


if __name__ in ['__builtin__', '__main__']:
    main()
    IJ.log("dOPM preflight finished")
