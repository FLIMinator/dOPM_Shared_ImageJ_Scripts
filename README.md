Here is a rewritten version in a more conventional bioimage analysis / academic software style.

---

# dOPM Shared ImageJ Scripts

Scripts for processing dual-view oblique plane microscopy (dOPM) datasets in Fiji/ImageJ using the Multiview Reconstruction framework (BigStitcher).

These scripts provide a lightweight interface for defining, transforming, registering, and fusing dOPM datasets. The implementation is intentionally minimal and relies on existing functionality in BigStitcher rather than reimplementing core algorithms.

---

## Overview

dOPM datasets consist of obliquely acquired image stacks from multiple views. This repository provides a set of scripts to:

* define multiview datasets from raw image files
* apply geometric transformations (deskew and rotation)
* perform view registration (optional, typically using bead datasets)
* fuse volumes using BigStitcher
* export fused or single-view volumes
* generate maximum intensity projections (MIPs) for rapid inspection

The pipeline is based on affine transformations stored in XML metadata, avoiding unnecessary reslicing during preprocessing.

---

## Installation

### Fiji

Use the following Fiji distribution, which has been tested with these scripts and is compatible with CLIJ:

[https://imperialcollegelondon.app.box.com/s/2pc9iiusvuh36uc8arceoutrwxi193ul/file/1364388978888](https://imperialcollegelondon.app.box.com/s/2pc9iiusvuh36uc8arceoutrwxi193ul/file/1364388978888)

Other Fiji versions may not be compatible with the Multiview Reconstruction workflows used here.

### Script installation

Clone or copy this repository into:

```
Fiji.app/plugins/Scripts/dOPM
```

After restarting Fiji, the scripts will be available under the `dOPM` menu.

---

## Dependencies

* Fiji (tested version above)
* Multiview Reconstruction / BigStitcher
* CLIJ (for GPU-accelerated projection and image processing)

---

## Data assumptions

* Two-view dOPM acquisition (angle 0 and angle 70 or equivalent)
* Consistent filename structure, for example:

```
spim_Time0000_Tile0000_angle0[_WellC2].nd2
spim_Time0000_Tile0000_angle70[_WellC2].nd2
```

* Optional well suffixes (e.g. `WellC2`) are supported and used to generate separate datasets per well

---

## Workflow

### 1. Dataset definition

Use `make_mvr_dataset.py` to generate a multiview dataset.

Outputs include:

* dataset XML file (`dataset_*.xml`)
* calibration metadata
* transformation definitions

The dataset definition step encodes all geometric transformations required for deskewing and alignment.

---

### 2. Registration (optional)

If bead data are available, registration can be performed on a single bead timepoint and reused for all sample datasets.

This is typically sufficient because the relative geometry between views is fixed.

---

### 3. Bounding box definition

Bounding boxes can be defined using the menu:

```
dOPM → Define bounding box for dataset
```

Available modes:

* manual definition
* reuse from a bead dataset
* geometric prediction (experimental)

The bounding box is stored in the dataset XML and applied during fusion.

---

### 4. Volume extraction

Deskewed volumes can be extracted using:

```
dOPM → Extract deskewed volumes
```

Options include:

* fused volumes
* single-view volumes
* configurable binning

---

### 5. Maximum intensity projections (MIPs)

MIPs can be generated using:

```
dOPM → MIPs
```

This uses CLIJ for GPU-accelerated projection and is intended for rapid quality control of fused datasets.

Batch modes are available to process multiple dataset folders.

---

## Bounding box (geometric mode)

An experimental method is included to estimate an optimal bounding box based on dOPM acquisition geometry.

This approach:

* computes the expected spatial extent of the scanned volume
* reduces the fused volume size (typically by ~20% or more)

Limitations:

* requires an initial bead dataset
* not fully headless
* still under evaluation

---

## Output structure

Typical output layout:

```
data/
  dataset_WellF5.xml
  dataset_WellF5/
    dataset_WellF5_fused_binning_2/
      *.tif
      MIP/
```

Each well is processed independently, with separate dataset XML files and output folders.

---

## Design principles

* Minimal abstraction layer over BigStitcher
* All transformations stored in XML metadata
* Avoid reslicing unless explicitly required
* Scripts remain readable and modifiable
* Batch processing supported where possible

---

## Notes

* The scripts assume two-view acquisitions and may not generalize to other configurations without modification
* Dataset naming is now well-aware to support multiwell acquisitions
* Legacy export scripts have been removed in favor of direct dataset-based workflows

---

## References

* BigStitcher (Multiview Reconstruction):
  [https://imagej.net/plugins/multiview-reconstruction](https://imagej.net/plugins/multiview-reconstruction)

* CLIJ (GPU image processing for Fiji):
  [https://imagej.net/plugins/clij](https://imagej.net/plugins/clij)

---

If needed, a short “quickstart” section or example dataset walkthrough can be added to illustrate a minimal end-to-end workflow.


