#@ PrefService prefs
from fiji.util.gui import GenericDialogPlus
import os
import re
import math
import csv
import shutil

from ij import IJ
from ij.io import FileSaver
from ij.plugin import FolderOpener
from ij.plugin import HyperStackConverter

from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.formats import MetadataTools
from loci.formats import ImageReader

from array import array
from os.path import isfile
from xml.etree import ElementTree as ET
from xml.dom import minidom
from ome.units import UNITS


def readdopmxml(filename):
    tree = ET.parse(filename)

    settings = {}
    for elem in tree.iter():
        if elem.text:
            settings.update({elem.tag: elem.text})

    filterstrings = [
        'extension',
        'boundingboxmin',
        'boundingboxmax',
        'filepattern',
        'pixelsize',
        'prismangle',
        'rawzplanes'
    ]

    settings = {k: v for k, v in settings.iteritems() if k in filterstrings}

    IJ.log('settings read:')
    IJ.log(str(settings))
    return settings


def writedopmxml(filename, settings):
    data = ET.Element('dOPMconfig')
    items = ET.SubElement(data, 'parameters')

    ET.SubElement(items, 'pixelsize').text = settings.get("pixelsize")
    ET.SubElement(items, 'rawzplanes').text = settings.get("rawzplanes")
    ET.SubElement(items, 'prismangle').text = settings.get("prismangle")
    ET.SubElement(items, 'extension').text = settings.get("extension")
    ET.SubElement(items, 'filepattern').text = settings.get("filepattern")

    boundingbox = ET.SubElement(items, 'BoundingBoxes')

    if settings.get("BoundingBoxDefinition") is not None:
        bb_def = ET.SubElement(boundingbox, 'BoundingBoxDefinition')
        ET.SubElement(bb_def, 'boundingboxmin').text = settings.get("boundingboxmin")
        ET.SubElement(bb_def, 'boundingboxmax').text = settings.get("boundingboxmax")
        bb_def.set('name', "My Bounding Box")

    xmlstr = minidom.parseString(
        ET.tostring(data)
    ).toprettyxml(indent="   ", encoding='UTF-8')

    with open(filename, "w") as f:
        f.write(xmlstr)

    IJ.log('settings written:')
    IJ.log(str(settings))


