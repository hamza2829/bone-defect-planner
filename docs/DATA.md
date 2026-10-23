# Data sources and permissions

This is a learning prototype. It is not medical software. The public scan is an optional input example. Quantitative accuracy evaluation uses generated phantoms with known masks.

## Generated phantom

Source: this repository's [`make_phantom`](../src/bone_defect_planner/phantom.py) function. The generator and its generated synthetic volumes and masks are original project assets covered by the repository's [MIT license](../LICENSE). No patient records or external image assets are used to generate them.

The phantom is a hollow cylinder with an outer radius of 14 mm, an inner radius of 8 mm and a cut-out on one side. It is a geometric stand-in for a bone, not a model of human tissue. The array has 80 by 80 by 64 voxels with spacing of 0.6 by 0.6 by 1.0 mm. Seed 7 makes the added noise repeatable. A small disconnected bright artifact tests connected-component cleanup.

The three cases are `nominal`, `low_contrast` and `thin_defect`. The low-contrast case deliberately makes threshold segmentation harder. The thin-defect case tests a narrow region that the available modules may fit poorly. Tests and CI generate their inputs locally and require no scan download.

The generator supplies the intact mask, remaining-bone mask and removed-defect mask. Ground-truth volumes are counts of these known voxels multiplied by voxel volume. They are digital reference volumes, not exact continuous-cylinder volumes. Module fitting uses the known defect mask. The prototype does not infer a missing anatomical shape from a scan.

## Optional public CT sample

| Item | Value |
| --- | --- |
| Dataset | CT portion of 3D Slicer's CT-MR Brain sample |
| Local filename | `data/downloads/CT-brain.nrrd` |
| Format | NRRD |
| Verified file size | 16,366,792 bytes |
| SHA256 | `6a5b6caccb76576a863beb095e3bfb910c50ca78f4c9bf043aa42f976cfa53d1` |
| Host | Official `Slicer/SlicerTestingData` GitHub release assets |
| Permission | Dataset-specific unrestricted-use statement from 3D Slicer |

[Direct CT download](https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/6a5b6caccb76576a863beb095e3bfb910c50ca78f4c9bf043aa42f976cfa53d1).

The official [Slicer 5.6.2 sample registration](https://github.com/Slicer/Slicer/blob/v5.6.2/Modules/Scripted/SampleData/SampleData.py) maps this checksum to `CT-brain.nrrd` in the CT-MR Brain sample. Its acknowledgement states that CT-MR Brain was donated by the people shown in the images and may be used without restrictions. This dataset permission is separate from the Slicer software license. The source does not name a separate SPDX or Creative Commons license for this sample, so this project does not label the scan MIT or BSD. Attribution is retained here to the 3D Slicer project and the people who donated the sample. The [official release asset listing](https://github.com/Slicer/SlicerTestingData/releases/expanded_assets/SHA256) also identifies the checksum and displays a rounded size of 15.6 MB.

The sample was downloaded for this project, its byte count recorded, and its SHA256 verified. The `public-demo` command was run with a threshold of 400 in the stored image intensity units. HU calibration was not independently established. This is a 3D skull scan, not a long-bone defect dataset.

No bone segmentation ground truth or defect annotation is supplied by the cited sample registration. The public demonstration selects a small surface region from the threshold result and marks its removal as an artificial defect. This region is created by code. It is not a diagnosis, expert annotation or real patient defect. No Dice score or clinical accuracy claim is reported for this scan.

## Download and reproduce

From the repository root, after installing the project:

```powershell
python tools/fetch_public_ct.py
python -m bone_defect_planner public-demo data/downloads/CT-brain.nrrd --threshold 400 --output artifacts/public-ct
```

[`tools/fetch_public_ct.py`](../tools/fetch_public_ct.py) fetches only the optional CT file and verifies the expected SHA256 before accepting it. It also verifies an existing cached file. A mismatched file raises an error. This download is not needed for `pytest` or the phantom demonstration.

SimpleITK loads the NRRD metadata. Array axes are converted to x, y, z, and spacing, origin and direction are retained. Physical measurements assume the sample coordinates use millimetres. The [SimpleITK geometry documentation](https://simpleitk.readthedocs.io/en/master/fundamentalConcepts.html) explains why spacing, origin and direction matter and why consistent units are the developer's responsibility.

## What is included

The raw CT is not bundled. `data/downloads/` is ignored by Git. The source archive also excludes the large derived public-scan STL and artificial-defect mask. The public run's `artifacts/public-ct/results.json` is included as a record of the actual demonstration. Re-run the commands above to recreate the excluded files.

Phantom code, tests and evaluation outputs are included. The real-scan demonstration supports only the claim that the loading, threshold, artificial-defect, mesh and module-selection paths executed on this public input. It does not establish anatomical correctness, biomechanical safety or suitability for patient care.
