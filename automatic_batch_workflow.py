# dOPM Automatic Batch Workflow
# Jython 2.7 compatible -- run inside Fiji/ImageJ
#
# Purpose:
#   One user-facing workflow that can:
#     1) use an existing registered bead XML, OR
#     2) automatically create/register a bead dataset when no XML exists,
#     3) batch-create/register sample datasets across well patterns,
#     4) optionally apply one common bead-derived bounding box,
#     5) optionally fuse all sample datasets,
#     6) optionally generate XYZ MIP montages from the fused outputs.
#
# This deliberately reuses the production dOPM workflow functions that were
# validated by Test_dOPM_EndToEnd_v3_faithful.py.

from __future__ import print_function

import os
import sys
import traceback
import xml.etree.ElementTree as ET

from java.lang import System
from ij import IJ
from ij.io import FileSaver, Opener
from fiji.util.gui import GenericDialogPlus
from loci.formats import ImageReader, MetadataTools
from net.haesleinhuepf.clij2 import CLIJ2


PATTERN = "spim_Time{tttt}_Tile{xxxx}_angle{a}"
EXTENSION = ".nd2"


def log(msg):
    print(msg)
    IJ.log("[dOPM AUTO] " + str(msg))


def get_fiji_dir():
    value = System.getProperty("fiji.dir")
    if value is None:
        raise RuntimeError("Java property fiji.dir is not set")
    return os.path.abspath(str(value))


def clear_module(name):
    if name in sys.modules:
        del sys.modules[name]


def import_workflows():
    dopm_dir = os.path.join(get_fiji_dir(), "plugins", "Scripts", "dOPM")
    if not os.path.isdir(dopm_dir):
        raise RuntimeError("dOPM folder not found: " + dopm_dir)

    if dopm_dir not in sys.path:
        sys.path.append(dopm_dir)

    compiled = os.path.join(dopm_dir, "dopmmvr$py.class")
    if os.path.isfile(compiled):
        try:
            os.remove(compiled)
        except Exception:
            pass

    clear_module("dopmmvr")
    clear_module("make_mvr_dataset")
    clear_module("define_bounding_box")
    clear_module("get_deskewed_dopm_volumes")

    import dopmmvr
    import make_mvr_dataset
    import define_bounding_box
    import get_deskewed_dopm_volumes

    return dopmmvr, make_mvr_dataset, define_bounding_box, get_deskewed_dopm_volumes


def list_nd2(folder):
    out = []
    if not os.path.isdir(folder):
        return out
    for name in os.listdir(folder):
        if name.lower().endswith(EXTENSION):
            out.append(name)
    out.sort()
    return out


def find_first_nd2_recursive(folder):
    for root, dirs, files in os.walk(folder):
        # Avoid walking our own output/test folders forever.
        dirs[:] = [d for d in dirs if not d.startswith("_dopm_")]
        for name in sorted(files):
            if name.lower().endswith(EXTENSION):
                return os.path.join(root, name)
    return None


def read_nd2_metadata(path_):
    reader = ImageReader()
    meta = MetadataTools.createOMEXMLMetadata()
    reader.setMetadataStore(meta)
    try:
        reader.setId(path_)
        px = None
        size_x = meta.getPixelsPhysicalSizeX(0)
        if size_x is not None:
            px = float(size_x.value())
        size_z = int(reader.getSizeZ())
        return px, size_z
    finally:
        try:
            reader.close()
        except Exception:
            pass


def infer_prism_angle(folder):
    angles = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith("_dopm_")]
        for name in files:
            if not name.lower().endswith(EXTENSION):
                continue
            stem = os.path.splitext(name)[0]
            token = "_angle"
            idx = stem.find(token)
            if idx < 0:
                continue
            rest = stem[idx + len(token):]
            digits = ""
            for ch in rest:
                if ch.isdigit() or ch == "." or ch == "-":
                    digits += ch
                else:
                    break
            if digits:
                try:
                    angles.append(float(digits))
                except Exception:
                    pass
    angles = sorted(list(set(angles)))
    if len(angles) == 2 and abs(angles[0]) < 1e-9:
        return angles[1] / 4.0
    return 17.5


def find_dataset_xmls(folder):
    out = []
    if not os.path.isdir(folder):
        return out
    for name in os.listdir(folder):
        if name.startswith("dataset") and name.lower().endswith(".xml"):
            full = os.path.join(folder, name)
            if os.path.isfile(full):
                out.append(full)
    out.sort()
    return out