class mvrsetup(object):

    def __init__(self, **kwargs):
        valid_keys = [
            "datapath",
            "regpath",
            "filepattern",
            "extension",
            "px",
            "py",
            "angle",
            "well_suffix",
            "well_tail",
            "dataset_basename",
            "bead_reference_timepoint",
            "registration_source_csv"
        ]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))

        self.regpath = self.regpath or self.datapath
        self.filepattern_ = self.filepattern
        self.well_suffix = self.well_suffix
        self.well_tail = getattr(self, 'well_tail', None)
        self.bead_reference_timepoint = self.bead_reference_timepoint
        self.registration_source_csv = getattr(self, 'registration_source_csv', None)

        if self.well_tail:
            self.filepattern = self.filepattern_ + self.well_tail + self.extension
        else:
            self.filepattern = self.filepattern_ + self.extension

        dataset_root = kwargs.get("dataset_basename")
        if dataset_root:
            self.dataset_root = dataset_root
        elif self.well_suffix:
            self.dataset_root = "dataset_" + self.well_suffix
        else:
            self.dataset_root = "dataset"

        self.dataset = self.dataset_root + ".xml"
        self.registration_csv = self.dataset_root + "_registrations.csv"
        self.calibration_csv = self.dataset_root + "_calibrations.csv"

        self.calibfile = os.path.normpath(os.path.join(self.datapath, self.calibration_csv))

        if self.registration_source_csv:
            self.regfile = os.path.normpath(self.registration_source_csv)
        else:
            self.regfile = os.path.normpath(os.path.join(self.regpath, self.registration_csv))

        self.dims = self.GetImageInfo()

    # -------------------------------------------------------------------------
    # filename parsing helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def parse_spim_filename_static(filename):
        stem = os.path.splitext(os.path.basename(filename))[0]

        info = {
            'time': None,
            'tile': None,
            'channel': None,
            'angle': None,
            'well': None,
            'well_tail': ''
        }

        parts = [p for p in re.split(r'_+', stem) if p]

        for p in parts:
            m = re.match(r'^Time(\d+)$', p)
            if m:
                info['time'] = str(int(m.group(1)))
                continue

            m = re.match(r'^Tile(\d+)$', p)
            if m:
                info['tile'] = str(int(m.group(1)))
                continue

            m = re.match(r'^channel(\d+)$', p)
            if m:
                info['channel'] = str(int(m.group(1)))
                continue

            m = re.match(r'^angle(\d+)$', p)
            if m:
                info['angle'] = str(int(m.group(1)))
                continue

            m = re.match(r'^Well.+$', p)
            if m:
                info['well'] = p
                continue

        m = re.search(r'(_+Well[^_]+)$', stem)
        if m:
            info['well_tail'] = m.group(1)

        return info

    def _parse_spim_filename(self, filename):
        return self.parse_spim_filename_static(filename)

    def _has_explicit_channel_token(self):
        return self.filepattern_.find('channel') != -1

    def list_input_files(self):
        files = []
        for each in os.listdir(self.datapath):
            if each.startswith('spim') and each.endswith(self.extension):
                parsed = self._parse_spim_filename(each)

                if parsed['time'] is None or parsed['tile'] is None or parsed['angle'] is None:
                    continue

                if self._has_explicit_channel_token() and parsed['channel'] is None:
                    continue

                parsed_tail = parsed['well_tail']
                if parsed_tail == '':
                    parsed_tail = None

                if self.well_tail is None:
                    if parsed_tail is not None:
                        continue
                else:
                    if parsed_tail != self.well_tail:
                        continue

                files.append(each)

        files.sort()
        return files

    @staticmethod
    def group_files_by_well(datapath, extension):
        groups = {}

        for each in os.listdir(datapath):
            if not each.startswith('spim') or not each.endswith(extension):
                continue

            parsed = mvrsetup.parse_spim_filename_static(each)
            well = parsed['well']

            if not groups.has_key(well):
                groups[well] = []
            groups[well].append(each)

        for key in groups:
            groups[key].sort()

        return groups

    @staticmethod
    def detect_well_suffixes(datapath, extension):
        groups = mvrsetup.group_files_by_well(datapath, extension)
        suffixes = groups.keys()

        def _sort_key(x):
            if x is None:
                return ""
            return x

        suffixes.sort(key=_sort_key)
        return suffixes

    @staticmethod
    def detect_well_tails(datapath, extension):
        tails = []

        for each in os.listdir(datapath):
            if not each.startswith('spim') or not each.endswith(extension):
                continue

            parsed = mvrsetup.parse_spim_filename_static(each)
            tail = parsed['well_tail']
            if tail == '':
                tail = None
            tails.append(tail)

        tails = list(set(tails))

        def _sort_key(x):
            if x is None:
                return ""
            return x

        tails.sort(key=_sort_key)
        return tails

    def choose_first_timepoint_from_current_files(self):
        times = []
        for each in self.list_input_files():
            parsed = self._parse_spim_filename(each)
            if parsed['time'] is not None:
                times.append(int(parsed['time']))

        if len(times) == 0:
            return None

        times = sorted(set(times))
        return str(times[0])

    # -------------------------------------------------------------------------
    # metadata / dataset setup
    # -------------------------------------------------------------------------

    def GetImageInfo(self):
        results = self.list_input_files()
        channels = []
        times = []
        tiles = []
        hyperstack = -1

        for each in results:
            parsed = self._parse_spim_filename(each)

            if parsed['time'] is None:
                raise ValueError("Could not parse time from file: " + each)
            if parsed['tile'] is None:
                raise ValueError("Could not parse tile from file: " + each)

            times.append(parsed['time'])
            tiles.append(parsed['tile'])

            if self._has_explicit_channel_token():
                if parsed['channel'] is None:
                    raise ValueError("Expected channel token in file: " + each)
                channels.append(parsed['channel'])

        T = ','.join(sorted(set(times), key=lambda x: int(x)))
        Tiles = ','.join(sorted(set(tiles), key=lambda x: int(x)))

        print results

        if len(results) == 0:
            print 'error in image format - does not match expected types'
            return []

        file = os.path.join(self.datapath, results[0])
        print file

        tiff_names = ['.tif', '.tiff']

        if any(self.extension == i for i in tiff_names):
            file = file.replace('\\', '/')
            imp = IJ.openImage(file)

            szX = imp.getCalibration().pixelWidth
            szY = imp.getCalibration().pixelHeight
            szZ = imp.getCalibration().pixelDepth
            X = imp.getWidth()
            Y = imp.getHeight()
            Z = imp.getImageStackSize()
            imp.close()

            hyperstack = 0
            print 'processing tif zstacks'

            if self._has_explicit_channel_token():
                C = ','.join(sorted(set(channels), key=lambda x: int(x)))
            else:
                C = '0'

        elif self.extension == '.nd2':
            reader = ImageReader()
            omeMeta = MetadataTools.createOMEXMLMetadata()
            reader.setMetadataStore(omeMeta)
            reader.setId(file)

            X = reader.getSizeX()
            Y = reader.getSizeY()
            Z = reader.getSizeZ()

            szX = omeMeta.getPixelsPhysicalSizeX(0).value()
            szY = omeMeta.getPixelsPhysicalSizeY(0).value()
            szZ = omeMeta.getPixelsPhysicalSizeZ(0).value()

            if reader.getSizeC() > 1 and not self._has_explicit_channel_token():
                print 'processing nd2 hyperstacks'
                hyperstack = 1
                c_list = []
                for c in range(reader.getSizeC()):
                    c_list.append(str(c))
                C = ','.join(c_list)

            elif reader.getSizeC() == 1 and self._has_explicit_channel_token():
                print 'processing nd2 zstacks'
                hyperstack = 0
                C = ','.join(sorted(set(channels), key=lambda x: int(x)))

            elif reader.getSizeC() == 1 and not self._has_explicit_channel_token():
                print 'processing nd2 single-channel files without explicit channel token'
                hyperstack = 1
                C = '0'

            else:
                reader.close()
                raise ValueError("Unsupported ND2 layout for file pattern: " + self.filepattern_)

            reader.close()

        else:
            print 'error in image format - does not match expected types'
            return []

        print [X, Y, Z, T, C, szX, szY, szZ]
        return [X, Y, Z, T, C, szX, szY, szZ, Tiles, hyperstack]

    def createXMLdataset(self):
        times = self.dims[3]
        tiles = self.dims[8]
        channels = self.dims[4]
        pz = self.dims[7]
        angles = "0-" + IJ.d2s(4 * self.angle, 0) + ":" + IJ.d2s(4 * self.angle, 0)

        px = IJ.d2s(self.px, 4)
        py = IJ.d2s(self.py, 4)
        pz = IJ.d2s(pz, 4)

        tiff_names = ['.tif', '.tiff']

        if any(self.extension == i for i in tiff_names):
            IJ.run(
                "Define Multi-View Dataset",
                "define_dataset=[Manual Loader (TIFF only, ImageJ Opener)] "
                "project_filename=[" + self.dataset + "] "
                "multiple_timepoints=[YES (one file per time-point)] "
                "multiple_channels=[YES (one file per channel)] "
                "_____multiple_illumination_directions=[NO (one illumination direction)] "
                "multiple_angles=[YES (one file per angle)] "
                "multiple_tiles=[YES (one file per tile)] "
                "image_file_directory=[" + self.datapath + "] "
                "image_file_pattern=" + self.filepattern + " "
                "timepoints_=" + times + " "
                "channels_=" + channels + " "
                "acquisition_angles_=" + angles + " "
                "tiles_=" + tiles + " "
                "calibration_type=[Same voxel-size for all views] "
                "calibration_definition=[Load voxel-size(s) from file(s) and display for verification] "
                "imglib2_data_container=[ArrayImg (faster)] "
                "pixel_distance_x=" + px + " "
                "pixel_distance_y=" + py + " "
                "pixel_distance_z=" + pz + " "
                "pixel_unit=microns"
            )
        elif self.dims[9] == 1:
            IJ.run(
                "Define Multi-View Dataset",
                "define_dataset=[Manual Loader (Bioformats based)] "
                "project_filename=[" + self.dataset + "] "
                "multiple_timepoints=[YES (one file per time-point)] "
                "multiple_channels=[YES (all channels in one file)] "
                "_____multiple_illumination_directions=[NO (one illumination direction)] "
                "multiple_angles=[YES (one file per angle)] "
                "multiple_tiles=[YES (one file per tile)] "
                "image_file_directory=[" + self.datapath + "] "
                "image_file_pattern=" + self.filepattern + " "
                "timepoints_=" + times + " "
                "channels_=" + channels + " "
                "acquisition_angles_=" + angles + " "
                "tiles_=" + tiles + " "
                "calibration_type=[Same voxel-size for all views] "
                "calibration_definition=[Load voxel-size(s) from file(s) and display for verification] "
                "imglib2_data_container=[ArrayImg (faster)] "
                "pixel_distance_x=" + px + " "
                "pixel_distance_y=" + py + " "
                "pixel_distance_z=" + pz + " "
                "pixel_unit=microns"
            )
        elif self.dims[9] == 0:
            IJ.run(
                "Define Multi-View Dataset",
                "define_dataset=[Manual Loader (Bioformats based)] "
                "project_filename=[" + self.dataset + "] "
                "multiple_timepoints=[YES (one file per time-point)] "
                "multiple_channels=[YES (one file per channel)] "
                "_____multiple_illumination_directions=[NO (one illumination direction)] "
                "multiple_angles=[YES (one file per angle)] "
                "multiple_tiles=[YES (one file per tile)] "
                "image_file_directory=[" + self.datapath + "] "
                "image_file_pattern=" + self.filepattern + " "
                "timepoints_=" + times + " "
                "channels_=" + channels + " "
                "acquisition_angles_=" + angles + " "
                "tiles_=" + tiles + " "
                "calibration_type=[Same voxel-size for all views] "
                "calibration_definition=[Load voxel-size(s) from file(s) and display for verification] "
                "imglib2_data_container=[ArrayImg (faster)] "
                "pixel_distance_x=" + px + " "
                "pixel_distance_y=" + py + " "
                "pixel_distance_z=" + pz + " "
                "pixel_unit=microns"
            )
        else:
            print 'wrong image format during createXMLdataset'

    def createFolder(self, newpath):
        try:
            if not os.path.exists(newpath):
                os.makedirs(newpath)
        except OSError:
            print ('Error: Creating directory. ' + newpath)

    def csvtoarray(self, csv_string, type_):
        values = csv_string.split(',')
        out = []
        for i in values:
            if type_ == 'int':
                out.append(int(i))
            elif type_ == 'float':
                out.append(float(i))
            elif type_ == 'string':
                out.append(str(i))
        return out

    def getCalibrations(self):
        file = os.path.join(self.datapath, self.dataset)

        root = ET.parse(file).getroot()
        affine_list = []
        spacer = 'NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN'

        for node in root.findall('./ViewRegistrations/ViewRegistration'):
            elem = None
            for i in node:
                elem = i.find('affine').text
            affine_list.append(elem)
            affine_list.append(spacer)

        savepath = os.path.normpath(os.path.join(os.path.split(file)[0], self.calibration_csv))
        savepath = savepath.replace('\\', '/')

        with open(savepath, "wb") as csv_file:
            writer = csv.writer(csv_file)
            for line in affine_list:
                writer.writerow(line.split())

    def getAffineTransformations(self):
        file = os.path.join(self.datapath, self.dataset)
        root = ET.parse(file).getroot()
        affine_list = []
        spacer = 'NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN NaN'

        for node in root.findall('./ViewRegistrations/ViewRegistration'):
            node_lines = []
            for i in node:
                elem = i.find('affine').text
                node_lines.append(elem)

            if len(node_lines) > 1:
                node_lines = node_lines[:-1]

            for elem in node_lines:
                affine_list.append(elem)

            affine_list.append(spacer)

        savepath = os.path.normpath(os.path.join(os.path.split(file)[0], self.registration_csv))
        savepath = savepath.replace('\\', '/')

        with open(savepath, "wb") as csv_file:
            writer = csv.writer(csv_file)
            for line in affine_list:
                writer.writerow(line.split())

    def _filter_registration_csv_to_first_timepoint(self, csv_path):
        if not os.path.exists(csv_path):
            raise IOError("Registration CSV not found: " + csv_path)

        rows = []
        with open(csv_path, "rb") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 0:
                    rows.append(row)

        if len(rows) == 0:
            raise ValueError("Registration CSV is empty: " + csv_path)

        filtered = []
        for row in rows:
            filtered.append(row)
            joined = ' '.join(row)
            if joined.startswith('NaN'):
                break

        with open(csv_path, "wb") as f:
            writer = csv.writer(f)
            for row in filtered:
                writer.writerow(row)

    def RegisterDataset(self):
        signal_strength = "[Weak & small (beads)]"
        datapath = os.path.join(self.datapath, self.dataset)

        tp = self.bead_reference_timepoint
        if tp is None:
            tp = self.choose_first_timepoint_from_current_files()

        if tp is None:
            raise ValueError("Could not determine bead reference timepoint.")

        IJ.log("Using bead reference timepoint: " + str(tp))

        IJ.run(
            "Detect Interest Points for Registration",
            "select=[" + datapath + "] "
            "process_angle=[All angles] "
            "process_channel=[All channels] "
            "process_illumination=[All illuminations] "
            "process_tile=[All tiles] "
            "process_timepoint=[Single Timepoint (Select from List)] "
            "type_of_interest_point_detection=Difference-of-Gaussian "
            "label_interest_points=beads "
            "subpixel_localization=[3-dimensional quadratic fit] "
            "interest_point_specification=" + signal_strength + " "
            "downsample_xy=1x downsample_z=1x "
            "compute_on=[CPU (Java)]"
        )

        IJ.run(
            "Register Dataset based on Interest Points",
            "select=[" + datapath + "] "
            "process_angle=[All angles] "
            "process_channel=[All channels] "
            "process_illumination=[All illuminations] "
            "process_tile=[All tiles] "
            "process_timepoint=[Single Timepoint (Select from List)] "
            "registration_algorithm=[Fast descriptor-based (rotation invariant)] "
            "registration_in_between_views=[Only compare overlapping views (according to current transformations)] "
            "interest_points=beads "
            "fix_views=[Fix first view] "
            "map_back_views=[Do not map back (use this if views are fixed)] "
            "transformation=Affine "
            "regularize_model model_to_regularize_with=Rigid "
            "lamba=0.10 redundancy=0 significance=10 "
            "allowed_error_for_ransac=5 "
            "number_of_ransac_iterations=Normal"
        )

    def ApplyCalibration(self):
        channels = self.dims[4]
        times = self.dims[3]
        tiles = self.dims[8]
        dataset = os.path.join(self.datapath, self.dataset)

        registration_list = []
        Reader = csv.reader(open(self.calibfile), delimiter=' ', quotechar='|')

        for registration in Reader:
            registration_list.append(registration[0])

        registration = registration_list[0]

        if (times.find('-') == -1 and times.find(',') == -1) and (len(self.csvtoarray(channels, 'int')) == 1):
            if len(self.csvtoarray(tiles, 'int')) == 1:
                IJ.run("Apply Transformations", "select=[" + dataset + "] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_angles timepoint_" + times + "_channel_" + channels + "_illumination_0_all_angles=[" + registration + "]")
            else:
                IJ.run("Apply Transformations", "select=[" + dataset + "] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_angles same_transformation_for_all_tiles timepoint_" + times + "_channel_" + channels + "_illumination_0_all_angles=[" + registration + "]")
        elif (times.find('-') == -1 and times.find(',') == -1) and (len(self.csvtoarray(channels, 'int')) > 1):
            IJ.run("Apply Transformations", "select=[" + dataset + "] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles timepoint_" + times + "_all_channels_illumination_0_all_angles=[" + registration + "]")
        elif (times.find('-') != -1 or times.find(',') != -1) and (len(self.csvtoarray(channels, 'int')) == 1):
            IJ.run("Apply Transformations", "select=[" + dataset + "] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_channel_" + channels + "_illumination_0_all_angles=[" + registration + "]")
        elif (times.find('-') != -1 or times.find(',') != -1) and (len(self.csvtoarray(channels, 'int')) > 1):
            IJ.run("Apply Transformations", "select=[" + dataset + "] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Identity transform (removes any existing transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=[" + registration + "]")
        else:
            print 'Unexpected calibration application case'

    def ApplyBeadRegCSV(self):
        channels = self.dims[4]
        times = self.dims[3]
        dataset = os.path.join(self.datapath, self.dataset)

        if not os.path.exists(self.regfile):
            raise IOError("Bead registration file not found: " + self.regfile)

        registration_list = []
        Reader = csv.reader(open(self.regfile), delimiter=' ', quotechar='|')
        for registration in Reader:
            registration_list.append(registration[0])

        filtered = []
        for row in registration_list:
            filtered.append(row)
            if row.startswith('NaN'):
                break

        registration_list = filtered

        idx = 0
        for registration in registration_list:
            idx += 1

            if registration.startswith('NaN'):
                continue

            channel = IJ.d2s(int(math.floor((idx - 1) / 2)), 0)
            angle_index = (idx - 1) % 2
            if angle_index == 0:
                angle_name = "0"
            else:
                angle_name = IJ.d2s(4 * self.angle, 0)

            if (times.find('-') == -1 and times.find(',') == -1):
                IJ.run(
                    "Apply Transformations",
                    "select=[" + dataset + "] "
                    "apply_to_angle=[Single angle (Select from List)] "
                    "apply_to_channel=[Single channel (Select from List)] "
                    "apply_to_illumination=[All illuminations] "
                    "apply_to_tile=[All tiles] "
                    "apply_to_timepoint=[All Timepoints] "
                    "processing_angle=[angle " + angle_name + "] "
                    "processing_channel=[channel " + channel + "] "
                    "transformation=Affine "
                    "apply=[Current view transformations (appends to current transforms)] "
                    "same_transformation_for_all_tiles "
                    "timepoint_" + times + "_channel_" + channel + "_illumination_0_angle_" + angle_name + "=[" + registration + "]"
                )
            else:
                IJ.run(
                    "Apply Transformations",
                    "select=[" + dataset + "] "
                    "apply_to_angle=[Single angle (Select from List)] "
                    "apply_to_channel=[Single channel (Select from List)] "
                    "apply_to_illumination=[All illuminations] "
                    "apply_to_tile=[All tiles] "
                    "apply_to_timepoint=[All Timepoints] "
                    "processing_angle=[angle " + angle_name + "] "
                    "processing_channel=[channel " + channel + "] "
                    "transformation=Affine "
                    "apply=[Current view transformations (appends to current transforms)] "
                    "same_transformation_for_all_timepoints "
                    "same_transformation_for_all_tiles "
                    "all_timepoints_channel_" + channel + "_illumination_0_angle_" + angle_name + "=[" + registration + "]"
                )

    def ResaveXMLtoHDF5(self, exportpath):
        datapath = os.path.join(self.datapath, self.dataset)
        exportpath = os.path.join(exportpath, 'hdf5')
        self.createFolder(exportpath)
        exportpath = os.path.join(exportpath, self.dataset)
        IJ.run("As HDF5", "select=[" + datapath + "] resave_angle=[All angles] resave_channel=[All channels] resave_illumination=[All illuminations] resave_tile=[All tiles] resave_timepoint=[All Timepoints] subsampling_factors=[{ {1,1,1}, {2,2,1} }] hdf5_chunk_sizes=[{ {32,16,8}, {16,16,16} }] timepoints_per_partition=1 setups_per_partition=0 use_deflate_compression export_path=[" + exportpath + "]")

    def transformXMLdataset(self):

        times = self.dims[3]
        channels = self.dims[4]
        zplanes = self.dims[2]
        xdim = self.dims[0]
        ydim = self.dims[1]
        pz = self.dims[7]

        pix = IJ.d2s(self.px,4)
        piy = IJ.d2s(self.py,4)
        piz = IJ.d2s(pz,4)

        Angle_ = 2*self.angle
        Angle = IJ.d2s(4*self.angle,0)

        zdim = math.floor(zplanes*pz/self.px)
        mirror_angle = (math.pi/180)*self.angle
        tan0 = math.tan(mirror_angle)
        ydim_deskewed = math.floor(ydim + zdim*tan0)
        zdim_correct_shift = math.floor(zdim/math.cos(mirror_angle))
        tan0 = IJ.d2s(tan0,6)
        datapath = os.path.join(self.datapath,self.dataset)

        if  (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))>1):
            print('single time, multiple channel')
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_channels axis_timepoint_"+times+"_all_channels_illumination_0_angle_0=x-axis rotation_timepoint_"+times+"_all_channels_illumination_0_angle_0="+string+"")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_channels axis_timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=x-axis rotation_timepoint_"+times+"_all_channels_illumination_0_angle_"+Angle+"=-"+string+"")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_channels same_transformation_for_all_angles timepoint_"+times+"_all_channels_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")

        elif (times.find('-')==-1 and times.find(',')==-1) and (len(self.csvtoarray(channels,'int'))==1):
            print('single time, single channel')
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] axis_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_0=x-axis rotation_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_0="+string+"")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] axis_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=x-axis rotation_timepoint_"+times+"_channel_"+channels+"_illumination_0_angle_"+Angle+"=-"+string+"")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_angles timepoint_"+times+"_channel_"+channels+"_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")

        elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))==1):
            print('multiple time, single channel')
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints axis_all_timepoints_channel_"+channels+"_illumination_0_angle_0=x-axis rotation_all_timepoints_channel_"+channels+"_illumination_0_angle_0="+string+"")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints axis_all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=x-axis rotation_all_timepoints_channel_"+channels+"_illumination_0_angle_"+Angle+"=-"+string+"")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_angles all_timepoints_channel_"+channels+"_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")

        elif (times.find('-')!=-1 or times.find(',')!=-1) and (len(self.csvtoarray(channels,'int'))>1):
            print('multiple time, multiple channel')
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0,"+tan0+", 0.0, 0.0, 0.0, 1.0, 0.0]")
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Affine apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_angle_"+Angle+"=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]")
            string = IJ.d2s(zdim_correct_shift,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_angle_"+Angle+"=[0,0,"+string+"]")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=[-"+string1+",-"+string2+",-" +string3+"]")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle 0] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles axis_all_timepoints_all_channels_illumination_0_angle_0=x-axis rotation_all_timepoints_all_channels_illumination_0_angle_0="+string+"")
            string = IJ.d2s(Angle_,0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[Single angle (Select from List)] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] processing_angle=[angle "+Angle+"] transformation=Rigid apply=[Current view transformations (appends to current transforms)] define=[Rotation around axis] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_tiles axis_all_timepoints_all_channels_illumination_0_angle_"+Angle+"=x-axis rotation_all_timepoints_all_channels_illumination_0_angle_"+Angle+"=-"+string+"")
            string1 = IJ.d2s(math.floor(xdim/2),0)
            string2 = IJ.d2s(math.floor(ydim_deskewed/2),0)
            string3 = IJ.d2s(math.floor(zdim_correct_shift/2),0)
            IJ.run("Apply Transformations", "select=["+datapath+"] apply_to_angle=[All angles] apply_to_channel=[All channels] apply_to_illumination=[All illuminations] apply_to_tile=[All tiles] apply_to_timepoint=[All Timepoints] transformation=Translation apply=[Current view transformations (appends to current transforms)] same_transformation_for_all_timepoints same_transformation_for_all_channels same_transformation_for_all_angles same_transformation_for_all_tiles all_timepoints_all_channels_illumination_0_all_angles=["+string1+","+string2+"," +string3+"]")
        else:
            print('incorrect format')


