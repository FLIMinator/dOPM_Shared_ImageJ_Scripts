# dOPM Shared ImageJ Scripts

Jython scripts for processing dual-view oblique plane microscopy (dOPM) datasets in Fiji/ImageJ with the Multiview Reconstruction / BigStitcher framework.

This revision adds a reproducible Fiji build, a faithful end-to-end validation script, and a higher-level automatic batch workflow while keeping the original step-by-step scripts available for inspection and manual control.

Currently supports Nikon .nd2 files. Can be extended to .tiffs and other formats while adhering to the Multiview Reconstruction / BigStitcher framework.

## What is in this repository

Production Fiji scripts at the repository root:

- `dopmmvr.py` — shared dOPM/BigStitcher implementation
- `make_mvr_dataset.py` — create, transform, and register bead/sample datasets
- `define_bounding_box.py` — define or copy bounding boxes
- `get_deskewed_dopm_volumes.py` — export fused or single-view volumes
- `get_fused_MIPs.py` — generate MIP montages from exported TIFFs
- `automatic_batch_workflow.py` — user-facing batch workflow from beads through sample datasets, optional fusion, and optional MIPs

Reproducibility/support files:

- `installers/build_dOPM_Fiji_windows.bat` — Windows 64-bit Fiji builder; no CPython required
- `installers/build_dOPM_Fiji_linux.sh` — Linux x86_64 Fiji builder; no CPython required
- `FIJI_ENVIRONMENT.md` — manual record of the exact tested Fiji/plugin recipe
- `validation/Test_dOPM_EndToEnd_v3_faithful.py` — strict production-order end-to-end test

The previous long-form user guide is intentionally not included in this draft revision. A new guide can be added after the automated workflow is finalised.

## Installation

### Recommended: build the tested Fiji environment

For Windows, run:

```text
installers\build_dOPM_Fiji_windows.bat
```

For Linux x86_64:

```bash
chmod +x installers/build_dOPM_Fiji_linux.sh
./installers/build_dOPM_Fiji_linux.sh
```

Both installers start from official Fiji 2.9.0 and install the pinned Multiview Reconstruction / SPIM Registration / CLIJ / CLIJ2 compatibility components used by the validated workflow. The official Fiji 2.9.0 release archive provides both Windows and Linux 64-bit builds.

The installers do **not** copy the dOPM source code into Fiji. After the Fiji build finishes, copy the production `.py` files from this repository to:

```text
Fiji.app/plugins/Scripts/dOPM
```

Then restart Fiji.

No separate CPython installation is required: these scripts run under Fiji's Jython environment.

### Manual Fiji reconstruction

If you do not want to use either installer, follow `FIJI_ENVIRONMENT.md`. It records the base Fiji archive, exact compatibility JAR versions, download locations, and target paths.

## Automatic batch workflow

Run:

```text
automatic_batch_workflow.py
```

The GUI asks for:

- bead/reference folder
- sample data folder
- optional output folder
- pixel size
- prism / mirror angle
- fusion binning
- whether to use one bead-derived bounding box for all sample datasets
- whether to fuse all sample datasets
- whether to create XYZ MIP montages
- whether rebuilding existing sample XML files is allowed

The workflow reuses the same production functions used by the original GenericDialog scripts rather than maintaining an independent processing implementation.

### Bead behaviour

If a registered bead XML already exists, the workflow uses it as the registration source. HDF5 XML files are preferred when present, matching the faithful validation path.

If no bead XML exists, the script deliberately does not silently create one. It offers either:

1. abort and use the original bead workflow for manual inspection/optimisation; or
2. explicitly run the automatic bead path.

The automatic bead path follows the tested order: create XML, apply calibration, apply dOPM geometry, register beads, resave to HDF5, then derive the bounding box when requested.

### Multi-well sample processing