def find_bead_xml_candidates(bead_folder):
    candidates = []

    # Prefer the HDF5 copy because that is what the faithful validation used
    # as the bead-registration source for sample processing.
    hdf5_dir = os.path.join(bead_folder, "hdf5")
    if os.path.isdir(hdf5_dir):
        for path_ in find_dataset_xmls(hdf5_dir):
            candidates.append(path_)

    for path_ in find_dataset_xmls(bead_folder):
        if path_ not in candidates:
            candidates.append(path_)

    return candidates


def choose_existing_bead_xml(bead_folder, candidates):
    if len(candidates) == 1:
        return candidates[0]

    labels = []
    for path_ in candidates:
        try:
            labels.append(os.path.relpath(path_, bead_folder))
        except Exception:
            labels.append(path_)

    gd = GenericDialogPlus("Choose registered bead XML")
    gd.addMessage(
        "More than one bead dataset XML was found.\n"
        "Choose the registered/optimised bead XML to use as the source."
    )
    gd.addChoice("Bead XML", labels, labels[0])
    gd.showDialog()
    if not gd.wasOKed():
        return None
    chosen = gd.getNextChoice()
    return candidates[labels.index(chosen)]


def get_xml_bounding_box(xml_path):
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return None
    boxes = root.find("./BoundingBoxes")
    if boxes is None:
        return None
    for node in list(boxes):
        if node.get("name") == "My Bounding Box":
            min_node = node.find("min")
            max_node = node.find("max")
            if min_node is None or max_node is None:
                return None
            return [min_node.text.split(), max_node.text.split()]
    return None


def find_bbox_source_xml(bead_folder, preferred_xml):
    # First use the selected bead XML if it already contains the named box.
    if get_xml_bounding_box(preferred_xml) is not None:
        return preferred_xml

    # Otherwise search the other bead XMLs; in the validated workflow the root
    # XML carries the common bounding box while the HDF5 XML is used for
    # registration transfer.
    for path_ in find_bead_xml_candidates(bead_folder):
        if get_xml_bounding_box(path_) is not None:
            return path_

    return None


def build_bead_setup(dopmmvr, make_workflow, bead_folder, pixel, angle):
    bead_suffix, bead_tail = make_workflow.get_single_bead_well_info(
        bead_folder, EXTENSION
    )
    basename = make_workflow.make_dataset_basename(bead_suffix)
    beads = dopmmvr.mvrsetup(
        datapath=bead_folder,
        regpath=r'',
        filepattern=PATTERN,
        extension=EXTENSION,
        px=pixel,
        py=pixel,
        angle=angle,
        well_suffix=bead_suffix,
        well_tail=bead_tail,
        dataset_basename=basename,
        view_mode='two_view'
    )
    return beads


def automatically_make_bead_dataset(dopmmvr, make_workflow,
                                    bead_folder, pixel, angle,
                                    need_bbox):
    log("No bead XML found: starting automatic bead workflow")

    beads = build_bead_setup(dopmmvr, make_workflow, bead_folder, pixel, angle)
    if not beads.dims:
        raise RuntimeError("No valid bead files matched the expected dOPM filename pattern")

    log("Creating bead dataset XML")
    beads.createXMLdataset()
    root_xml = os.path.join(bead_folder, beads.dataset)

    log("Applying calibration")
    beads.ApplyCalibrationFromXML()

    log("Applying dOPM geometric transforms")
    beads.transformXMLdataset()

    log("Registering bead dataset")
    beads.RegisterDataset()

    log("Resaving registered bead dataset to HDF5")
    beads.ResaveXMLtoHDF5(bead_folder)
    hdf5_xml = os.path.join(bead_folder, "hdf5", beads.dataset)
    if not os.path.isfile(hdf5_xml):
        raise RuntimeError("Expected HDF5 bead XML was not created: " + hdf5_xml)

    bbox_source = root_xml
    if need_bbox:
        log("Calculating bead-derived common bounding box")
        bbox = dopmmvr.defineboundingbox(
            dataset=beads.dataset,
            rawzplanes=beads.dims[2],
            prismangle=angle
        )
        bb = bbox.OptimalBoundingBox(bead_folder)
        bbox.defineBoundingBoxNoInteraction(bead_folder)
        bbox.modifyBoundingBox(bead_folder, bb)
        if get_xml_bounding_box(root_xml) is None:
            raise RuntimeError("Automatic bead workflow did not create 'My Bounding Box'")

    return hdf5_xml, bbox_source