class mvrgetvolumes(object):

    BB = 'All Views'

    def __init__(self, **kwargs):
        valid_keys = ["datapath", "savepath", "binning", "dataset"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))

        self.dataset = self._resolve_dataset_name(getattr(self, 'dataset', None))

        info = self.getXMLinfo()
        self.xml_tiles = info[0]
        self.xml_times = info[1]
        self.xml_angles = info[2]

    def _resolve_dataset_name(self, dataset):
        """
        Resolve which dataset XML to use.

        Priority:
        1. explicit dataset argument
        2. dataset.xml if it exists
        3. exactly one dataset_*.xml file
        4. otherwise raise a clear error
        """
        if dataset is not None:
            dataset_path = os.path.join(self.datapath, dataset)
            if not os.path.exists(dataset_path):
                raise IOError("Dataset XML not found: " + dataset_path)
            return dataset

        default_dataset = os.path.join(self.datapath, 'dataset.xml')
        if os.path.exists(default_dataset):
            return 'dataset.xml'

        candidates = []
        for each in os.listdir(self.datapath):
            if each.startswith('dataset_') and each.endswith('.xml'):
                candidates.append(each)

        candidates.sort()

        if len(candidates) == 1:
            IJ.log("Auto-selected dataset: " + candidates[0])
            return candidates[0]

        if len(candidates) == 0:
            raise IOError(
                "No dataset XML found in folder: " + self.datapath +
                ". Expected dataset.xml or dataset_*.xml"
            )

        raise ValueError(
            "Multiple dataset XML files found in folder: " + self.datapath +
            ". Please specify one explicitly using dataset='...'. Found: " +
            ', '.join(candidates)
        )

    def createFolder(self, fusedpath):
        try:
            if not os.path.exists(fusedpath):
                os.makedirs(fusedpath)
        except OSError:
            print('Error: Creating directory. ' + fusedpath)

    def csvtoarray(self, csv_string, type_):
        csv_vals = csv_string.split(',')
        out = []
        for i in csv_vals:
            if type_ == 'int':
                out.append(int(i))
            elif type_ == 'float':
                out.append(float(i))
            elif type_ == 'string':
                out.append(str(i))
        return out

    def getXMLinfo(self):
        file = os.path.join(self.datapath, self.dataset)
        root = ET.parse(file).getroot()

        tile_list = []
        times_list = []
        angle_list = []

        for node in root.findall('./SequenceDescription/Timepoints'):
            times_list.append(node.find('integerpattern').text)
        times_list = self.csvtoarray(times_list[0], 'int')
        times_list.sort()

        for node in root.findall('./SequenceDescription/ViewSetups/ViewSetup/attributes'):
            elem = node.find('tile').text
            tile_list.append(elem)

        for node in root.findall('./SequenceDescription/ViewSetups/Attributes/Angle/name'):
            angle_list.append(node.text)

        for i in range(len(tile_list)):
            tile_list[i] = int(tile_list[i])

        tile_list = list(set(tile_list))
        tile_list.sort()

        return [tile_list, times_list, angle_list]

    def getFusedVolumes(self):
        datasepath = os.path.join(self.datapath, self.dataset)

        dataset_tag = os.path.splitext(self.dataset)[0]
        fusedfolder = dataset_tag + '_fused_binning_' + self.binning
        fusedpath = os.path.join(self.savepath, fusedfolder)
        self.createFolder(fusedpath)

        tiles = self.xml_tiles
        times = self.xml_times

        if len(tiles) == 1:
            IJ.run(
                "Fuse",
                "select=[" + datasepath + "] "
                "process_angle=[All angles] process_channel=[All channels] "
                "process_illumination=[All illuminations] process_tile=[All tiles] "
                "process_timepoint=[All Timepoints] bounding_box=[" + self.BB + "] "
                "downsampling=" + self.binning + " pixel_type=[16-bit unsigned integer] "
                "interpolation=[Linear Interpolation] image=[Precompute Image] "
                "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                "blend produce=[Each timepoint & channel] "
                "fused_image=[Save as (compressed) TIFF stacks] "
                "output_file_directory=[" + fusedpath + "] "
                "filename_addition=tile_" + str(tiles[0])
            )
        else:
            if len(times) == 1:
                for tile in tiles:
                    IJ.run(
                        "Fuse",
                        "select=[" + datasepath + "] "
                        "process_angle=[All angles] process_channel=[All channels] "
                        "process_illumination=[All illuminations] "
                        "process_tile=[Single tile (Select from List)] "
                        "process_timepoint=[All Timepoints] "
                        "processing_tile=[tile " + str(tile) + "] "
                        "bounding_box=[" + self.BB + "] "
                        "downsampling=" + self.binning + " "
                        "pixel_type=[16-bit unsigned integer] "
                        "interpolation=[Linear Interpolation] image=[Precompute Image] "
                        "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                        "blend produce=[Each timepoint & channel] "
                        "fused_image=[Save as (compressed) TIFF stacks] "
                        "output_file_directory=[" + fusedpath + "] "
                        "filename_addition=tile_" + str(tile)
                    )
            else:
                for time in times:
                    for tile in tiles:
                        IJ.run(
                            "Fuse",
                            "select=[" + datasepath + "] "
                            "process_angle=[All angles] process_channel=[All channels] "
                            "process_illumination=[All illuminations] "
                            "process_tile=[Single tile (Select from List)] "
                            "process_timepoint=[Single Timepoint (Select from List)] "
                            "processing_tile=[tile " + str(tile) + "] "
                            "processing_timepoint=[Timepoint " + str(time) + "] "
                            "bounding_box=[" + self.BB + "] "
                            "downsampling=" + self.binning + " "
                            "pixel_type=[16-bit unsigned integer] "
                            "interpolation=[Linear Interpolation] image=[Precompute Image] "
                            "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                            "blend produce=[Each timepoint & channel] "
                            "fused_image=[Save as (compressed) TIFF stacks] "
                            "output_file_directory=[" + fusedpath + "] "
                            "filename_addition=tile_" + str(tile)
                        )

    def getSingleView(self, view):
        datasepath = os.path.join(self.datapath, self.dataset)

        dataset_tag = os.path.splitext(self.dataset)[0]
        fusedfolder = dataset_tag + '_view_' + str(int(view) + 1) + '_binning_' + self.binning
        fusedpath = os.path.join(self.savepath, fusedfolder)
        self.createFolder(fusedpath)

        tiles = self.xml_tiles
        times = self.xml_times

        if len(tiles) == 1:
            IJ.run(
                "Fuse",
                "select=[" + datasepath + "] "
                "process_angle=[Single angle (Select from List)] "
                "process_channel=[All channels] process_illumination=[All illuminations] "
                "process_tile=[All tiles] process_timepoint=[All Timepoints] "
                "processing_angle=[angle " + self.xml_angles[int(view)] + "] "
                "bounding_box=[" + self.BB + "] "
                "downsampling=" + self.binning + " "
                "pixel_type=[16-bit unsigned integer] "
                "interpolation=[Linear Interpolation] image=[Precompute Image] "
                "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                "blend produce=[Each timepoint & channel] "
                "fused_image=[Save as (compressed) TIFF stacks] "
                "output_file_directory=[" + fusedpath + "] "
                "filename_addition=tile_" + str(tiles[0])
            )
        else:
            if len(times) == 1:
                for tile in tiles:
                    IJ.run(
                        "Fuse",
                        "select=[" + datasepath + "] "
                        "process_angle=[Single angle (Select from List)] "
                        "process_channel=[All channels] process_illumination=[All illuminations] "
                        "process_tile=[Single tile (Select from List)] "
                        "process_timepoint=[All Timepoints] "
                        "processing_angle=[angle " + self.xml_angles[int(view)] + "] "
                        "processing_tile=[tile " + str(tile) + "] "
                        "bounding_box=[" + self.BB + "] "
                        "downsampling=" + self.binning + " "
                        "pixel_type=[16-bit unsigned integer] "
                        "interpolation=[Linear Interpolation] image=[Precompute Image] "
                        "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                        "blend produce=[Each timepoint & channel] "
                        "fused_image=[Save as (compressed) TIFF stacks] "
                        "output_file_directory=[" + fusedpath + "] "
                        "filename_addition=tile_" + str(tile)
                    )
            else:
                for time in times:
                    for tile in tiles:
                        IJ.run(
                            "Fuse",
                            "select=[" + datasepath + "] "
                            "process_angle=[Single angle (Select from List)] "
                            "process_channel=[All channels] process_illumination=[All illuminations] "
                            "process_tile=[Single tile (Select from List)] "
                            "process_timepoint=[Single Timepoint (Select from List)] "
                            "processing_angle=[angle " + self.xml_angles[int(view)] + "] "
                            "processing_tile=[tile " + str(tile) + "] "
                            "processing_timepoint=[Timepoint " + str(time) + "] "
                            "bounding_box=[" + self.BB + "] "
                            "downsampling=" + self.binning + " "
                            "pixel_type=[16-bit unsigned integer] "
                            "interpolation=[Linear Interpolation] image=[Precompute Image] "
                            "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                            "blend produce=[Each timepoint & channel] "
                            "fused_image=[Save as (compressed) TIFF stacks] "
                            "output_file_directory=[" + fusedpath + "] "
                            "filename_addition=tile_" + str(tile)
                        )

    def getSingleViewSubset(self, view, times, tiles):
        datasepath = os.path.join(self.datapath, self.dataset)

        dataset_tag = os.path.splitext(self.dataset)[0]
        fusedfolder = dataset_tag + '_subset_view_' + str(int(view) + 1) + '_binning_' + self.binning
        fusedpath = os.path.join(self.savepath, fusedfolder)
        self.createFolder(fusedpath)

        for time in times:
            for tile in tiles:
                IJ.run(
                    "Fuse",
                    "select=[" + datasepath + "] "
                    "process_angle=[Single angle (Select from List)] "
                    "process_channel=[All channels] process_illumination=[All illuminations] "
                    "process_tile=[Single tile (Select from List)] "
                    "process_timepoint=[Single Timepoint (Select from List)] "
                    "processing_angle=[angle " + self.xml_angles[int(view)] + "] "
                    "processing_tile=[tile " + str(tile) + "] "
                    "processing_timepoint=[Timepoint " + str(time) + "] "
                    "bounding_box=[" + self.BB + "] "
                    "downsampling=" + self.binning + " "
                    "pixel_type=[16-bit unsigned integer] "
                    "interpolation=[Linear Interpolation] image=[Precompute Image] "
                    "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                    "blend produce=[Each timepoint & channel] "
                    "fused_image=[Save as (compressed) TIFF stacks] "
                    "output_file_directory=[" + fusedpath + "] "
                    "filename_addition=tile_" + str(tile)
                )

    def getFusedVolumesSubset(self, times, tiles):
        datasepath = os.path.join(self.datapath, self.dataset)

        dataset_tag = os.path.splitext(self.dataset)[0]
        fusedfolder = dataset_tag + '_subset_fused_binning_' + self.binning
        fusedpath = os.path.join(self.savepath, fusedfolder)
        self.createFolder(fusedpath)

        for time in times:
            for tile in tiles:
                IJ.run(
                    "Fuse",
                    "select=[" + datasepath + "] "
                    "process_angle=[All angles] process_channel=[All channels] "
                    "process_illumination=[All illuminations] "
                    "process_tile=[Single tile (Select from List)] "
                    "process_timepoint=[Single Timepoint (Select from List)] "
                    "processing_tile=[tile " + str(tile) + "] "
                    "processing_timepoint=[Timepoint " + str(time) + "] "
                    "bounding_box=[" + self.BB + "] "
                    "downsampling=" + self.binning + " "
                    "pixel_type=[16-bit unsigned integer] "
                    "interpolation=[Linear Interpolation] image=[Precompute Image] "
                    "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
                    "blend produce=[Each timepoint & channel] "
                    "fused_image=[Save as (compressed) TIFF stacks] "
                    "output_file_directory=[" + fusedpath + "] "
                    "filename_addition=tile_" + str(tile)
                )

    def ResaveXMLtoHDF5(self):
        datapath = os.path.join(self.datapath, self.dataset)
        IJ.run(
            "As HDF5",
            "select=[" + datapath + "] "
            "resave_angle=[All angles] resave_channel=[All channels] "
            "resave_illumination=[All illuminations] resave_tile=[All tiles] "
            "resave_timepoint=[All Timepoints] "
            "subsampling_factors=[{ {1,1,1}, {2,2,1} }] "
            "hdf5_chunk_sizes=[{ {32,16,8}, {16,16,16} }] "
            "timepoints_per_partition=1 setups_per_partition=0 "
            "use_deflate_compression export_path=[" + datapath + "]"
        )

    def CheckTimesTilesSubsets(self, tiles_chosen, times_chosen):
        tiles = self.xml_tiles
        times = self.xml_times

        if "-" in tiles_chosen:
            tiles_chosen = tiles_chosen.split('-')
            tiles_chosen = range(int(tiles_chosen[0]), int(tiles_chosen[1]) + 1, 1)
            if set(tiles_chosen) <= set(tiles):
                tiles_chosen = list(set(tiles_chosen))
            else:
                print 'no valid tiles chosen aborting'
                return
        elif "," in tiles_chosen:
            tiles_chosen = tiles_chosen.split(',')
            tiles_chosen = [int(x) for x in tiles_chosen]
            if set(tiles_chosen) <= set(tiles):
                tiles_chosen = list(set(tiles_chosen))
            else:
                print 'no valid tiles chosen aborting'
                return
        elif tiles_chosen:
            if not isinstance(tiles_chosen, list):
                tiles_chosen = [int(tiles_chosen)]
            if set(tiles_chosen) <= set(tiles):
                tiles_chosen = list(set(tiles_chosen))
            else:
                print 'no valid tiles chosen aborting'
                return
        else:
            print 'no valid tiles chosen aborting'
            return

        if "-" in times_chosen:
            times_chosen = times_chosen.split('-')
            times_chosen = range(int(times_chosen[0]), int(times_chosen[1]) + 1, 1)
            if set(times_chosen) <= set(times):
                times_chosen = list(set(times_chosen))
            else:
                print 'no valid times chosen aborting'
                return
        elif "," in times_chosen:
            times_chosen = times_chosen.split(',')
            times_chosen = [int(x) for x in times_chosen]
            if set(times_chosen) <= set(times):
                times_chosen = list(set(times_chosen))
            else:
                print 'no valid times chosen aborting'
                return
        elif times_chosen:
            if not isinstance(times_chosen, list):
                times_chosen = [int(times_chosen)]
            if set(times_chosen) <= set(times):
                times_chosen = list(set(times_chosen))
            else:
                print 'no valid times chosen aborting'
                return
        else:
            print 'no valid times chosen aborting'
            return

        print 'times and tiles valid starting processing.....'
        return [True, sorted(times_chosen), sorted(tiles_chosen)]
   
   
