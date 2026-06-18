# Utility functions for dOPM launcher scripts.
# Jython/ImageJ compatible: avoid Python 3-only syntax.

from ij import IJ
from java.lang.System import getProperty
from sys import path
from os.path import isfile
import os
import csv
import re
import time
from xml.etree import ElementTree as ET

code_path = getProperty('fiji.dir') + '/plugins/Scripts/dOPM'
if code_path not in path:
    path.append(code_path)

# Remove compiled Jython cache so edits to dopmmvr.py are picked up.
ScriptPath = code_path + "/dopmmvr$py.class"
if isfile(ScriptPath):
    os.remove(ScriptPath)

from dopmmvr import mvrsetup, defineboundingbox, mvrgetvolumes

DEFAULT_FILE_PATTERN = "spim_Time{tttt}_Tile{xxxx}_angle{a}"
DEFAULT_BB_NAME = "My Bounding Box"
MANIFEST_NAME = "dopm_run_manifest.csv"


def normpath(p):
    if p is None:
        return None
    return os.path.normpath(str(p))


def safe_makedirs(folder):
    if folder is None or str(folder).strip() == "":
        return
    if not os.path.exists(folder):
        os.makedirs(folder)


def normalize_extension(extension):
    ext = str(extension).strip()
    if ext == "":
        raise ValueError("Image file extension is empty.")
    if not ext.startswith('.'):
        ext = '.' + ext
    return ext.lower()


def normalize_angle(angle_value):
    if angle_value is None:
        return None
    txt = str(angle_value).strip()
    if txt == "":
        return None
    return str(int(float(txt)))


def expected_second_angle(prism_angle):
    return str(int(round(4 * float(prism_angle))))


def well_name_from_tail(tail):
    if tail is None or str(tail).strip() == "":
        return "no_well"
    return str(tail).lstrip('_')


def well_suffix_from_tail(tail):
    if tail is None or str(tail).strip() == "":
        return None
    return str(tail).lstrip('_')


def make_dataset_basename(well_suffix, angle_suffix=None, suffix=None):
    if well_suffix is None:
        root = "dataset"
    else:
        root = "dataset_" + str(well_suffix)

    if angle_suffix is not None and str(angle_suffix).strip() != "":
        root = root + "_angle" + str(int(float(angle_suffix)))

    if suffix is not None and str(suffix).strip() != "":
        root = root + "_" + str(suffix).strip()

    return root


def split_dataset_path(xmlpath):
    xmlpath = normpath(xmlpath)
    datapath = os.path.dirname(xmlpath)
    dataset = os.path.basename(xmlpath)
    if dataset == "":
        raise ValueError("Please select a dataset XML file, not just a folder.")
    if not dataset.lower().endswith('.xml'):
        raise ValueError("Selected file is not an XML dataset: " + str(xmlpath))
    if not os.path.exists(xmlpath):
        raise ValueError("Selected dataset XML does not exist: " + str(xmlpath))
    return datapath, dataset


def parse_raw_files(datapath, extension):
    datapath = normpath(datapath)
    extension = normalize_extension(extension)
    rows = []
    if not os.path.isdir(datapath):
        raise ValueError("Input folder does not exist: " + str(datapath))

    for each in os.listdir(datapath):
        if not each.startswith('spim'):
            continue
        if not each.lower().endswith(extension):
            continue
        parsed = mvrsetup.parse_spim_filename_static(each)
        if parsed['time'] is None or parsed['tile'] is None or parsed['angle'] is None:
            continue
        tail = parsed['well_tail']
        if tail == '':
            tail = None
        rows.append({
            'file': each,
            'time': parsed['time'],
            'tile': parsed['tile'],
            'angle': parsed['angle'],
            'channel': parsed['channel'],
            'well': parsed['well'],
            'well_tail': tail,
            'well_suffix': well_suffix_from_tail(tail)
        })
    rows.sort(key=lambda r: r['file'])
    return rows


