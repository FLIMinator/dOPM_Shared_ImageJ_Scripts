# dOPM Shared ImageJ Scripts

Jython scripts for processing dual-view oblique plane microscopy (dOPM) datasets in Fiji/ImageJ using Multiview Reconstruction / BigStitcher.

This README is written as a **how-to guide**. For the exact pinned Fiji/JAR versions used by the project, see `FIJI_ENVIRONMENT.md`.

## What this workflow does

The scripts support a typical dOPM processing sequence:

```text
bead dataset
  -> geometric transform / deskew
  -> bead registration
  -> optional bead-derived bounding box
  -> transfer registration to sample datasets
  -> process all detected wells
  -> optional fusion
  -> optional XYZ MIP generation
```

The current workflow is designed for Nikon `.nd2` files and the two-view filename pattern described below.

---

# 1. Install the validated Fiji environment

## Windows - recommended

Clone or download this repository, then run:

```text
installers\setup_dOPM_windows.bat
```

The setup script will:

1. create a validated Fiji 2.9.0 environment if one does not already exist;
2. install the pinned BigStitcher / Multiview Reconstruction / BigDataViewer / CLIJ compatibility stack;
3. create the Fiji script folder;
4. copy the repository Python/Jython scripts into Fiji.

The generated Fiji installation is placed here:

```text
dOPM_Shared_ImageJ_Scripts/
  Fiji_2.9.0_dOPM/
    Fiji.app/
```

The dOPM scripts are copied to:

```text
Fiji_2.9.0_dOPM/Fiji.app/plugins/Scripts/dOPM
```

No separate CPython installation is required. The processing scripts run inside Fiji using Jython.

## Linux x86_64

Run:

```bash
chmod +x installers/setup_dOPM_linux.sh
./installers/setup_dOPM_linux.sh
```

The Linux setup reconstructs the same pinned Fiji/plugin stack. CLIJ2 MIP generation also requires a working OpenCL runtime/driver on the Linux machine.

## Build Fiji only

If you only want the Fiji environment and do not want the repository scripts copied automatically, use:

```text
installers/build_dOPM_Fiji_windows.bat
```

or:

```bash
installers/build_dOPM_Fiji_linux.sh
```

For manual reconstruction of the environment, see `FIJI_ENVIRONMENT.md`.

> **Important:** do not update Fiji / BigStitcher before validating the workflow. The project currently relies on a pinned historical plugin stack.

---

# 2. Prepare your data

## Two-view filename pattern

The canonical pattern is:

```text
spim_Time{tttt}_Tile{xxxx}_angle{a}.nd2
```

Example:

```text
spim_Time0000_Tile0000_angle0.nd2
spim_Time0000_Tile0000_angle70.nd2
```

Well suffixes are supported:

```text
spim_Time0000_Tile0000_angle0__WellF5.nd2
spim_Time0000_Tile0000_angle70__WellF5.nd2
```

When well suffixes are present, the workflow creates separate XML datasets such as:

```text
dataset_WellF5.xml
dataset_WellF6.xml
```

Files without a well suffix use:

```text
dataset.xml
```

## Recommended folder arrangement

Keep bead/reference data and biological/sample data in separate folders, for example:

```text
experiment/
  beads/
    spim_Time0000_Tile0000_angle0.nd2
    spim_Time0000_Tile0000_angle70.nd2

  data/
    spim_Time0000_Tile0000_angle0__WellF5.nd2
    spim_Time0000_Tile0000_angle70__WellF5.nd2
    spim_Time0000_Tile0001_angle0__WellF5.nd2
    spim_Time0000_Tile0001_angle70__WellF5.nd2
    spim_Time0000_Tile0002_angle0__WellF6.nd2
    spim_Time0000_Tile0002_angle70__WellF6.nd2
```

The automatic workflow detects the well patterns and processes them as separate sample datasets.

---

# 3. Recommended workflow: automatic batch processing

Run:

```text
automatic_batch_workflow.py
```

from Fiji's dOPM script menu / script location.

The dialog asks for:

- bead/reference folder;
- sample data folder;
- optional output folder;
- pixel size;
- prism / mirror angle;
- fusion binning;
- whether to use one bead-derived bounding box for all sample datasets;
- whether to fuse the sample datasets;
- whether to create XYZ MIP montages;
- whether existing sample XML files may be rebuilt.

## If the bead folder already contains a registered XML

The script uses the existing registered bead dataset as the registration source.

If an HDF5-resaved bead XML is present, it can be used directly for registration transfer.

For bounding-box estimation, the workflow now supports both:

- bead datasets backed by the original ND2 files; and
- HDF5/XML-only bead datasets.

The raw Z depth is obtained from the XML when available, with ND2 metadata used as a fallback. If neither provides it, the user is prompted for the original raw Z depth.

## If the bead folder does not contain an XML

The workflow asks what to do rather than silently creating a registration.

You can either:

1. abort and use the original manual bead workflow, inspect the registration, and then rerun the automatic workflow; or
2. explicitly allow the automatic bead workflow to run.

The automatic bead sequence is:

```text
create XML
-> apply calibration
-> apply dOPM geometric transforms
-> register beads
-> resave to HDF5
-> calculate bead bounding box when requested
```

## Sample processing

After a bead registration source has been selected or created, the workflow:

