# Ordered reproduction and screenshot guide

Use only the supplied phantom or the attributed public sample. This is a learning project, not a tool for planning an actual procedure. Screenshots below are a capture checklist. The two generated figures already exist, but no terminal or GitHub screenshots are fabricated.

## 1. Open the project

Extract the source ZIP if using it. Open the `bone-defect-planner` folder in your editor. Open a terminal in that exact folder. Confirm `py -3.12 --version` on Windows, or `python3.12 --version` on Linux/macOS.

**Screenshot:** `01-project-structure.png`, showing `src/`, `tests/`, `docs/`, `pyproject.toml` and Python version.

## 2. Install in a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

You do not need to activate the environment. Installation requires internet access. If you lack Python 3.12, install it before continuing. Docker is not used.

**Screenshot:** `02-installation.png`, showing the successful project installation. Do not claim installation succeeded if pip failed.

## 3. Run tests

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

For a restricted temporary directory use:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-temp
```

Use `.venv/bin/python` on Linux/macOS. The current local result is 21 passing tests. Deprecation warnings may appear from scikit-image with NumPy. They are not hidden. Do not alter expected results just to make a test pass.

**Screenshot:** `03-pytest.png`, including the full pass/fail summary and warning count.

## 4. Run the offline phantom pipeline

```powershell
.\.venv\Scripts\python.exe -m bone_defect_planner demo --output artifacts --figures docs
```

The command generates and writes three intensity volumes, reloads them with SimpleITK, segments them, fits modules, exports meshes and writes results. No download occurs. It also writes truth and segmentation masks as NIfTI files so you can inspect them in a compatible viewer.

**Screenshot:** `04-phantom-results.png`, showing all three console result lines, including the low-contrast degradation and poor thin-defect fit.

## 5. Inspect a slice

Open `docs/slice-overlay.png`. The green overlay is segmentation. Red is the known defect mask. The axis labels are image-axis millimetres. The synthetic cylinder is hollow, with a lateral cut-out, and has no anatomical realism claim.

**Screenshot:** `05-slice-overlay.png`, the full figure with title and axis labels. The original PNG itself can also serve as the figure artifact.

## 6. Inspect the mesh and module geometry

Open `docs/mesh-render.png`. The remaining segmented bone is gray, the known defect red, and the selected voxel module union green. Inspect `artifacts/nominal-bone.stl`, `nominal-defect.stl` and `nominal-modules.stl` in any installed STL viewer if desired. Interpret units as mm; STL does not store reliable units.

**Screenshot:** `06-mesh-render.png`, showing the full exported render. If using an STL viewer, also save `06b-stl-viewer.png` with the imported filename visible. No special viewer is needed for tests.

## 7. Inspect metrics and the block catalogue

Open `src/bone_defect_planner/blocks.json` and `artifacts/results.json` beside each other. Confirm six catalogue types, selected IDs/poses, coverage, overshoot, remaining-bone overlap and rejected 2 mm thin plate. The 3 mm minimum thickness rule is a toy geometric gate. The module union can contain interpenetrating blocks and is not a manufacturable assembly.

Open `artifacts/results.csv` as text or in a spreadsheet viewer. Keep every row, including `thin_defect`. Never report just the nominal case. Full module union volume and overlap are in JSON.

**Screenshot:** `07-module-fit.png`, showing the poor thin-defect result and thickness rejection. **Screenshot:** `08-results-table.png`, showing all three cases and their measured numbers.

## 8. Optionally reproduce the public CT demonstration

This requires one public data download. Review [DATA.md](DATA.md) first.

```powershell
.\.venv\Scripts\python.exe tools/fetch_public_ct.py
.\.venv\Scripts\python.exe -m bone_defect_planner public-demo data/downloads/CT-brain.nrrd --output artifacts/public-ct
```

The download script verifies the published SHA256. The public demonstration segments a high-intensity component and artificially removes a small surface ROI. It does not detect a real defect, and has no labels for Dice. The result is already recorded in `artifacts/public-ct/results.json`. This command can produce a large STL. The raw CT and derived large mesh stay outside the source archive.

**Screenshot:** `09-public-ct.png`, showing checksum verification and the resulting metrics. Keep the no-ground-truth limitation in the caption.

## 9. Push to your own GitHub repository

The project is now hosted at [hamza2829/bone-defect-planner](https://github.com/hamza2829/bone-defect-planner). If you are recreating it under another account, create an empty GitHub repository named `bone-defect-planner`, then from this project folder run:

```powershell
git init
git add .
git commit -m "Add educational bone defect geometry prototype"
git branch -M main
```

Copy the exact remote URL from your repository's **Code** menu. Add it with `git remote add origin <your-repository-url>` and then `git push -u origin main`. Replace the placeholder with your actual URL. If a remote already exists, inspect it with `git remote -v` before changing it. Keep `.venv`, downloaded CT, caches and large generated volumes excluded by `.gitignore`.

**Screenshot:** `10-github-repository.png`, showing README, source, tests, figures and workflow in the repository. Do not capture credentials or tokens.

## 10. Verify the actual GitHub Actions run

Open the GitHub repository > **Actions** > **Tests and phantom evaluation**. The push should start a run. Alternatively choose **Run workflow** on the default branch. Wait for the conclusion. Open the run and inspect **Run tests** and **Run download-free phantom evaluation**, then download the `phantom-evaluation` artifact.

**Screenshot:** `11-github-actions.png`, showing the real run URL, branch/commit and conclusion. If it fails, keep the failure and repair the cause. A workflow file in the repo does not prove a run passed.

The first [verified successful run](https://github.com/hamza2829/bone-defect-planner/actions/runs/40031257920) is recorded in `verification.md`. For later runs, record the new URL, tested commit and conclusion. Do not change the numerical table unless the new measured output differs. Explain any differences rather than replacing failures with expectations.

## 11. Final portfolio check

Confirm README links resolve, both figures display, results include failures, data attribution remains present and the medical disclaimer is visible. Use the three German CV bullets in README only while they match actual work. The current bullets include locally and remotely passed tests, supported by the recorded GitHub run. They do not claim medical validation.

Store genuine captures under `docs/screenshots/` when you take them. None is required to run the project. Do not add a screenshot to the evidence list until it exists.