def compute_bbox_for_existing_xml(dopmmvr, bead_folder, bead_xml, angle):
    raw = find_first_nd2_recursive(bead_folder)
    if raw is None:
        raise RuntimeError(
            "Cannot calculate a bounding box automatically because no bead ND2 file was found"
        )

    _, size_z = read_nd2_metadata(raw)
    xml_folder = os.path.dirname(bead_xml)
    dataset_name = os.path.basename(bead_xml)

    log("Calculating missing bounding box from existing bead XML")
    bbox = dopmmvr.defineboundingbox(
        dataset=dataset_name,
        rawzplanes=size_z,
        prismangle=angle
    )
    bb = bbox.OptimalBoundingBox(xml_folder)
    bbox.defineBoundingBoxNoInteraction(xml_folder)
    bbox.modifyBoundingBox(xml_folder, bb)

    if get_xml_bounding_box(bead_xml) is None:
        raise RuntimeError("Bounding box calculation completed but no 'My Bounding Box' was stored")

    return bead_xml


def prompt_no_xml_action():
    gd = GenericDialogPlus("No bead XML found")
    gd.addMessage(
        "The bead folder does not contain a dataset XML.\n\n"
        "Recommended conservative option:\n"
        "  Abort, run the existing Make MVR Dataset bead workflow, inspect the bead registration,\n"
        "  then run this automatic script again.\n\n"
        "Alternatively this script can run the same bead workflow automatically."
    )
    gd.addChoice(
        "Action",
        ["Abort and use the existing bead workflow", "Try automatic bead processing"],
        "Abort and use the existing bead workflow"
    )
    gd.showDialog()
    if not gd.wasOKed():
        return "abort"
    choice = gd.getNextChoice()
    if choice.startswith("Try automatic"):
        return "automatic"
    return "abort"


def get_main_options():
    gd = GenericDialogPlus("dOPM Automatic Batch Workflow")
    gd.addMessage(
        "Batch workflow: registered beads -> all sample wells -> optional common BB -> fusion -> MIPs\n"
        "Raw ND2 files are not modified. Dataset XML/HDF5/output files are written to the selected folders."
    )
    gd.addDirectoryField("Bead folder", "")
    gd.addDirectoryField("Data folder", "")
    gd.addDirectoryField("Output folder (blank = data/dOPM_output)", "")
    gd.addNumericField("Pixel size (um)", 0.35, 6)
    gd.addNumericField("Prism / mirror angle (degrees)", 17.5, 2)
    gd.addChoice("Fusion binning", ["1", "2", "4", "8", "16"], "2")
    gd.addCheckbox("Use one bead-derived bounding box for all sample datasets", True)
    gd.addCheckbox("Fuse all sample datasets", True)
    gd.addCheckbox("Create XYZ MIP montages after fusion", True)
    gd.addCheckbox("Allow rebuilding existing sample dataset XMLs", False)
    gd.showDialog()

    if not gd.wasOKed():
        return None

    bead_folder = os.path.abspath(gd.getNextString())
    data_folder = os.path.abspath(gd.getNextString())
    output_text = gd.getNextString().strip()
    pixel = gd.getNextNumber()
    angle = gd.getNextNumber()
    binning = gd.getNextChoice()
    use_bbox = gd.getNextBoolean()
    do_fuse = gd.getNextBoolean()
    do_mips = gd.getNextBoolean()
    allow_rebuild = gd.getNextBoolean()

    if do_mips and not do_fuse:
        # MIPs in this workflow are generated from fused TIFF stacks.
        do_fuse = True
        log("MIPs were requested, so fusion has been enabled automatically")

    if output_text:
        output_folder = os.path.abspath(output_text)
    else:
        output_folder = os.path.join(data_folder, "dOPM_output")

    return {
        "bead_folder": bead_folder,
        "data_folder": data_folder,
        "output_folder": output_folder,
        "pixel": pixel,
        "angle": angle,
        "binning": str(binning),
        "use_bbox": use_bbox,
        "do_fuse": do_fuse,
        "do_mips": do_mips,
        "allow_rebuild": allow_rebuild
    }


def open_image_robust(path_):
    imp = None
    try:
        imp = Opener().openImage(path_)
    except Exception:
        imp = None
    if imp is None:
        try:
            imp = IJ.openImage(path_)
        except Exception:
            imp = None
    return imp


def get_stack_list(folder):
    out = []
    if not os.path.isdir(folder):
        return out
    for name in os.listdir(folder):
        low = name.lower()
        if low.endswith(".tif") or low.endswith(".tiff"):
            out.append(os.path.join(folder, name))
    out.sort()
    return out


