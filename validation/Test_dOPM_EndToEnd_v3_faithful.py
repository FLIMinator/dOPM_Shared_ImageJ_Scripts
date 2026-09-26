# dOPM faithful end-to-end validation test
# Jython 2.7 compatible -- run inside Fiji/ImageJ
#
# This version deliberately mirrors the existing GenericDialog workflows:
#   make_mvr_dataset.py -> Transform & register beads
#   make_mvr_dataset.py -> Transform & register data
#   define_bounding_box.py -> batch / use existing box
#   get_deskewed_dopm_volumes.py -> batch fused (all XMLs in folder)
#   get_fused_MIPs.py -> search root for dataset folders / fused
#
# Input layout:
#   demo_sample_data/
#       v1/    bead data without well suffix
#       v2/    bead data with __WellC2 suffix
#       data/  sample data containing one or more Well... groups
#
# The original demo data are never modified.

from __future__ import print_function

import os
import sys
import shutil
import traceback
import xml.etree.ElementTree as ET

from java.lang import System
from ij import IJ
from ij.io import DirectoryChooser, FileSaver, Opener
from fiji.util.gui import GenericDialogPlus
from loci.formats import ImageReader, MetadataTools
from net.haesleinhuepf.clij2 import CLIJ2


PATTERN = "spim_Time{tttt}_Tile{xxxx}_angle{a}"
EXTENSION = ".nd2"
RESULTS = []
FAILURES = []


def sep():
    print("=" * 80)


def record(status, name, detail=""):
    RESULTS.append((status, name, detail))
    text = "[" + status + "] " + name
    if detail:
        text += " - " + str(detail)
    print(text)


def fail(name, exc):
    detail = exc.__class__.__name__ + ": " + str(exc)
    FAILURES.append((name, detail))
    record("FAIL", name, detail)
    traceback.print_exc()
    print("")


def get_fiji_dir():
    value = System.getProperty("fiji.dir")
    if value is None:
        raise RuntimeError("Java property fiji.dir is not set")
    return os.path.abspath(str(value))


def clear_module(name):
    if name in sys.modules:
        del sys.modules[name]


def import_production_workflows():
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

    return dopm_dir, dopmmvr, make_mvr_dataset, define_bounding_box, get_deskewed_dopm_volumes


def list_nd2(folder):
    out = []
    for name in os.listdir(folder):
        if name.lower().endswith(".nd2"):
            out.append(name)
    out.sort()
    return out


def ensure_clean_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)


def copy_nd2_folder(src, dst):
    if not os.path.isdir(dst):
        os.makedirs(dst)
    count = 0
    for name in list_nd2(src):
        shutil.copy2(os.path.join(src, name), os.path.join(dst, name))
        count += 1
    return count


def read_pixel_size_x(nd2_path):
    reader = ImageReader()
    meta = MetadataTools.createOMEXMLMetadata()
    reader.setMetadataStore(meta)
    try:
        reader.setId(nd2_path)
        size = meta.getPixelsPhysicalSizeX(0)
        if size is None:
            return None
        return float(size.value())
    finally:
        try:
            reader.close()
        except Exception:
            pass


def infer_angle_from_filenames(folder):
    angles = []
    for name in list_nd2(folder):
        stem = os.path.splitext(name)[0]
        token = "_angle"
        idx = stem.find(token)
        if idx < 0:
            continue
        rest = stem[idx + len(token):]
        digits = ""
        for ch in rest:
            if ch.isdigit() or ch == '.' or ch == '-':
                digits += ch
            else:
                break
        if digits:
            angles.append(float(digits))
    angles = sorted(list(set(angles)))
    if len(angles) != 2 or abs(angles[0]) > 1e-9:
        raise RuntimeError("Expected two bead angles beginning at 0; found " + str(angles))
    return angles[1] / 4.0