class defineboundingbox(object):

    def __init__(self, **kwargs):
        valid_keys = ["datapath", "beadpath", "dataset"]
        for key in valid_keys:
            setattr(self, key, kwargs.get(key))

        if getattr(self, 'dataset', None) is None:
            self.dataset = 'dataset.xml'

    def getXMLBoundingBox(self, datapath):
        file = os.path.join(datapath, self.dataset)
        root = ET.parse(file).getroot()

        for boundingbox in root.find('./BoundingBoxes'):
            if boundingbox.get('name') == 'My Bounding Box':
                min_ = boundingbox.find('min').text.split(' ')
                max_ = boundingbox.find('max').text.split(' ')
                return [min_, max_]

    def defineBoundingBox(self, datapath):
        datasepath = os.path.join(datapath, self.dataset)
        IJ.run(
            "Define Bounding Box",
            "select=[" + datasepath + "] "
            "process_angle=[All angles] process_channel=[All channels] "
            "process_illumination=[All illuminations] process_tile=[All tiles] "
            "process_timepoint=[All Timepoints] "
            "bounding_box=[Define using the BigDataViewer interactively] "
            "bounding_box_name=[My Bounding Box]"
        )

    def defineBoundingBoxNoInteraction(self, datapath):
        datasepath = os.path.join(datapath, self.dataset)
        IJ.run(
            "Define Bounding Box",
            "select=[" + datasepath + "] "
            "process_angle=[All angles] process_channel=[All channels] "
            "process_illumination=[All illuminations] process_tile=[All tiles] "
            "process_timepoint=[All Timepoints] "
            "bounding_box=[Maximal Bounding Box spanning all transformed views] "
            "bounding_box_name=[My Bounding Box] "
            "minimal_x=0 minimal_y=0 minimal_z=0 "
            "maximal_x=100 maximal_y=100 maximal_z=100"
        )

    def modifyBoundingBox(self, datapath, BB):
        datasepath = os.path.join(datapath, self.dataset)
        IJ.run(
            "Define Bounding Box",
            "select=[" + datasepath + "] "
            "process_angle=[All angles] process_channel=[All channels] "
            "process_illumination=[All illuminations] process_tile=[All tiles] "
            "process_timepoint=[All Timepoints] "
            "bounding_box=[Modify pre-defined Bounding Box] "
            "bounding_box_name=[My Bounding Box] "
            "bounding_box_title=[My Bounding Box] "
            "minimal_x=" + BB[0][0] + " "
            "minimal_y=" + BB[0][1] + " "
            "minimal_z=" + BB[0][2] + " "
            "maximal_x=" + BB[1][0] + " "
            "maximal_y=" + BB[1][1] + " "
            "maximal_z=" + BB[1][2]
        )

    def OptimalBoundingBox(self, datapath):
        settingsfile = os.path.join(datapath, 'dopmsettings.xml')
        IJ.log(str(datapath))
        IJ.log(str(settingsfile))
        settings = readdopmxml(settingsfile)

        zstack_microns = int(settings['rawzplanes'])
        prism_angle = float(settings['prismangle'])

        datapath_ = os.path.join(datapath, self.dataset)
        IJ.log(str(datapath_))

        IJ.run(
            "Fuse",
            "select=[" + datapath_ + "] "
            "process_angle=[All angles] "
            "process_channel=[Single channel (Select from List)] "
            "process_illumination=[All illuminations] "
            "process_tile=[Single tile (Select from List)] "
            "process_timepoint=[Single Timepoint (Select from List)] "
            "processing_channel=[channel 0] "
            "processing_tile=[tile 0] "
            "processing_timepoint=[Timepoint 0] "
            "bounding_box=[All Views] downsampling=1 "
            "pixel_type=[16-bit unsigned integer] "
            "interpolation=[Linear Interpolation] image=[Precompute Image] "
            "interest_points_for_non_rigid=[-= Disable Non-Rigid =-] "
            "blend produce=[Each timepoint & channel] "
            "fused_image=[Display using ImageJ]"
        )

        imp = IJ.getImage()

        offset = [
            imp.getCalibration().xOrigin / imp.getCalibration().pixelWidth,
            imp.getCalibration().yOrigin / imp.getCalibration().pixelHeight,
            imp.getCalibration().zOrigin / imp.getCalibration().pixelDepth
        ]

        d = round(zstack_microns / imp.getCalibration().pixelDepth)
        d_z = round(d / math.cos(2 * prism_angle * math.pi / 180))

        bb_x = [
            0 - math.floor(offset[0]),
            imp.getWidth() - math.ceil(offset[0])
        ]

        bb_y = [
            -math.floor(offset[1]),
            imp.getHeight() - math.floor(offset[1])
        ]

        bb_z = [
            (imp.getImageStackSize() / 2 - math.floor(d_z / 2)) - math.floor(offset[2]),
            (imp.getImageStackSize() / 2 + math.floor(d_z / 2)) - math.ceil(offset[2])
        ]

        imp.close()

        bb_x = [str(x) for x in bb_x]
        bb_y = [str(x) for x in bb_y]
        bb_z = [str(x) for x in bb_z]

        IJ.log("=========================================================")
        IJ.log("recommended bounding box for diamond for x range is: ")
        IJ.log(' '.join(bb_x))
        IJ.log("recommended bounding box for diamond for y range is: ")
        IJ.log(' '.join(bb_y))
        IJ.log("recommended bounding box for diamond for z range is: ")
        IJ.log(' '.join(bb_z))
        IJ.log("--------------------------------------------------------")

        settings['BoundingBoxDefinition'] = 'My Bounding Box'
        settings['boundingboxmin'] = ' '.join([bb_x[0], bb_y[0], bb_z[0]])
        settings['boundingboxmax'] = ' '.join([bb_x[1], bb_y[1], bb_z[1]])

        settingsfile = os.path.join(datapath, 'dopmsettings.xml')
        writedopmxml(settingsfile, settings)

        BB = [[bb_x[0], bb_y[0], bb_z[0]], [bb_x[1], bb_y[1], bb_z[1]]]
        return BB


if __name__ in ['__builtin__', '__main__']:
    IJ.log("Finished")