1. discovers the well groups in the sample folder;
2. creates one dataset XML per well;
3. applies the sample geometry;
4. transfers the bead registration to the sample datasets;
5. optionally applies the same bead-derived bounding box to every sample XML;
6. optionally fuses all datasets;
7. optionally creates XYZ MIP montages from the fused TIFF stacks.

If MIPs are selected, fusion is required because the MIP stage operates on the fused TIFF outputs.

---

# 4. Manual workflow

Use the manual scripts when you want to inspect or intervene at individual BigStitcher stages.

The intended order is:

```text
1. create / transform / register the bead dataset
2. inspect the bead registration in BigStitcher / Data Explorer
3. define the bead bounding box
4. create sample datasets and transfer bead registration
5. copy the common bounding box to the sample datasets
6. fuse / export the sample datasets
7. generate MIPs
```

The main scripts are:

- `make_mvr_dataset.py` - create, transform, and register bead/sample datasets
- `define_bounding_box.py` - define, calculate, or copy bounding boxes
- `get_deskewed_dopm_volumes.py` - export fused or single-view volumes
- `get_fused_MIPs.py` - create MIP montages
- `dopmmvr.py` - shared dOPM / BigStitcher implementation used by the workflow scripts

## Inspecting bead registration

After bead registration, open the dataset in BigStitcher / Data Explorer and inspect the views before using the registration on biological data.

The pinned BigDataViewer stack is included specifically so the BigStitcher viewer / Data Explorer can be used for this QC step.

---

# 5. Bounding boxes

A common bead-derived bounding box can be applied to every sample dataset so that all exported volumes use the same coordinate extent.

The bounding-box tools support:

- a bead XML with the original ND2 data available;
- a resaved HDF5 bead XML without the original ND2 files;
- manual entry of the original raw Z depth if it cannot be determined automatically.

In the automatic workflow, enable:

```text
Use one bead-derived bounding box for all sample datasets
```

when you want all well datasets to use the same bead-derived volume limits.

---

# 6. Fusion and MIPs

If fusion is enabled, the workflow processes every generated sample XML in batch.

Typical output structure:

```text
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

The MIP workflow generates an XYZ montage for each fused TIFF stack using CLIJ2.

---

# 7. Validate the installation with the example dataset

A small example dataset is available on Zenodo:

<https://zenodo.org/records/22979717>

Expected layout after extraction:

```text
demo_sample_data/
  v1/     # bead data without a well suffix
  v2/     # bead data with a well suffix
  data/   # multi-well sample data
```

Run:

```text
validation/Test_dOPM_EndToEnd_v3_faithful.py
```

inside Fiji and select the extracted `demo_sample_data` folder.

The validator copies the source ND2 files into an isolated test area, so the original test dataset is not modified.

The validation workflow follows the production processing order and checks more than file creation. It verifies that:

- dOPM geometry transforms were applied;
- bead registration changed the registration transforms;
- the HDF5 resave preserved the registered transforms;
- sample registration stacks match the bead registration source;
- the common bounding box is copied correctly;
- fused TIFFs are produced;
- the number of generated MIPs matches the fused TIFF outputs.

The development validation has passed both supported bead filename patterns (`v1` and `v2`) through the complete workflow.

---

# 8. Troubleshooting

## BigStitcher / Data Explorer opens but the BigDataViewer window fails

The dOPM environment requires a compatible historical BigDataViewer stack. The setup scripts pin:

```text
bigdataviewer-core-10.2.0.jar
bigdataviewer-vistools-1.0.0-beta-28.jar
bigdataviewer_fiji-6.2.1.jar
```

A newer bundled `bigdataviewer-core-10.4.3.jar` can cause a `NoSuchMethodError` when the Data Explorer tries to open the BDV viewer.

Rebuild Fiji using the current installer if you see that error.

## The scripts run but the bead registration looks wrong

Do not rely only on the fact that the registration command completed. Inspect the bead dataset in BigStitcher / Data Explorer before transferring the registration to biological data.

The faithful validation script also checks that registration produced non-identity changes rather than accepting a no-op registration as a pass.

## Bounding-box calculation asks for ND2 data

Use the current version of `automatic_batch_workflow.py` / `define_bounding_box.py`. The updated code can obtain raw Z depth from the bead XML for HDF5-only datasets and only falls back to ND2 metadata when necessary.

## MIPs fail on Linux

Check that the machine has a functioning OpenCL implementation / GPU driver. CLIJ2 depends on OpenCL.

---

# 9. Repository contents

```text
dOPM_Shared_ImageJ_Scripts/
  automatic_batch_workflow.py
  define_bounding_box.py
  dopmmvr.py
  get_deskewed_dopm_volumes.py
  get_fused_MIPs.py
  make_mvr_dataset.py

  installers/
    setup_dOPM_windows.bat
    setup_dOPM_linux.sh
    build_dOPM_Fiji_windows.bat
    build_dOPM_Fiji_linux.sh

  validation/
    Test_dOPM_EndToEnd_v3_faithful.py

  FIJI_ENVIRONMENT.md
  LICENSE.md
```

The generated Fiji environment is stored at the repository root as `Fiji_2.9.0_dOPM/` and is ignored by Git.

---

# 10. License

See `LICENSE.md`.