def get_test_options(demo_root):
    v1_files = list_nd2(os.path.join(demo_root, "v1"))
    if len(v1_files) == 0:
        raise RuntimeError("No ND2 files found in v1")

    inferred_pixel = read_pixel_size_x(os.path.join(demo_root, "v1", v1_files[0]))
    if inferred_pixel is None:
        inferred_pixel = 0.0
    inferred_angle = infer_angle_from_filenames(os.path.join(demo_root, "v1"))

    gui = GenericDialogPlus("Faithful dOPM workflow test options")
    gui.addMessage("These are the same acquisition values requested by make_mvr_dataset.py")
    gui.addNumericField("pixel size (um)", inferred_pixel, 6)
    gui.addNumericField("prism angle (degrees)", inferred_angle, 2)
    gui.addChoice("fusion binning", ["1", "2", "4", "8", "16"], "4")
    gui.showDialog()

    if not gui.wasOKed():
        return None

    pixel = gui.getNextNumber()
    angle = gui.getNextNumber()
    binning = gui.getNextChoice()

    if pixel <= 0:
        raise ValueError("Pixel size must be greater than zero")
    if angle <= 0:
        raise ValueError("Prism angle must be greater than zero")

    return pixel, angle, binning


def affine_texts(view_registration):
    out = []
    for child in list(view_registration):
        affine = child.find("affine")
        if affine is not None and affine.text is not None:
            out.append(" ".join(affine.text.split()))
    return out


def registration_snapshot(xml_path):
    root = ET.parse(xml_path).getroot()
    snap = {}
    for vr in root.findall("./ViewRegistrations/ViewRegistration"):
        tp = vr.get("timepoint")
        setup = vr.get("setup")
        if setup is None:
            setup = vr.get("setupid")
        snap[(str(tp), str(setup))] = affine_texts(vr)
    return snap


def parse_affine(text):
    return [float(x) for x in text.replace(",", " ").split()]


def is_identity_affine(text, tol=1e-6):
    expected = [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0]
    vals = parse_affine(text)
    if len(vals) != 12:
        return False
    for i in range(12):
        if abs(vals[i] - expected[i]) > tol:
            return False
    return True


def validate_geometry_snapshot(snap):
    if len(snap) == 0:
        raise RuntimeError("No ViewRegistrations found after geometric transformation")

    counts = []
    non_identity = 0
    for key in snap:
        vals = snap[key]
        counts.append(len(vals))
        for text in vals:
            if not is_identity_affine(text):
                non_identity += 1

    if non_identity == 0:
        raise RuntimeError("Geometric transform stage left every affine at identity")

    if min(counts) < 4:
        raise RuntimeError("Unexpectedly short dOPM geometry transform stack: " + str(counts))

    return "views=" + str(len(snap)) + "; transforms/view=" + str(counts)


def validate_registration_changed(before, after):
    changed_views = 0
    non_identity_new_or_changed = 0

    for key in after:
        before_stack = before.get(key, [])
        after_stack = after[key]
        if before_stack != after_stack:
            changed_views += 1

            # Registration usually changes/appends one or more transforms. Count
            # any affine in the post-registration stack that is not present at
            # the same position in the geometry-only stack and is non-identity.
            for i in range(len(after_stack)):
                previous = None
                if i < len(before_stack):
                    previous = before_stack[i]
                if previous != after_stack[i] and not is_identity_affine(after_stack[i]):
                    non_identity_new_or_changed += 1

    if changed_views == 0:
        raise RuntimeError("Bead registration did not change any ViewRegistration stack")

    if non_identity_new_or_changed == 0:
        raise RuntimeError(
            "Bead registration changed XML structure but produced no non-identity registration correction"
        )

    return "changed views=" + str(changed_views) + "; non-identity registration changes=" + str(non_identity_new_or_changed)


def read_setup_map(xml_path):
    root = ET.parse(xml_path).getroot()
    result = {}
    for setup in root.findall("./SequenceDescription/ViewSetups/ViewSetup"):
        sid_node = setup.find("id")
        if sid_node is None or sid_node.text is None:
            continue
        sid = str(int(sid_node.text))
        attrs = setup.find("attributes")
        if attrs is None:
            continue
        channel = attrs.find("channel")
        angle = attrs.find("angle")
        tile = attrs.find("tile")
        result[sid] = {
            "channel": None if channel is None else str(int(channel.text)),
            "angle": None if angle is None else str(int(angle.text)),
            "tile": None if tile is None else str(int(tile.text))
        }
    return result


