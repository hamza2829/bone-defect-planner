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

## Verified GitHub Actions run

- Repository: [hamza2829/bone-defect-planner](https://github.com/hamza2829/bone-defect-planner).
- Run: [40031257920](https://github.com/hamza2829/bone-defect-planner/actions/runs/40031257920), conclusion **success**.
- Tested commit: `202b86d4995526902755d415df6f12ef608d4649`.
- GitHub-hosted Ubuntu runner, Python 3.12. Tests: **21 passed, 64 warnings in 4.00 seconds**.
- The offline phantom evaluation reproduced the reported rounded metrics for all three cases.
- Result and figure artifact upload succeeded: [phantom-evaluation](https://github.com/hamza2829/bone-defect-planner/actions/runs/40031257920/artifacts/12535740159).
- The test job completed in 41 seconds. The optional public CT was not downloaded in CI.

GitHub emitted runner/action deprecation notices. They did not fail this run. Future runs may require action-version or runner updates.

Upstream scikit-image currently emits NumPy deprecation warnings during marching cubes. The final recorded local full test run has 64 warnings and zero failures. They are not suppressed.

Not confirmed:

- Terminal/GitHub screenshots taken by the user. The capture checklist is in STEPS.md.
- Any diagnosis, patient-specific clinical validation, mechanical simulation, manufactured implant or medical benefit.

The workflow is `.github/workflows/tests.yml`. The run above is remote CI evidence for its recorded commit. Later documentation updates do not change that tested implementation.