def unique_sorted_numeric(values):
    out = []
    for v in values:
        if v is None:
            continue
        s = str(int(v))
        if s not in out:
            out.append(s)
    out.sort(key=lambda x: int(x))
    return out


def unique_sorted_text(values):
    out = []
    for v in values:
        if v not in out:
            out.append(v)
    def key(x):
        if x is None:
            return ""
        return str(x)
    out.sort(key=key)
    return out


def detect_dataset_summary(datapath, extension):
    rows = parse_raw_files(datapath, extension)
    wells = unique_sorted_text([r['well_tail'] for r in rows])
    times = unique_sorted_numeric([r['time'] for r in rows])
    tiles = unique_sorted_numeric([r['tile'] for r in rows])
    angles = unique_sorted_numeric([r['angle'] for r in rows])
    channels = unique_sorted_numeric([r['channel'] for r in rows if r['channel'] is not None])
    return {
        'rows': rows,
        'wells': wells,
        'times': times,
        'tiles': tiles,
        'angles': angles,
        'channels': channels
    }


def format_well_list(wells):
    labels = []
    for tail in wells:
        if tail is None:
            labels.append("no well suffix")
        else:
            labels.append(well_suffix_from_tail(tail))
    return ', '.join(labels)


def parse_well_selection(selection, detected_well_tails):
    """
    selection accepts:
        all
        no_well / none / blank-no-well
        WellF5,WellG5
        F5,G5
    Returns a list of well_tail values such as None or '__WellF5'.
    """
    txt = str(selection).strip()
    if txt == "" or txt.lower() == "all":
        return detected_well_tails

    tokens = [t.strip() for t in txt.split(',') if t.strip() != ""]
    out = []
    detected_map = {}
    for tail in detected_well_tails:
        suffix = well_suffix_from_tail(tail)
        if suffix is None:
            detected_map['no_well'] = tail
            detected_map['none'] = tail
        else:
            detected_map[suffix.lower()] = tail
            if suffix.lower().startswith('well'):
                detected_map[suffix[4:].lower()] = tail

    for token in tokens:
        key = token.lower()
        if key.startswith('__'):
            key2 = well_suffix_from_tail(key).lower()
        else:
            key2 = key
        if key2 not in detected_map:
            raise ValueError(
                "Requested well '" + token + "' was not detected. Detected wells: " +
                format_well_list(detected_well_tails)
            )
        tail = detected_map[key2]
        if tail not in out:
            out.append(tail)
    return out


def filter_rows_for_well_angle(rows, well_tail, target_angle):
    out = []
    for r in rows:
        if r['well_tail'] != well_tail:
            continue
        if target_angle is not None and str(r['angle']) != str(target_angle):
            continue
        out.append(r)
    return out


def validate_complete_combinations(rows, mode_name):
    """
    Warns if time/tile/angle combinations are incomplete. Returns warning list.
    """
    warnings = []
    times = unique_sorted_numeric([r['time'] for r in rows])
    tiles = unique_sorted_numeric([r['tile'] for r in rows])
    angles = unique_sorted_numeric([r['angle'] for r in rows])
    present = {}
    for r in rows:
        present[(str(r['time']), str(r['tile']), str(r['angle']))] = 1
    missing = []
    for t in times:
        for tile in tiles:
            for a in angles:
                if (t, tile, a) not in present:
                    missing.append("Time" + t + "/Tile" + tile + "/angle" + a)
    if len(missing) > 0:
        warnings.append(mode_name + ": missing combinations: " + ', '.join(missing[:20]))
        if len(missing) > 20:
            warnings.append(mode_name + ": plus " + str(len(missing) - 20) + " more missing combinations")
    return warnings