def get_mips_on_folder(datapath):
    # Same processing path used by the faithful end-to-end validator and the
    # existing get_fused_MIPs workflow.
    mip_dir = os.path.join(datapath, "MIP")
    if not os.path.isdir(mip_dir):
        os.makedirs(mip_dir)

    tiffs = get_stack_list(datapath)
    if len(tiffs) == 0:
        raise RuntimeError("No fused TIFF stacks found in: " + datapath)

    made = []
    for tiff_stack in tiffs:
        clij2 = CLIJ2.getInstance()
        imp = open_image_robust(tiff_stack)
        if imp is None:
            raise RuntimeError("Could not open: " + tiff_stack)
        final_imp = None
        try:
            dims = imp.getDimensions()
            imageInput = clij2.push(imp)
            imageOutput1 = clij2.create([dims[0], dims[1]], imageInput.getNativeType())
            clij2.maximumZProjection(imageInput, imageOutput1)
            imageOutput2 = clij2.create([dims[3], dims[1]], imageInput.getNativeType())
            clij2.maximumXProjection(imageInput, imageOutput2)
            imageOutput3 = clij2.create([dims[0], dims[3]], imageInput.getNativeType())
            clij2.maximumYProjection(imageInput, imageOutput3)
            imageOutput4 = clij2.create([dims[0] + dims[3], dims[1]], imageInput.getNativeType())
            clij2.combineHorizontally(imageOutput1, imageOutput2, imageOutput4)
            imageOutput5 = clij2.create([dims[3], dims[1]], imageInput.getNativeType())
            imageOutput6 = clij2.create([dims[0] + dims[3], dims[1]], imageInput.getNativeType())
            clij2.combineHorizontally(imageOutput3, imageOutput5, imageOutput6)
            imageOutput7 = clij2.create([dims[0] + dims[3], dims[1] + dims[1]], imageInput.getNativeType())
            clij2.combineVertically(imageOutput4, imageOutput6, imageOutput7)
            final_imp = clij2.pull(imageOutput7)
            stem = os.path.splitext(os.path.basename(tiff_stack))[0]
            out_path = os.path.join(mip_dir, stem + ".tif")
            if not FileSaver(final_imp).saveAsTiff(out_path):
                raise RuntimeError("Failed to save MIP: " + out_path)
            made.append(out_path)
        finally:
            try:
                if final_imp is not None:
                    final_imp.close()
            except Exception:
                pass
            try:
                imp.close()
            except Exception:
                pass
            clij2.clear()
    return made


def find_dataset_output_folders(root_folder, binning):
    matches = []
    suffix = "_fused_binning_" + str(binning)
    if not os.path.isdir(root_folder):
        return matches
    for each in os.listdir(root_folder):
        dataset_dir = os.path.join(root_folder, each)
        if not os.path.isdir(dataset_dir) or not each.startswith("dataset"):
            continue
        candidate = os.path.join(dataset_dir, each + suffix)
        if os.path.isdir(candidate):
            matches.append(candidate)
    matches.sort()
    return matches


def make_all_mips(root_folder, binning):
    folders = find_dataset_output_folders(root_folder, binning)
    if len(folders) == 0:
        raise RuntimeError("No fused dataset output folders found under: " + root_folder)
    counts = {}
    for folder in folders:
        log("Making MIPs: " + folder)
        counts[folder] = len(get_mips_on_folder(folder))
    return counts


def write_report(path_, opts, bead_source_xml, bbox_source_xml,
                 sample_xmls, mip_counts):
    f = open(path_, "w")
    try:
        f.write("dOPM Automatic Batch Workflow\n")
        f.write("=" * 80 + "\n")
        f.write("bead folder: " + opts["bead_folder"] + "\n")
        f.write("data folder: " + opts["data_folder"] + "\n")
        f.write("bead registration XML: " + bead_source_xml + "\n")
        f.write("bounding-box source XML: " + str(bbox_source_xml) + "\n")
        f.write("pixel size (um): " + str(opts["pixel"]) + "\n")
        f.write("prism / mirror angle (deg): " + str(opts["angle"]) + "\n")
        f.write("use common BB: " + str(opts["use_bbox"]) + "\n")
        f.write("fusion: " + str(opts["do_fuse"]) + "\n")
        f.write("fusion binning: " + str(opts["binning"]) + "\n")
        f.write("MIPs: " + str(opts["do_mips"]) + "\n")
        f.write("\nSample datasets:\n")
        for xml_name in sample_xmls:
            f.write("  " + xml_name + "\n")
        if mip_counts:
            f.write("\nMIP outputs:\n")
            for folder in sorted(mip_counts.keys()):
                f.write("  " + folder + ": " + str(mip_counts[folder]) + "\n")
        f.write("\nRESULT: PASS\n")
    finally:
        f.close()


