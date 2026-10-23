# Verification scope

Actually executed locally on Windows with Python 3.12.14:

- Installed the project and its dependencies in `.venv`.
- Ran the three-case phantom pipeline, including writing and reloading NIfTI volumes with SimpleITK.
- Ran pytest with a workspace-local temporary directory: 21 tests passed.
- Downloaded the optional public CT, 16,366,792 bytes, and verified its published SHA256.
- Ran the public CT artificial-defect demonstration. No public-data Dice or true-volume claim was made.
- Exported STL geometry and checked watertightness and valid volumes in code.
- Opened and visually inspected both Matplotlib output figures.

The regression suite includes an enclosed-cavity test. It verifies that an internal cavity reduces mesh volume instead of increasing it. This catches an earlier normal-winding issue that was fixed before the reported final run.

Upstream scikit-image currently emits NumPy deprecation warnings during marching cubes. The final recorded local full test run has 64 warnings and zero failures. They are not suppressed.

Not confirmed:

- A remote GitHub Actions execution, because no destination repository has been supplied yet.
- Terminal/GitHub screenshots taken by the user. The capture checklist is in STEPS.md.
- Any diagnosis, patient-specific clinical validation, mechanical simulation, manufactured implant or medical benefit.

The workflow exists at `.github/workflows/tests.yml` and is ready for a GitHub repository. Record a real workflow run URL, commit and conclusion here after it runs. Do not present the local test result as remote CI evidence.