def log_summary(summary):
    IJ.log("Detected raw dataset summary")
    IJ.log("  Files: " + str(len(summary['rows'])))
    IJ.log("  Wells: " + format_well_list(summary['wells']))
    IJ.log("  Timepoints: " + ','.join(summary['times']))
    IJ.log("  Tiles: " + ','.join(summary['tiles']))
    IJ.log("  Angles: " + ','.join(summary['angles']))
    if len(summary['channels']) > 0:
        IJ.log("  Channel file tokens: " + ','.join(summary['channels']))


def xml_has_bounding_box(xmlpath, name=DEFAULT_BB_NAME):
    if not os.path.exists(xmlpath):
        return False
    root = ET.parse(xmlpath).getroot()
    bb_root = root.find('./BoundingBoxes')
    if bb_root is None:
        return False
    for boundingbox in bb_root:
        if boundingbox.get('name') == name:
            return True
    return False


def xml_view_angles(xmlpath):
    if not os.path.exists(xmlpath):
        raise IOError("Dataset XML not found: " + str(xmlpath))
    root = ET.parse(xmlpath).getroot()
    angles = []
    for node in root.findall('./SequenceDescription/ViewSetups/Attributes/Angle'):
        name_node = node.find('name')
        if name_node is not None and name_node.text is not None:
            angles.append(name_node.text)
    return angles


def xml_has_view_registrations(xmlpath):
    if not os.path.exists(xmlpath):
        return False
    root = ET.parse(xmlpath).getroot()
    nodes = root.findall('./ViewRegistrations/ViewRegistration')
    return len(nodes) > 0


def wait_for_file(path_, timeout_seconds=2.0):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        if os.path.exists(path_):
            return True
        time.sleep(0.1)
    return os.path.exists(path_)


def verify_file_exists(path_, label):
    if not wait_for_file(path_):
        raise IOError(label + " was not created or cannot be found: " + str(path_))
    IJ.log("Verified " + label + ": " + str(path_))


def verify_xml_ready(xmlpath, label):
    verify_file_exists(xmlpath, label)
    if not xml_has_view_registrations(xmlpath):
        raise ValueError(label + " exists but does not contain ViewRegistrations: " + str(xmlpath))
    IJ.log("Verified XML has ViewRegistrations: " + str(xmlpath))


def create_mvr_object(datapath, extension, filepattern, pixel, prism_angle,
                      well_tail, view_mode, target_angle=None,
                      bead_xml=None, dataset_suffix=None):
    well_suffix = well_suffix_from_tail(well_tail)
    if view_mode == 'single_view':
        root = make_dataset_basename(well_suffix, target_angle, dataset_suffix)
    else:
        root = make_dataset_basename(well_suffix, None, dataset_suffix)

    regpath = r''
    if bead_xml is not None and str(bead_xml).strip() != "":
        regpath = os.path.dirname(normpath(bead_xml))

    return mvrsetup(
        datapath=normpath(datapath),
        regpath=regpath,
        filepattern=filepattern,
        extension=normalize_extension(extension),
        px=float(pixel),
        py=float(pixel),
        angle=float(prism_angle),
        well_suffix=well_suffix,
        well_tail=well_tail,
        dataset_basename=root,
        registration_source_xml=bead_xml,
        view_mode=view_mode,
        target_angle=target_angle
    )


