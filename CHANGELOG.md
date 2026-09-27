# Changelog

## Bounding-box compatibility for HDF5 bead datasets - 2026-09-27

- automatic batch workflow now reads the preserved ViewSetup Z depth directly from a bead XML, so geometry-based bounding-box estimation works with HDF5/XML-only bead datasets
- retained ND2 metadata lookup as a fallback for older or unusual XML files
- added a final user prompt for raw Z depth when neither XML nor ND2 can provide it
- standalone `define_bounding_box.py` now pre-fills raw Z depth from the selected reference XML when available

## Repository bootstrap and Fiji layout - 2026-09-27

- added one-step Windows and Linux setup scripts that build Fiji when missing and deploy repository-root Jython scripts automatically
- moved generated `Fiji_2.9.0_dOPM` output from `installers/` to the repository root
- added `Fiji_2.9.0_dOPM/` to `.gitignore` so the generated Fiji application is not committed
- retained lower-level environment-only builders for users who want to install Fiji without deploying the dOPM scripts
- documented the pinned BigDataViewer compatibility stack required for BigStitcher Data Explorer / BDV viewing

## Reproducibility / automatic batch workflow draft - 2026-09

- added `automatic_batch_workflow.py`
- added faithful end-to-end production-order validation
- added a reproducible Windows Fiji 2.9.0 builder with pinned compatibility JARs
- added a Linux x86_64 builder using the same pinned Java/plugin stack
- added `FIJI_ENVIRONMENT.md` so the Fiji environment can be reconstructed manually
- changed test-data documentation to a placeholder Zenodo record pending publication
- documented multi-well batch processing, common bounding-box transfer, fusion, and MIP generation
- intentionally omitted the older long-form guide from this draft repository bundle; a replacement guide will follow after workflow finalisation
