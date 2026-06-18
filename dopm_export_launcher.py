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
    MANIFEST_NAME,
    read_manifest,
    find_dataset_xmls,
    split_dataset_path,
    apply_bounding_box,
    export_rows,
    verify_export_outputs,
    run_mips_for_export_outputs,
    normpath,
)


def rows_from_folder(xml_folder, name_filter):
    xmls = find_dataset_xmls(xml_folder, name_filter=name_filter)
    rows = []
    for xmlpath in xmls:
        datapath, dataset = split_dataset_path(xmlpath)
        rows.append({
            'well': '',
            'well_tail': '',
            'view_mode': '',
            'angle': '',
            'xml_path': xmlpath,
            'dataset': dataset,
            'datapath': datapath,
            'raw_z_planes': '',
            'bounding_box': '',
            'export_mode': '',
            'export_path': ''
        })
    return rows


def run_export(rows, bb_mode, reference_xml, rawzplanes, prism_angle,
               savepath, binning, export_mode, crop, export_angle, make_mips):
    if len(rows) == 0:
        raise ValueError("No XML rows selected for export.")

    # If geometry_per_xml and manifest has raw_z_planes, per-row values are used.
    # For folder-only mode, rawzplanes from the GUI is used.
    rows = apply_bounding_box(rows, bb_mode, rawzplanes, prism_angle, reference_xml=reference_xml)

    rows = export_rows(rows, savepath, binning, export_mode, crop, requested_angle=export_angle)
    verify_export_outputs(savepath, rows, export_mode, binning, requested_angle=export_angle)

    if make_mips:
        run_mips_for_export_outputs(savepath, rows, export_mode, binning, requested_angle=export_angle)

    return rows


def main():
    input_choices = ["manifest CSV", "folder of XMLs"]
    bb_choices = ["none", "geometry_per_xml", "geometry_from_reference", "copy_existing", "manual_reference"]
    export_choices = ["fused", "single_angle", "both_single_views"]
    yesno = ["no", "yes"]
    binning_choices = ["1", "2", "4", "8", "16"]

    gui = GenericDialogPlus("dOPM bounding-box/export launcher")
    gui.addChoice("Input XML list", input_choices, input_choices[0])
    gui.addFileField("Manifest CSV", prefs.get(None, "launcher_manifest_path_", ""))
    gui.addDirectoryField("Folder containing XMLs", prefs.get(None, "launcher_xml_folder_", ""))
    gui.addStringField("Optional XML filename filter, e.g. angle70", prefs.get(None, "launcher_xml_filter_", ""), 20)
    gui.addChoice("Bounding box mode", bb_choices, bb_choices[0])
    gui.addFileField("Reference XML for bounding box modes", prefs.get(None, "launcher_reference_xml_", ""))
    gui.addNumericField("Raw Z planes for geometry mode", prefs.getFloat(None, "launcher_rawzplanes_", 0), 0)
    gui.addNumericField("Prism angle (degrees)", prefs.getFloat(None, "launcher_prism_angle_", 17.5), 2)
    gui.addDirectoryField("Export save root", prefs.get(None, "launcher_savepath_", ""))
    gui.addChoice("Binning", binning_choices, prefs.get(None, "launcher_binning_", binning_choices[0]))
    gui.addChoice("Export mode", export_choices, export_choices[0])
    gui.addStringField("Export angle for single_angle mode, e.g. 0 or 70", prefs.get(None, "launcher_export_angle_", "70"), 8)
    gui.addChoice("Crop using My Bounding Box", yesno, prefs.get(None, "launcher_crop_", yesno[0]))
    gui.addChoice("Generate MIPs after export", yesno, prefs.get(None, "launcher_make_mips_", yesno[1]))
    gui.showDialog()

    if not gui.wasOKed():
        return

    input_choice = gui.getNextChoice()
    manifest_path = gui.getNextString()
    xml_folder = gui.getNextString()
    xml_filter = gui.getNextString()
    bb_mode = gui.getNextChoice()
    reference_xml = gui.getNextString()
    rawzplanes = gui.getNextNumber()
    prism_angle = gui.getNextNumber()
    savepath = gui.getNextString()
    binning = gui.getNextChoice()
    export_mode = gui.getNextChoice()
    export_angle = gui.getNextString()
    crop = (gui.getNextChoice() == 'yes')
    make_mips = (gui.getNextChoice() == 'yes')

    prefs.put(None, "launcher_manifest_path_", manifest_path)
    prefs.put(None, "launcher_xml_folder_", xml_folder)
    prefs.put(None, "launcher_xml_filter_", xml_filter)
    prefs.put(None, "launcher_reference_xml_", reference_xml)
    prefs.put(None, "launcher_rawzplanes_", rawzplanes)
    prefs.put(None, "launcher_prism_angle_", prism_angle)
    prefs.put(None, "launcher_savepath_", savepath)
    prefs.put(None, "launcher_binning_", binning)
    prefs.put(None, "launcher_export_angle_", export_angle)
    prefs.put(None, "launcher_crop_", 'yes' if crop else 'no')
    prefs.put(None, "launcher_make_mips_", 'yes' if make_mips else 'no')

    if input_choice == 'manifest CSV':
        rows = read_manifest(manifest_path)
    else:
        rows = rows_from_folder(xml_folder, xml_filter)

    run_export(rows, bb_mode, reference_xml, rawzplanes, prism_angle,
               savepath, binning, export_mode, crop, export_angle, make_mips)


if __name__ in ['__builtin__', '__main__']:
    main()
    IJ.log("dOPM export launcher finished")