def main():
    opts = get_main_options()
    if opts is None:
        return

    if not os.path.isdir(opts["bead_folder"]):
        IJ.error("dOPM Automatic Batch", "Bead folder does not exist:\n" + opts["bead_folder"])
        return
    if not os.path.isdir(opts["data_folder"]):
        IJ.error("dOPM Automatic Batch", "Data folder does not exist:\n" + opts["data_folder"])
        return
    if opts["pixel"] <= 0 or opts["angle"] <= 0:
        IJ.error("dOPM Automatic Batch", "Pixel size and angle must be greater than zero")
        return

    existing_sample_xmls = find_dataset_xmls(opts["data_folder"])
    if existing_sample_xmls and not opts["allow_rebuild"]:
        IJ.error(
            "dOPM Automatic Batch",
            "Existing sample dataset XMLs were found in the data folder.\n\n"
            "To avoid overwriting/rebuilding them, this run has stopped.\n"
            "Tick 'Allow rebuilding existing sample dataset XMLs' if that is intentional."
        )
        return

    try:
        dopmmvr, make_workflow, bb_workflow, volume_workflow = import_workflows()

        candidates = find_bead_xml_candidates(opts["bead_folder"])
        bead_source_xml = None
        bbox_source_xml = None

        if candidates:
            bead_source_xml = choose_existing_bead_xml(opts["bead_folder"], candidates)
            if bead_source_xml is None:
                return
            log("Using existing registered bead XML: " + bead_source_xml)
            bbox_source_xml = find_bbox_source_xml(opts["bead_folder"], bead_source_xml)

            if opts["use_bbox"] and bbox_source_xml is None:
                bbox_source_xml = compute_bbox_for_existing_xml(
                    dopmmvr, opts["bead_folder"], bead_source_xml, opts["angle"]
                )

        else:
            action = prompt_no_xml_action()
            if action != "automatic":
                IJ.showMessage(
                    "dOPM Automatic Batch",
                    "No bead dataset was created.\n\n"
                    "Run the existing Make MVR Dataset bead workflow, inspect/optimise the registration,\n"
                    "then run this automatic batch script again."
                )
                return

            bead_source_xml, bbox_source_xml = automatically_make_bead_dataset(
                dopmmvr,
                make_workflow,
                opts["bead_folder"],
                opts["pixel"],
                opts["angle"],
                opts["use_bbox"]
            )

        log("Creating/registering sample datasets across detected well patterns")
        make_workflow.process_data_with_beads(
            bead_source_xml,
            opts["data_folder"],
            EXTENSION,
            PATTERN,
            opts["pixel"],
            opts["angle"]
        )

        sample_xml_paths = find_dataset_xmls(opts["data_folder"])
        if len(sample_xml_paths) == 0:
            raise RuntimeError("No sample dataset XMLs were created")
        sample_xml_names = [os.path.basename(x) for x in sample_xml_paths]
        log("Sample datasets: " + str(sample_xml_names))

        if opts["use_bbox"]:
            if bbox_source_xml is None:
                raise RuntimeError("A common bounding box was requested but no bead bounding-box source is available")
            log("Applying one bead-derived bounding box to every sample XML")
            bb_workflow.batch_apply_existing_bb(
                bbox_source_xml,
                opts["data_folder"]
            )

        mip_counts = {}
        if opts["do_fuse"]:
            if not os.path.isdir(opts["output_folder"]):
                os.makedirs(opts["output_folder"])

            if opts["use_bbox"]:
                dopmmvr.mvrgetvolumes.BB = "My Bounding Box"
            else:
                dopmmvr.mvrgetvolumes.BB = "All Views"

            log("Fusing all sample dataset XMLs")
            volume_workflow.run_batch_for_all_xmls(
                opts["data_folder"],
                opts["output_folder"],
                opts["binning"],
                mode="fused"
            )

            if opts["do_mips"]:
                log("Generating XYZ MIP montages from all fused dataset folders")
                mip_counts = make_all_mips(opts["output_folder"], opts["binning"])

        report_path = os.path.join(opts["data_folder"], "dOPM_automatic_batch_report.txt")
        write_report(
            report_path,
            opts,
            bead_source_xml,
            bbox_source_xml,
            sample_xml_names,
            mip_counts
        )

        log("DONE")
        IJ.showMessage(
            "dOPM Automatic Batch - Complete",
            "The workflow completed successfully.\n\n"
            "Sample datasets: " + str(len(sample_xml_names)) + "\n"
            "Report:\n" + report_path
        )

    except Exception as exc:
        traceback.print_exc()
        IJ.error(
            "dOPM Automatic Batch - Failed",
            exc.__class__.__name__ + ": " + str(exc) +
            "\n\nSee the Fiji Log / Script Editor console for the full traceback."
        )


main()