def create_dataset_for_well(datapath, extension, filepattern, pixel, prism_angle,
                            well_tail, view_mode, target_angle=None,
                            registration_mode='none', bead_xml=None,
                            dataset_suffix=None):
    target_angle = normalize_angle(target_angle)
    obj = create_mvr_object(
        datapath, extension, filepattern, pixel, prism_angle,
        well_tail, view_mode, target_angle=target_angle,
        bead_xml=bead_xml, dataset_suffix=dataset_suffix
    )

    if not obj.dims:
        raise ValueError("No valid files matched for well " + well_name_from_tail(well_tail))

    IJ.log("Creating dataset: " + obj.dataset)
    obj.createXMLdataset()
    xmlpath = os.path.join(normpath(datapath), obj.dataset)
    verify_xml_ready(xmlpath, "created dataset XML")

    IJ.log("Applying calibration from XML: " + obj.dataset)
    obj.ApplyCalibrationFromXML()
    verify_xml_ready(xmlpath, "calibrated dataset XML")

    IJ.log("Applying dOPM geometric transforms: " + obj.dataset)
    obj.transformXMLdataset()
    verify_xml_ready(xmlpath, "transformed dataset XML")

    if registration_mode == 'copy_bead_xml':
        if bead_xml is None or str(bead_xml).strip() == "":
            raise ValueError("registration_mode=copy_bead_xml requires bead_xml")
        IJ.log("Copying bead registration into: " + obj.dataset)
        obj.CopyBeadRegistrationXMLGlobal(normpath(bead_xml), source_timepoint="0", source_tile="0")
        verify_xml_ready(xmlpath, "registered sample XML")
    elif registration_mode == 'register_beads':
        IJ.log("Registering bead dataset: " + obj.dataset)
        obj.RegisterDataset()
        verify_xml_ready(xmlpath, "registered bead XML")
    elif registration_mode == 'none':
        pass
    else:
        raise ValueError("Unknown registration_mode: " + str(registration_mode))

    return {
        'well_tail': well_tail,
        'well': well_name_from_tail(well_tail),
        'view_mode': view_mode,
        'angle': target_angle,
        'xml_path': xmlpath,
        'dataset': obj.dataset,
        'datapath': normpath(datapath),
        'raw_z_planes': obj.dims[2]
    }


def write_manifest(manifest_path, rows):
    manifest_path = normpath(manifest_path)
    safe_makedirs(os.path.dirname(manifest_path))
    fields = ['well', 'well_tail', 'view_mode', 'angle', 'xml_path', 'dataset', 'datapath', 'raw_z_planes', 'bounding_box', 'export_mode', 'export_path']
    f = open(manifest_path, 'wb')
    try:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = {}
            for field in fields:
                out[field] = row.get(field, '')
            writer.writerow(out)
    finally:
        f.close()
    IJ.log("Wrote manifest: " + manifest_path)


def read_manifest(manifest_path):
    manifest_path = normpath(manifest_path)
    if not os.path.exists(manifest_path):
        raise IOError("Manifest not found: " + str(manifest_path))
    rows = []
    f = open(manifest_path, 'rb')
    try:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    finally:
        f.close()
    return rows


def find_dataset_xmls(folder, name_filter=None):
    folder = normpath(folder)
    xmls = []
    if not os.path.isdir(folder):
        raise ValueError("XML folder does not exist: " + str(folder))
    for each in os.listdir(folder):
        if not each.startswith('dataset') or not each.lower().endswith('.xml'):
            continue
        if name_filter is not None and str(name_filter).strip() != "":
            if str(name_filter).strip() not in each:
                continue
        full = os.path.join(folder, each)
        if os.path.isfile(full):
            xmls.append(full)
    xmls.sort()
    return xmls


def compute_geometry_bb_for_xml(xmlpath, rawzplanes, prism_angle):
    datapath, dataset = split_dataset_path(xmlpath)
    bb_obj = defineboundingbox(dataset=dataset, rawzplanes=float(rawzplanes), prismangle=float(prism_angle))
    BB = bb_obj.OptimalBoundingBox(datapath)
    bb_obj.defineBoundingBoxNoInteraction(datapath)
    bb_obj.modifyBoundingBox(datapath, BB)
    if not xml_has_bounding_box(xmlpath):
        raise ValueError("Bounding box was not written to XML: " + str(xmlpath))
    IJ.log("Verified bounding box in XML: " + str(xmlpath))
    return BB