def find_viewreg(root, timepoint, setup_id):
    for vr in root.findall("./ViewRegistrations/ViewRegistration"):
        tp = vr.get("timepoint")
        sid = vr.get("setup")
        if sid is None:
            sid = vr.get("setupid")
        if str(tp) == str(timepoint) and str(int(sid)) == str(int(setup_id)):
            return vr
    return None


def source_registration_map(bead_xml, source_timepoint="0", source_tile="0"):
    root = ET.parse(bead_xml).getroot()
    setup_map = read_setup_map(bead_xml)
    out = {}
    for sid in setup_map:
        meta = setup_map[sid]
        if meta["tile"] != str(int(source_tile)):
            continue
        vr = find_viewreg(root, source_timepoint, sid)
        if vr is None:
            continue
        out[(meta["channel"], meta["angle"])] = affine_texts(vr)
    return out


def validate_sample_matches_bead(sample_xml, bead_xml):
    source = source_registration_map(bead_xml, "0", "0")
    if len(source) == 0:
        raise RuntimeError("No bead registration source map could be built")

    root = ET.parse(sample_xml).getroot()
    setup_map = read_setup_map(sample_xml)
    checked = 0

    for vr in root.findall("./ViewRegistrations/ViewRegistration"):
        sid = vr.get("setup")
        if sid is None:
            sid = vr.get("setupid")
        sid = str(int(sid))
        if sid not in setup_map:
            continue
        meta = setup_map[sid]
        key = (meta["channel"], meta["angle"])
        if key not in source:
            raise RuntimeError("Sample channel/angle has no bead source transform: " + str(key))
        if affine_texts(vr) != source[key]:
            raise RuntimeError("Sample transform stack does not exactly match bead source for " + str(key))
        checked += 1

    if checked == 0:
        raise RuntimeError("No sample ViewRegistrations were checked")
    return checked


def get_xml_bounding_box(xml_path):
    root = ET.parse(xml_path).getroot()
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


def bb_equal(a, b, tol=1e-6):
    if a is None or b is None:
        return False
    for i in range(2):
        if len(a[i]) != len(b[i]):
            return False
        for j in range(len(a[i])):
            if abs(float(a[i][j]) - float(b[i][j])) > tol:
                return False
    return True


def find_dataset_xmls(folder):
    out = []
    for name in os.listdir(folder):
        if name.startswith("dataset") and name.lower().endswith(".xml"):
            full = os.path.join(folder, name)
            if os.path.isfile(full):
                out.append(name)
    out.sort()
    return out


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


def get_stack_list(stackdir):
    out = []
    for name in os.listdir(stackdir):
        low = name.lower()
        if low.endswith(".tif") or low.endswith(".tiff"):
            out.append(os.path.join(stackdir, name))
    out.sort()
    return out


def get_mips_on_folder(datapath):
    # Same processing logic as get_fused_MIPs.py::getMIPsonFolder.
    mip_dir = os.path.join(datapath, "MIP")
    if not os.path.isdir(mip_dir):
        os.makedirs(mip_dir)

    tiffs = get_stack_list(datapath)
    if len(tiffs) == 0:
        raise RuntimeError("No TIFF stacks found in: " + datapath)

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
    for each in os.listdir(root_folder):
        dataset_dir = os.path.join(root_folder, each)
        if not os.path.isdir(dataset_dir) or not each.startswith("dataset"):
            continue
        candidate = os.path.join(dataset_dir, each + suffix)
        if os.path.isdir(candidate):
            matches.append(candidate)
    matches.sort()
    return matches


def run_mip_root_mode(root_folder, binning):
    folders = find_dataset_output_folders(root_folder, binning)
    if len(folders) == 0:
        raise RuntimeError("No fused dataset output folders found under: " + root_folder)
    result = {}
    for folder in folders:
        result[folder] = get_mips_on_folder(folder)
    return result


