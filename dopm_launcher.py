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
    apply_bounding_box,
    export_rows,
    verify_export_outputs,
    run_mips_for_export_outputs,
    normpath,
    normalize_angle,
    expected_second_angle,
)


def confirm_plan(plan_lines):
    gui = GenericDialogPlus("Confirm dOPM launcher plan")
    gui.addMessage('\n'.join(plan_lines))
    gui.addCheckbox("Run this plan", False)
    gui.showDialog()
    if not gui.wasOKed():
        return False
    return gui.getNextBoolean()


def run_chained_workflow(datapath, extension, filepattern, pixel, prism_angle,
                         wells_text, dataset_mode, single_angle,
                         registration_choice, bead_xml,
                         bb_mode, reference_xml, rawzplanes,
                         savepath, binning, export_mode, crop, export_angle, make_mips,
                         do_export):
    summary = detect_dataset_summary(datapath, extension)
    log_summary(summary)
    selected_wells = parse_well_selection(wells_text, summary['wells'])

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
    else:
        raise ValueError("Unknown registration choice: " + str(registration_choice))

    plan = []
    plan.append("Workflow summary")
    plan.append("Input: " + str(datapath))
    plan.append("Wells: " + format_well_list(selected_wells))
    plan.append("Dataset mode: " + dataset_mode)
    if dataset_mode == 'single_view':
        plan.append("Single-view angle: angle" + str(single_angle))
    plan.append("Registration: " + registration_choice)
    if bead_xml is not None:
        plan.append("Bead XML: " + str(bead_xml))
    plan.append("Bounding box: " + str(bb_mode))
    if do_export:
        plan.append("Export: " + str(export_mode) + ", binning " + str(binning) + ", crop " + str(crop))
        if export_mode == 'single_angle':
            plan.append("Export angle: angle" + str(export_angle))
        plan.append("MIPs: " + str(make_mips))
    else:
        plan.append("Export: no")

    for line in plan:
        IJ.log(line)

    if not confirm_plan(plan):
        IJ.log("Launcher plan cancelled by user.")
        return []

    IJ.log("STEP 1/" + ("3" if do_export else "2") + ": Create and transform datasets")
    rows = create_rows_for_selected_wells(
        datapath, extension, filepattern, pixel, prism_angle,
        selected_wells, dataset_mode,
        single_view_angle=single_angle,
        registration_mode=registration_mode,
        bead_xml=bead_xml
    )

    manifest_path = os.path.join(normpath(datapath), MANIFEST_NAME)
    write_manifest(manifest_path, rows)

    IJ.log("STEP 2/" + ("3" if do_export else "2") + ": Bounding box")
    rows = apply_bounding_box(rows, bb_mode, rawzplanes, prism_angle, reference_xml=reference_xml)
    write_manifest(manifest_path, rows)

    if do_export:
        IJ.log("STEP 3/3: Export volumes")
        rows = export_rows(rows, savepath, binning, export_mode, crop, requested_angle=export_angle)
        verify_export_outputs(savepath, rows, export_mode, binning, requested_angle=export_angle)
        if make_mips:
            run_mips_for_export_outputs(savepath, rows, export_mode, binning, requested_angle=export_angle)
        write_manifest(manifest_path, rows)

    IJ.log("Launcher workflow complete. Manifest: " + manifest_path)
    return rows


def main():
    workflow_choices = [
        "preflight only",
        "create datasets only",
        "create datasets + bounding box",
        "create datasets + bounding box + export + optional MIPs"
    ]
    extension_choices = [".nd2", ".tif", ".tiff"]
    dataset_modes = ["two_view", "single_view"]
    registration_choices = ["none", "copy predefined bead XML"]
    bb_choices = ["none", "geometry_per_xml", "geometry_from_reference", "copy_existing", "manual_reference"]
    export_choices = ["fused", "single_angle", "both_single_views"]
    yesno = ["no", "yes"]
    binning_choices = ["1", "2", "4", "8", "16"]

    gui = GenericDialogPlus("dOPM master launcher")
    gui.addChoice("Workflow", workflow_choices, workflow_choices[0])
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
    gui.addChoice("Bounding box mode", bb_choices, prefs.get(None, "launcher_bb_mode_", bb_choices[0]))
    gui.addFileField("Reference XML for bounding-box modes", prefs.get(None, "launcher_reference_xml_", ""))
    gui.addNumericField("Raw Z planes for geometry mode", prefs.getFloat(None, "launcher_rawzplanes_", 0), 0)
    gui.addDirectoryField("Export save root", prefs.get(None, "launcher_savepath_", ""))
    gui.addChoice("Binning", binning_choices, prefs.get(None, "launcher_binning_", binning_choices[0]))
    gui.addChoice("Export mode", export_choices, prefs.get(None, "launcher_export_mode_", export_choices[0]))
    gui.addStringField("Export angle for single_angle mode, e.g. 0 or 70", prefs.get(None, "launcher_export_angle_", "70"), 8)
    gui.addChoice("Crop using My Bounding Box", yesno, prefs.get(None, "launcher_crop_", yesno[0]))
    gui.addChoice("Generate MIPs after export", yesno, prefs.get(None, "launcher_make_mips_", yesno[1]))
    gui.showDialog()

    if not gui.wasOKed():
        return

    workflow = gui.getNextChoice()
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
    bb_mode = gui.getNextChoice()
    reference_xml = gui.getNextString()
    rawzplanes = gui.getNextNumber()
    savepath = gui.getNextString()
    binning = gui.getNextChoice()
    export_mode = gui.getNextChoice()
    export_angle = gui.getNextString()
    crop = (gui.getNextChoice() == 'yes')
    make_mips = (gui.getNextChoice() == 'yes')

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
    prefs.put(None, "launcher_bb_mode_", bb_mode)
    prefs.put(None, "launcher_reference_xml_", reference_xml)
    prefs.put(None, "launcher_rawzplanes_", rawzplanes)
    prefs.put(None, "launcher_savepath_", savepath)
    prefs.put(None, "launcher_binning_", binning)
    prefs.put(None, "launcher_export_mode_", export_mode)
    prefs.put(None, "launcher_export_angle_", export_angle)
    prefs.put(None, "launcher_crop_", 'yes' if crop else 'no')
    prefs.put(None, "launcher_make_mips_", 'yes' if make_mips else 'no')

    if workflow == 'preflight only':
        from dopm_preflight import run_preflight
        run_preflight(datapath, extension, wells_text, dataset_mode, single_angle, prism_angle)
        return

    if workflow == 'create datasets only':
        bb_mode = 'none'
        do_export = False
    elif workflow == 'create datasets + bounding box':
        do_export = False
    else:
        do_export = True

    run_chained_workflow(datapath, extension, filepattern, pixel, prism_angle,
                         wells_text, dataset_mode, single_angle,
                         registration_choice, bead_xml,
                         bb_mode, reference_xml, rawzplanes,
                         savepath, binning, export_mode, crop, export_angle, make_mips,
                         do_export)


if __name__ in ['__builtin__', '__main__']:
    main()
    IJ.log("dOPM master launcher finished")