def copy_bb(reference_xml, target_xml):
    ref_datapath, ref_dataset = split_dataset_path(reference_xml)
    target_datapath, target_dataset = split_dataset_path(target_xml)
    ref_bb = defineboundingbox(dataset=ref_dataset)
    BB = ref_bb.getXMLBoundingBox(ref_datapath)
    if BB is None:
        raise ValueError("Reference XML does not contain '" + DEFAULT_BB_NAME + "': " + str(reference_xml))
    target_bb = defineboundingbox(dataset=target_dataset)
    target_bb.defineBoundingBoxNoInteraction(target_datapath)
    target_bb.modifyBoundingBox(target_datapath, BB)
    if not xml_has_bounding_box(target_xml):
        raise ValueError("Bounding box was not copied to XML: " + str(target_xml))
    IJ.log("Copied bounding box to: " + str(target_xml))


def define_bb_interactive(reference_xml, target_xml):
    ref_datapath, ref_dataset = split_dataset_path(reference_xml)
    target_datapath, target_dataset = split_dataset_path(target_xml)
    ref_bb = defineboundingbox(dataset=ref_dataset)
    ref_bb.defineBoundingBox(ref_datapath)
    BB = ref_bb.getXMLBoundingBox(ref_datapath)
    if BB is None:
        raise ValueError("Interactive bounding box was not found in reference XML: " + str(reference_xml))
    target_bb = defineboundingbox(dataset=target_dataset)
    target_bb.defineBoundingBoxNoInteraction(target_datapath)
    target_bb.modifyBoundingBox(target_datapath, BB)
    if not xml_has_bounding_box(target_xml):
        raise ValueError("Bounding box was not copied to XML: " + str(target_xml))
    IJ.log("Defined/copied bounding box to: " + str(target_xml))


def apply_bounding_box(xml_rows, mode, rawzplanes, prism_angle, reference_xml=None):
    """
    mode: none, geometry_per_xml, geometry_from_reference, copy_existing, manual_reference
    """
    mode = str(mode)
    if mode == 'none':
        return xml_rows

    if len(xml_rows) == 0:
        raise ValueError("No XML rows provided for bounding-box step.")

    if mode == 'geometry_per_xml':
        for row in xml_rows:
            rz = row.get('raw_z_planes', rawzplanes)
            compute_geometry_bb_for_xml(row['xml_path'], rz, prism_angle)
            row['bounding_box'] = DEFAULT_BB_NAME
        return xml_rows

    if reference_xml is None or str(reference_xml).strip() == "":
        raise ValueError("Bounding-box mode " + mode + " requires a reference XML.")
    reference_xml = normpath(reference_xml)

    if mode == 'geometry_from_reference':
        ref_datapath, ref_dataset = split_dataset_path(reference_xml)
        ref_bb = defineboundingbox(dataset=ref_dataset, rawzplanes=float(rawzplanes), prismangle=float(prism_angle))
        BB = ref_bb.OptimalBoundingBox(ref_datapath)
        ref_bb.defineBoundingBoxNoInteraction(ref_datapath)
        ref_bb.modifyBoundingBox(ref_datapath, BB)
        for row in xml_rows:
            target_datapath, target_dataset = split_dataset_path(row['xml_path'])
            bb = defineboundingbox(dataset=target_dataset)
            bb.defineBoundingBoxNoInteraction(target_datapath)
            bb.modifyBoundingBox(target_datapath, BB)
            if not xml_has_bounding_box(row['xml_path']):
                raise ValueError("Bounding box not written to: " + str(row['xml_path']))
            row['bounding_box'] = DEFAULT_BB_NAME
        return xml_rows

    if mode == 'copy_existing':
        for row in xml_rows:
            copy_bb(reference_xml, row['xml_path'])
            row['bounding_box'] = DEFAULT_BB_NAME
        return xml_rows

    if mode == 'manual_reference':
        # Define once on the reference XML, then copy that same box to all targets.
        ref_datapath, ref_dataset = split_dataset_path(reference_xml)
        ref_bb = defineboundingbox(dataset=ref_dataset)
        ref_bb.defineBoundingBox(ref_datapath)
        BB = ref_bb.getXMLBoundingBox(ref_datapath)
        if BB is None:
            raise ValueError("Interactive bounding box was not found in reference XML: " + str(reference_xml))
        for row in xml_rows:
            target_datapath, target_dataset = split_dataset_path(row['xml_path'])
            target_bb = defineboundingbox(dataset=target_dataset)
            target_bb.defineBoundingBoxNoInteraction(target_datapath)
            target_bb.modifyBoundingBox(target_datapath, BB)
            if not xml_has_bounding_box(row['xml_path']):
                raise ValueError("Bounding box not written to: " + str(row['xml_path']))
            row['bounding_box'] = DEFAULT_BB_NAME
        return xml_rows

    raise ValueError("Unknown bounding-box mode: " + str(mode))


