# Reproducible Fiji environment for dOPM

This repository has been tested with a Fiji 2.9.0 environment reconstructed from the official Fiji archive plus a small set of pinned compatibility components.

The purpose of this file is to make the environment recoverable even if the installer scripts are not used.

## Base Fiji

Windows 64-bit:

- `https://downloads.imagej.net/fiji/releases/2.9.0/fiji-2.9.0-win64.zip`

Linux x86_64:

- `https://downloads.imagej.net/fiji/releases/2.9.0/fiji-2.9.0-linux64.zip`

Extract the archive so that you have a normal `Fiji.app` directory.

## Pinned compatibility components

Replace any conflicting versions and install the following exact files.

| Component | Version | Destination in Fiji.app | Source |
|---|---:|---|---|
| BigStitcher | 0.8.3 | `plugins/Big_Stitcher-0.8.3.jar` | `https://sites.imagej.net/BigStitcher/plugins/Big_Stitcher-0.8.3.jar-20211130143242` |
| BigDataViewer core | 10.2.0 | `jars/bigdataviewer-core-10.2.0.jar` | `https://sites.imagej.net/Fiji/jars/bigdataviewer-core-10.2.0.jar-20210222164216` |
| BigDataViewer vistools | 1.0.0-beta-28 | `jars/bigdataviewer-vistools-1.0.0-beta-28.jar` | `https://sites.imagej.net/Fiji/jars/bigdataviewer-vistools-1.0.0-beta-28.jar-20210222164216` |
| BigDataViewer Fiji | 6.2.1 | `plugins/bigdataviewer_fiji-6.2.1.jar` | `https://sites.imagej.net/Fiji/plugins/bigdataviewer_fiji-6.2.1.jar-20210222164216` |
| Multiview Reconstruction | 0.11.5 | `plugins/multiview_reconstruction-0.11.5.jar` | `https://sites.imagej.net/BigStitcher/plugins/multiview_reconstruction-0.11.5.jar-20211201080417` |
| SPIM Registration compatibility JAR | 0.0.1 | `plugins/SPIM_Registration-0.0.1.jar` | `https://sites.imagej.net/BigStitcher/plugins/SPIM_Registration-0.0.1.jar-20180411172036` |
| CLIJ | 1.9.0.1 | `plugins/clij_-1.9.0.1.jar` | `https://sites.imagej.net/clij/plugins/clij_-1.9.0.1.jar-20210613085830` |
| CLIJ2 | 2.5.1.4 | `plugins/clij2_-2.5.1.4.jar` | `https://sites.imagej.net/clij2/plugins/clij2_-2.5.1.4.jar-20211023172143` |
| CLIJ ClearCL | 2.5.0.1 | `jars/clij-clearcl-2.5.0.1.jar` | `https://repo1.maven.org/maven2/net/haesleinhuepf/clij-clearcl/2.5.0.1/clij-clearcl-2.5.0.1.jar` |
| CLIJ core | 1.8.1.1 | `jars/clij-core-1.8.1.1.jar` | `https://repo1.maven.org/maven2/net/haesleinhuepf/clij-core/1.8.1.1/clij-core-1.8.1.1.jar` |
| CLIJ coremem | 2.3.0.4 | `jars/clij-coremem-2.3.0.4.jar` | `https://repo1.maven.org/maven2/net/haesleinhuepf/clij-coremem/2.3.0.4/clij-coremem-2.3.0.4.jar` |
| JOCL | 2.0.2 | `jars/jocl-2.0.2.jar` | `https://repo1.maven.org/maven2/org/jocl/jocl/2.0.2/jocl-2.0.2.jar` |

Before copying these files, remove older/conflicting copies matching these patterns:

```text
plugins/Big_Stitcher*.jar
plugins/BigStitcher*.jar
plugins/multiview_reconstruction*.jar
plugins/SPIM_Registration*.jar
plugins/bigdataviewer_fiji*.jar
jars/bigdataviewer-core*.jar
jars/bigdataviewer-vistools*.jar
jars/bigdataviewer_fiji*.jar
plugins/clij_*.jar
plugins/clij2_*.jar
jars/clij-clearcl*.jar
jars/clij-core-*.jar
jars/clij-coremem*.jar
jars/jocl-*.jar
```

The exact `multiview_reconstruction-0.11.5.jar` matters because this dOPM workflow calls the historical BigStitcher/ImageJ command named `Fuse` directly.

The BigDataViewer versions are pinned because newer bundled BDV core versions (for example 10.4.3) can break the historical BigStitcher Data Explorer with `NoSuchMethodError` errors even when the processing scripts themselves still run.

## Recommended repository setup

The repository now includes one-step bootstrap scripts:

- Windows: `installers/setup_dOPM_windows.bat`
- Linux x86_64: `installers/setup_dOPM_linux.sh`

They create the generated Fiji environment at the repository root:

```text
Fiji_2.9.0_dOPM/Fiji.app
```

and then copy all repository-root `.py` files to `Fiji.app/plugins/Scripts/dOPM`. The generated Fiji directory is ignored by Git.

The lower-level `build_dOPM_Fiji_windows.bat` and `build_dOPM_Fiji_linux.sh` scripts only build the Fiji environment.

## Install the dOPM scripts

Copy the production Python/Jython scripts from this repository to:

```text
Fiji.app/plugins/Scripts/dOPM
```

The scripts run inside Fiji's Jython environment. A separate CPython installation is not required.

## Validation state

The faithful end-to-end validator in `validation/Test_dOPM_EndToEnd_v3_faithful.py` has been used to exercise the production-order workflow:

```text
bead XML creation
-> calibration
-> dOPM geometric transforms
-> bead registration
-> HDF5 resave
-> bead-derived bounding box
-> sample dataset creation across well groups
-> transfer of bead registration to samples
-> common bounding box transfer
-> fused TIFF export
-> CLIJ2 XYZ MIP generation
```

The validated test included both bead naming styles (`dataset.xml` and a well-suffixed bead dataset), and sample data containing multiple well groups.

Do not update Fiji through `Help > Update...` before reproducing the validation, because doing so changes the dependency set.

## Linux/OpenCL note

The Fiji/Jython and BigStitcher portions are Java-based and the Linux builder installs the same pinned Java/plugin versions. CLIJ2 MIP generation also depends on a working system OpenCL runtime and GPU/driver configuration, so that part still needs to be validated on the target Linux machine.