Sample processing calls the production `process_data_with_beads(...)` workflow, which discovers the well groups and generates the corresponding `dataset_Well...xml` files. The automatic workflow then optionally copies one bead-derived bounding box to all sample XMLs, performs batch fusion, and generates MIPs from the fused TIFF stacks.

If MIPs are selected while fusion is not selected, fusion is enabled automatically because this workflow generates MIPs from fused TIFF outputs.

## Original manual workflow

The original scripts remain available and are still useful when a user wants to inspect or intervene at each BigStitcher stage.

The intended order is:

```text
1. make/register bead dataset
2. inspect/optimise bead registration if required
3. derive or define the bead bounding box
4. create sample datasets and transfer bead registration
5. copy the common bounding box to the sample datasets
6. fuse/export sample datasets
7. generate MIPs
```

The faithful validator intentionally mirrors these existing GenericDialog workflows in this order rather than constructing a parallel pipeline.

## Data assumptions

The canonical two-view file pattern is:

```text
spim_Time{tttt}_Tile{xxxx}_angle{a}.nd2
```

For example:

```text
spim_Time0000_Tile0000_angle0.nd2
spim_Time0000_Tile0000_angle70.nd2
```

Optional well suffixes are supported:

```text
spim_Time0000_Tile0000_angle0__WellF5.nd2
spim_Time0000_Tile0000_angle70__WellF5.nd2
```

Well-suffixed files are grouped into independent datasets such as:

```text
dataset_WellF5.xml
dataset_WellF6.xml
```

Files without a well suffix use the default dataset name:

```text
dataset.xml
```

The current two-view registration model treats the bead registration as a global experiment-level registration source. Sample transforms are matched by channel and angle and transferred across the sample timepoints, tiles, and well datasets.

## Output example

```text
data/
  dataset_WellF5.xml
  dataset_WellF6.xml
  dOPM_automatic_batch_report.txt

output/
  dataset_WellF5/
    dataset_WellF5_fused_binning_2/
      *.tif
      MIP/
        *.tif
  dataset_WellF6/
    dataset_WellF6_fused_binning_2/
      *.tif
      MIP/
        *.tif
```

## Test dataset

A public Zenodo record will contain the small validation dataset used during development.

**Placeholder — replace when the Zenodo record is published:**

<https://zenodo.org/records/22979717>

Expected extracted layout:

```text
demo_sample_data/
  v1/     # bead data without a well suffix
  v2/     # bead data with a well suffix
  data/   # sample data with multiple well groups
```

The faithful validator expects exactly this `v1`, `v2`, and `data` structure.

Run `validation/Test_dOPM_EndToEnd_v3_faithful.py` inside Fiji and choose the extracted `demo_sample_data` folder. The validator copies the raw ND2 inputs into an isolated test area before running, so the source test data are not modified.

### Current validated result

The development test has passed both supported bead naming cases through the full production-order workflow, including geometry, registration transfer, common bounding box, fused TIFF output, and MIP generation.

The test specifically checks that bead registration changes the ViewRegistration transforms rather than accepting an identity/no-registration result. It also verifies that each sample transform stack exactly matches the corresponding bead registration source by channel and angle.

With the current demo data and the tested settings (`0.35 um`, `17.5 degrees`, fusion binning `2`), both v1 and v2 completed successfully. The multi-well sample set produced fused volumes and a matching MIP count for each dataset.

## Important reproducibility note

Do not run the Fiji updater before reproducing the validation. This project currently depends on specific historical Multiview Reconstruction and CLIJ versions. In particular, the dOPM code relies on the ImageJ command named `Fuse`, which is supplied by the pinned Multiview Reconstruction version used here.

## Linux status

The Linux installer reconstructs the same pinned Fiji/Java plugin stack using the official Fiji 2.9.0 Linux x86_64 archive. The shell script has been syntax-checked, but the full end-to-end dOPM workflow still needs to be run on a Linux workstation before Linux should be described as experimentally validated. CLIJ2 MIP generation additionally requires a functioning OpenCL runtime/driver on that system.

## License

See `LICENSE.md`.