def angle_to_view_index(xmlpath, requested_angle):
    requested_angle = normalize_angle(requested_angle)
    angles = xml_view_angles(xmlpath)
    if requested_angle is None:
        if len(angles) == 1:
            return "0"
        raise ValueError("requested_angle is blank, but XML has multiple angles: " + str(angles))
    for idx in range(len(angles)):
        if normalize_angle(angles[idx]) == requested_angle:
            return str(idx)
    raise ValueError("Angle " + str(requested_angle) + " not found in XML " + str(xmlpath) + ". XML angles: " + str(angles))


def export_xml(xmlpath, savepath, binning, export_mode, crop, requested_angle=None):
    datapath, dataset = split_dataset_path(xmlpath)
    savepath = normpath(savepath)
    safe_makedirs(savepath)
    if crop:
        mvrgetvolumes.BB = DEFAULT_BB_NAME
        if not xml_has_bounding_box(xmlpath):
            raise ValueError("Crop requested but XML does not contain '" + DEFAULT_BB_NAME + "': " + str(xmlpath))
    else:
        mvrgetvolumes.BB = 'All Views'

    data = mvrgetvolumes(datapath=datapath, savepath=savepath, binning=str(binning), dataset=dataset)
    if export_mode == 'fused':
        data.getFusedVolumes()
    elif export_mode == 'single_angle':
        view_index = angle_to_view_index(xmlpath, requested_angle)
        IJ.log("Exporting requested angle" + str(requested_angle) + " using XML view index " + view_index)
        data.getSingleView(view_index)
    elif export_mode == 'both_single_views':
        angles = xml_view_angles(xmlpath)
        if len(angles) < 2:
            raise ValueError("Cannot export both single views from XML with fewer than two angles: " + str(xmlpath))
        data.getSingleView("0")
        data.getSingleView("1")
    else:
        raise ValueError("Unknown export mode: " + str(export_mode))

    return savepath


def export_rows(xml_rows, savepath_root, binning, export_mode, crop, requested_angle=None):
    for row in xml_rows:
        dataset_stem = os.path.splitext(os.path.basename(row['xml_path']))[0]
        xml_savepath = os.path.join(normpath(savepath_root), dataset_stem)
        safe_makedirs(xml_savepath)
        export_xml(row['xml_path'], xml_savepath, binning, export_mode, crop, requested_angle=requested_angle)
        row['export_mode'] = export_mode
        row['export_path'] = xml_savepath
    return xml_rows


def find_mip_input_folders(savepath_root, xml_rows, export_mode, binning, requested_angle=None):
    folders = []
    for row in xml_rows:
        dataset_stem = os.path.splitext(os.path.basename(row['xml_path']))[0]
        root = os.path.join(normpath(savepath_root), dataset_stem)
        if export_mode == 'fused':
            suffixes = [dataset_stem + '_fused_binning_' + str(binning)]
        elif export_mode == 'single_angle':
            # BigStitcher helper names output by view index, not physical angle.
            try:
                view_index = angle_to_view_index(row['xml_path'], requested_angle)
            except:
                view_index = "0"
            # Existing getSingleView uses view+1 in folder names.
            suffixes = [dataset_stem + '_view_' + str(int(view_index) + 1) + '_binning_' + str(binning)]
        else:
            suffixes = []
        for suffix in suffixes:
            candidate = os.path.join(root, suffix)
            if os.path.isdir(candidate):
                folders.append(candidate)
    return folders


