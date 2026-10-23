"""Run the actual phantom pipeline without downloading any data."""

import json

import numpy as np
import pytest

from bone_defect_planner.io import Volume, save_volume
from bone_defect_planner.phantom import make_phantom
from bone_defect_planner.pipeline import run_phantom, run_volume


def test_phantom_ground_truth_and_reproducibility():
    first = make_phantom("nominal", seed=7)
    second = make_phantom("nominal", seed=7)
    np.testing.assert_array_equal(first["volume"].data, second["volume"].data)
    np.testing.assert_array_equal(first["intact_truth"], first["bone_truth"] | first["defect_truth"])
    assert not np.any(first["bone_truth"] & first["defect_truth"])
    assert first["defect_truth"].any()


def test_phantom_integration_emits_report_meshes_and_figures(tmp_path):
    output = tmp_path / "artifacts"
    figures = tmp_path / "docs"
    report = run_phantom(output_dir=output, figure_dir=figures)
    assert {case["case"] for case in report["cases"]} == {"nominal", "low_contrast", "thin_defect"}
    cases = {case["case"]: case for case in report["cases"]}
    assert cases["nominal"]["segmentation_dice"] > cases["low_contrast"]["segmentation_dice"]
    assert cases["thin_defect"]["modules"]["fit_quality"] == "poor fit"
    for case in report["cases"]:
        assert 0 <= case["segmentation_dice"] <= 1
        assert case["bone_volume_error_pct"] >= 0
        assert case["defect_volume_mm3"] > 0
        assert case["bone_mesh"]["watertight"]
        assert case["defect_mesh"]["watertight"]
        fit = case["modules"]
        assert 0 <= fit["coverage_pct"] <= 100
        assert np.isclose(fit["union_volume_mm3"], fit["covered_mm3"] + fit["overshoot_mm3"])
    assert json.loads((output / "results.json").read_text(encoding="utf-8")) == report
    assert (output / "results.csv").stat().st_size > 100
    assert len(list(output.glob("*.stl"))) >= 3
    for name in ["slice-overlay.png", "mesh-render.png"]:
        assert (figures / name).stat().st_size > 1000


def test_external_mask_pipeline_removes_marked_defect_and_preserves_spacing(tmp_path):
    data = np.zeros((20, 20, 20), dtype=np.int16)
    data[4:16, 4:16, 4:16] = 1000
    defect = np.zeros_like(data, dtype=bool)
    defect[8:12, 8:12, 8:12] = True
    spacing = (0.7, 1.2, 1.5)
    origin = (10, -20, 30)
    direction = ((0, -1, 0), (1, 0, 0), (0, 0, 1))
    input_path, mask_path = tmp_path / "sample.nii.gz", tmp_path / "defect.nii.gz"
    save_volume(Volume(data, spacing, origin, direction), input_path)
    save_volume(Volume(defect, spacing, origin, direction), mask_path)
    output = tmp_path / "external-results"
    report = run_volume(input_path, mask_path, output, threshold=400)
    voxel_volume = np.prod(spacing)
    assert report["defect_volume_mm3"] == pytest.approx(4 ** 3 * voxel_volume)
    assert report["segmentation_volume_mm3"] == pytest.approx((12 ** 3 - 4 ** 3) * voxel_volume)
    assert report["mesh"]["watertight"]
    assert report["mesh"]["valid_volume"]
    assert (output / "segmentation.stl").stat().st_size > 100
    assert json.loads((output / "results.json").read_text(encoding="utf-8")) == report