def build_bead_setup(dopmmvr, make_workflow, bead_folder, pixel, angle):
    bead_suffix, bead_tail = make_workflow.get_single_bead_well_info(bead_folder, EXTENSION)
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


def run_bead_dialog_workflow(dopmmvr, make_workflow, bead_folder, pixel, angle):
    # This is make_mvr_dataset.py::process_beads in the same order, with
    # validation snapshots inserted between its production calls.
    beads = build_bead_setup(dopmmvr, make_workflow, bead_folder, pixel, angle)
    if not beads.dims:
        raise RuntimeError("No valid bead files matched the expected pattern")

    IJ.log("[FAITHFUL TEST] createXMLdataset")
    beads.createXMLdataset()
    bead_xml = os.path.join(bead_folder, beads.dataset)

    IJ.log("[FAITHFUL TEST] ApplyCalibrationFromXML")
    beads.ApplyCalibrationFromXML()

    IJ.log("[FAITHFUL TEST] transformXMLdataset")
    beads.transformXMLdataset()
    geometry = registration_snapshot(bead_xml)
    geometry_detail = validate_geometry_snapshot(geometry)

    IJ.log("[FAITHFUL TEST] RegisterDataset")
    beads.RegisterDataset()
    registered = registration_snapshot(bead_xml)
    registration_detail = validate_registration_changed(geometry, registered)

    IJ.log("[FAITHFUL TEST] ResaveXMLtoHDF5")
    beads.ResaveXMLtoHDF5(bead_folder)
    hdf5_xml = os.path.join(bead_folder, "hdf5", beads.dataset)
    if not os.path.isfile(hdf5_xml):
        raise RuntimeError("HDF5 XML was not created: " + hdf5_xml)

    # The resaved HDF5 XML should preserve the current registered transform stacks.
    hdf5_registered = registration_snapshot(hdf5_xml)
    if hdf5_registered != registered:
        raise RuntimeError("HDF5 resave did not preserve the registered ViewRegistration stacks")

    IJ.log("[FAITHFUL TEST] OptimalBoundingBox -> define -> modify")
    bbox = dopmmvr.defineboundingbox(
        dataset=beads.dataset,
        rawzplanes=beads.dims[2],
        prismangle=angle
    )
    bb = bbox.OptimalBoundingBox(bead_folder)
    bbox.defineBoundingBoxNoInteraction(bead_folder)
    bbox.modifyBoundingBox(bead_folder, bb)

    stored_bb = get_xml_bounding_box(bead_xml)
    if not bb_equal(stored_bb, bb):
        raise RuntimeError("Stored bead bounding box does not match OptimalBoundingBox result")

    return {
        "object": beads,
        "root_xml": bead_xml,
        "hdf5_xml": hdf5_xml,
        "bounding_box": stored_bb,
        "geometry_detail": geometry_detail,
        "registration_detail": registration_detail
    }


def run_sample_dialog_workflow(make_workflow, bead_source_xml, sample_folder, pixel, angle):
    # This calls the production function used by the "Transform & register data"
    # GenericDialog path. It discovers all well groups itself.
    make_workflow.process_data_with_beads(
        bead_source_xml,
        sample_folder,
        EXTENSION,
        PATTERN,
        pixel,
        angle
    )
    xmls = find_dataset_xmls(sample_folder)
    if len(xmls) == 0:
        raise RuntimeError("Production sample workflow created no dataset XMLs")
    return xmls


def count_tiffs(folder):
    n = 0
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            low = name.lower()
            if low.endswith(".tif") or low.endswith(".tiff"):
                n += 1
    return n