def has_tiffs(folder):
    if not os.path.isdir(folder):
        return False
    for each in os.listdir(folder):
        low = each.lower()
        if low.endswith('.tif') or low.endswith('.tiff'):
            return True
    return False


def verify_export_outputs(savepath_root, xml_rows, export_mode, binning, requested_angle=None):
    folders = find_mip_input_folders(savepath_root, xml_rows, export_mode, binning, requested_angle=requested_angle)
    if len(folders) == 0:
        IJ.log("Warning: no expected export folders were found under: " + str(savepath_root))
        return
    for folder in folders:
        if has_tiffs(folder):
            IJ.log("Verified exported TIFF folder: " + folder)
        else:
            IJ.log("Warning: export folder contains no TIFF stacks yet: " + folder)


def _open_image_robust(path_):
    from ij.io import Opener
    imp = None
    try:
        imp = Opener().openImage(path_)
    except:
        imp = None
    if imp is None:
        try:
            imp = IJ.openImage(path_)
        except:
            imp = None
    return imp


def _list_tiff_stacks(folder):
    out = []
    for each in os.listdir(folder):
        low = each.lower()
        if low.endswith('.tif') or low.endswith('.tiff'):
            out.append(os.path.join(folder, each))
    out.sort()
    return out


def generate_mips_in_folder(folder):
    from ij.io import FileSaver
    from net.haesleinhuepf.clij2 import CLIJ2

    folder = normpath(folder)
    mip_folder = os.path.join(folder, 'MIP')
    safe_makedirs(mip_folder)
    tiffs = _list_tiff_stacks(folder)

    if len(tiffs) == 0:
        IJ.log("No TIFF stacks found for MIP generation in: " + folder)
        return

    for tiff_stack in tiffs:
        clij2 = CLIJ2.getInstance()
        imp = _open_image_robust(tiff_stack)
        if imp is None:
            IJ.log("Could not open: " + tiff_stack)
            continue
        try:
            dims = imp.getDimensions()  # x,y,c,z,t
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
            name = os.path.splitext(os.path.basename(tiff_stack))[0]
            FileSaver(final_imp).saveAsTiff(os.path.join(mip_folder, name + '.tif'))
            final_imp.close()
        finally:
            try:
                imp.close()
            except:
                pass
            clij2.clear()


def run_mips_for_export_outputs(savepath_root, xml_rows, export_mode, binning, requested_angle=None):
    folders = find_mip_input_folders(savepath_root, xml_rows, export_mode, binning, requested_angle=requested_angle)
    if len(folders) == 0:
        IJ.log("No export folders found for MIP generation.")
        return
    for folder in folders:
        IJ.log("Generating MIPs in: " + folder)
        generate_mips_in_folder(folder)


def create_rows_for_selected_wells(datapath, extension, filepattern, pixel, prism_angle,
                                   selected_well_tails, dataset_mode,
                                   single_view_angle=None,
                                   registration_mode='none', bead_xml=None):
    rows = []
    if dataset_mode == 'single_view':
        view_mode = 'single_view'
        target_angle = normalize_angle(single_view_angle)
        if target_angle is None:
            raise ValueError("Single-view dataset mode requires a selected angle in launcher mode.")
    elif dataset_mode == 'two_view':
        view_mode = 'two_view'
        target_angle = None
    else:
        raise ValueError("Unknown dataset_mode: " + str(dataset_mode))

    for tail in selected_well_tails:
        row = create_dataset_for_well(
            datapath, extension, filepattern, pixel, prism_angle,
            tail, view_mode, target_angle=target_angle,
            registration_mode=registration_mode, bead_xml=bead_xml
        )
        rows.append(row)
    return rows