def run_case(label, source_root, output_root, pixel, angle, binning,
             dopmmvr, make_workflow, bb_workflow, volume_workflow):
    case_root = os.path.join(output_root, label + "_registration_case")
    bead_folder = os.path.join(case_root, "beads")
    sample_folder = os.path.join(case_root, "data")
    export_root = os.path.join(case_root, "output")

    ensure_clean_dir(case_root)
    os.makedirs(bead_folder)
    os.makedirs(sample_folder)
    os.makedirs(export_root)

    bead_n = copy_nd2_folder(os.path.join(source_root, label), bead_folder)
    sample_n = copy_nd2_folder(os.path.join(source_root, "data"), sample_folder)
    if bead_n == 0 or sample_n == 0:
        raise RuntimeError("Input copy failed")

    bead = run_bead_dialog_workflow(dopmmvr, make_workflow, bead_folder, pixel, angle)

    # The GenericDialog asks for an "Optimised bead/reference dataset XML".
    # For this automatic test, use the freshly resaved HDF5 XML because that is
    # the post-registration dataset intended for BigStitcher inspection/editing.
    bead_source_xml = bead["hdf5_xml"]

    sample_xml_names = run_sample_dialog_workflow(
        make_workflow, bead_source_xml, sample_folder, pixel, angle
    )

    transfer_counts = {}
    for name in sample_xml_names:
        sample_xml = os.path.join(sample_folder, name)
        transfer_counts[name] = validate_sample_matches_bead(sample_xml, bead_source_xml)

    # Mirror define_bounding_box.py GenericDialog choice:
    #   batch apply to all xmls in folder -> use existing box
    bb_workflow.batch_apply_existing_bb(bead["root_xml"], sample_folder)
    for name in sample_xml_names:
        sample_bb = get_xml_bounding_box(os.path.join(sample_folder, name))
        if not bb_equal(sample_bb, bead["bounding_box"]):
            raise RuntimeError("Common bead bounding box was not copied exactly to " + name)

    # Mirror get_deskewed_dopm_volumes.py GenericDialog choice:
    #   batch fused (all xmls in folder), bounding box=yes.
    dopmmvr.mvrgetvolumes.BB = "My Bounding Box"
    volume_workflow.run_batch_for_all_xmls(
        sample_folder,
        export_root,
        str(binning),
        mode="fused"
    )

    # Mirror get_fused_MIPs.py GenericDialog choice:
    #   search root for dataset folders, volume=fused, requested binning.
    mip_results = run_mip_root_mode(export_root, binning)

    outputs = {}
    for name in sample_xml_names:
        stem = os.path.splitext(name)[0]
        fused_dir = os.path.join(export_root, stem, stem + "_fused_binning_" + str(binning))
        mip_dir = os.path.join(fused_dir, "MIP")
        fused_n = count_tiffs(fused_dir)
        mip_n = count_tiffs(mip_dir)
        if fused_n == 0:
            raise RuntimeError("No fused TIFFs created for " + name)
        if mip_n != fused_n:
            raise RuntimeError(
                "MIP count does not match fused TIFF count for " + name +
                ": fused=" + str(fused_n) + ", MIP=" + str(mip_n)
            )
        outputs[name] = (fused_n, mip_n)

    return {
        "label": label,
        "bead_root_xml": bead["root_xml"],
        "bead_hdf5_xml": bead["hdf5_xml"],
        "bounding_box": bead["bounding_box"],
        "geometry_detail": bead["geometry_detail"],
        "registration_detail": bead["registration_detail"],
        "sample_xmls": sample_xml_names,
        "transfer_counts": transfer_counts,
        "outputs": outputs,
        "output_root": export_root
    }


def write_report(path, pixel, angle, binning, case_results):
    f = open(path, "w")
    try:
        f.write("dOPM Faithful End-to-End Validation Test\n")
        f.write("=" * 80 + "\n")
        f.write("pixel size (um): " + str(pixel) + "\n")
        f.write("prism angle (deg): " + str(angle) + "\n")
        f.write("fusion binning: " + str(binning) + "\n\n")

        for status, name, detail in RESULTS:
            f.write("[" + status + "] " + name)
            if detail:
                f.write(" - " + str(detail))
            f.write("\n")

        f.write("\n")
        for result in case_results:
            f.write("CASE: " + result["label"] + "\n")
            f.write("  bead root XML: " + result["bead_root_xml"] + "\n")
            f.write("  bead HDF5 XML used for registration transfer: " + result["bead_hdf5_xml"] + "\n")
            f.write("  geometry validation: " + result["geometry_detail"] + "\n")
            f.write("  registration validation: " + result["registration_detail"] + "\n")
            f.write("  common bounding box: " + str(result["bounding_box"]) + "\n")
            for name in result["sample_xmls"]:
                counts = result["outputs"][name]
                f.write("  " + name + ": copied registrations=" + str(result["transfer_counts"][name]))
                f.write(", fused TIFFs=" + str(counts[0]) + ", MIPs=" + str(counts[1]) + "\n")
            f.write("\n")

        if len(FAILURES) == 0 and len(case_results) == 2:
            f.write("RESULT: PASS\n")
        else:
            f.write("RESULT: FAIL\n")
    finally:
        f.close()


sep()
print("dOPM Faithful End-to-End Validation Test")
sep()
print("This test follows the existing Jython GenericDialog workflows and production")
print("functions rather than reconstructing a parallel workflow.")
print("")
print("It copies v1/v2/data into an isolated test area; originals are untouched.")
print("")

chooser = DirectoryChooser("Choose demo_sample_data root (contains data, v1, v2)")
DEMO_ROOT = chooser.getDirectory()

if DEMO_ROOT is None:
    print("Cancelled.")
else:
    DEMO_ROOT = os.path.abspath(DEMO_ROOT)

    required = [os.path.join(DEMO_ROOT, "v1"), os.path.join(DEMO_ROOT, "v2"), os.path.join(DEMO_ROOT, "data")]
    for folder in required:
        if not os.path.isdir(folder):
            raise RuntimeError("Required folder not found: " + folder)

    options = get_test_options(DEMO_ROOT)
    if options is None:
        print("Cancelled.")
    else:
        PIXEL, ANGLE, BINNING = options
        OUTPUT_ROOT = os.path.join(DEMO_ROOT, "_dopm_faithful_end_to_end_test")
        REPORT_PATH = os.path.join(OUTPUT_ROOT, "dOPM_faithful_end_to_end_report.txt")

        if os.path.isdir(OUTPUT_ROOT):
            shutil.rmtree(OUTPUT_ROOT)
        os.makedirs(OUTPUT_ROOT)

        case_results = []

        try:
            dopm_dir, dopmmvr, make_workflow, bb_workflow, volume_workflow = import_production_workflows()
            record("PASS", "Import production dOPM workflows", dopm_dir)
        except Exception as exc:
            fail("Import production dOPM workflows", exc)
            dopmmvr = None

        if dopmmvr is not None:
            for case_name in ["v1", "v2"]:
                print("")
                sep()
                print("Running faithful workflow case: " + case_name)
                sep()
                try:
                    result = run_case(
                        case_name,
                        DEMO_ROOT,
                        OUTPUT_ROOT,
                        PIXEL,
                        ANGLE,
                        BINNING,
                        dopmmvr,
                        make_workflow,
                        bb_workflow,
                        volume_workflow
                    )
                    case_results.append(result)
                    details = [result["geometry_detail"], result["registration_detail"], "BB=" + str(result["bounding_box"])]
                    for name in result["sample_xmls"]:
                        counts = result["outputs"][name]
                        details.append(name + ": " + str(counts[0]) + " fused / " + str(counts[1]) + " MIPs")
                    record("PASS", "Faithful end-to-end " + case_name, "; ".join(details))
                except Exception as exc:
                    fail("Faithful end-to-end " + case_name, exc)

        write_report(REPORT_PATH, PIXEL, ANGLE, BINNING, case_results)

        print("")
        sep()
        if len(FAILURES) == 0 and len(case_results) == 2:
            print("PASS")
            print("")
            print("Both filename-pattern cases passed the strict, production-order workflow.")
        else:
            print("FAIL")
            print("")
            print(str(len(FAILURES)) + " required case(s) failed.")
            print("A registration-quality failure is intentional: the test will not call")
            print("identity/no-correspondence bead registration a successful end-to-end run.")

        print("")
        print("Test output:")
        print(OUTPUT_ROOT)
        print("")
        print("Report:")
        print(REPORT_PATH)
        sep()
