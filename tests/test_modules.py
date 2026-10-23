"""Check block selection against geometry with a known exact solution."""

import numpy as np
import pytest

from bone_defect_planner.modules import load_catalogue, select_modules


def test_catalogue_contains_cuboids_and_cylinders():
    catalogue = load_catalogue()
    assert 5 <= len(catalogue) <= 6
    assert {item["shape"] for item in catalogue} == {"cuboid", "cylinder"}
    assert len({item["id"] for item in catalogue}) == len(catalogue)


def test_selection_is_deterministic_bounded_and_counts_union():
    defect = np.zeros((24, 24, 24), dtype=bool)
    defect[4:20, 4:20, 4:20] = True
    a = select_modules(defect, (1.0, 1.0, 1.0), max_blocks=2)
    b = select_modules(defect, (1.0, 1.0, 1.0), max_blocks=2)
    assert a["blocks"] == b["blocks"]
    assert a["coverage_pct"] == b["coverage_pct"]
    assert a["overshoot_pct"] == b["overshoot_pct"]
    np.testing.assert_array_equal(a["union_mask"], b["union_mask"])
    assert 1 <= len(a["blocks"]) <= 2
    assert 0 < a["coverage_pct"] <= 100.0
    assert a["overshoot_pct"] >= 0.0
    expected_coverage = 100.0 * np.count_nonzero(a["union_mask"] & defect) / defect.sum()
    assert a["coverage_pct"] == pytest.approx(expected_coverage)


def test_empty_defect_cannot_request_blocks():
    with pytest.raises(ValueError):
        select_modules(np.zeros((5, 5, 5), dtype=bool), (1, 1, 1))


def test_one_cube_has_an_exact_fit_without_overshoot():
    defect = np.zeros((14, 14, 14), dtype=bool)
    defect[4:10, 4:10, 4:10] = True
    cube = next(item for item in load_catalogue() if item["id"] == "cube-6")
    result = select_modules(defect, (1, 1, 1), catalogue=[cube], max_blocks=1)
    assert len(result["blocks"]) == 1
    assert result["blocks"][0]["id"] == "cube-6"
    assert result["coverage_pct"] == pytest.approx(100.0)
    assert result["overshoot_pct"] == pytest.approx(0.0)
    np.testing.assert_array_equal(result["union_mask"], defect)


def test_thickness_rule_rejects_thin_modules():
    catalogue = load_catalogue()
    defect = np.ones((8, 8, 8), dtype=bool)
    result = select_modules(defect, (1, 1, 1), catalogue=catalogue, min_thickness_mm=1000.0)
    assert result["blocks"] == []
    assert result["coverage_pct"] == 0.0
    assert len(result["rejected_thin"]) == len(catalogue)


def test_integer_face_ties_do_not_expand_a_six_mm_cube_to_seven_voxels():
    defect = np.zeros((16, 16, 16), dtype=bool)
    defect[4:11, 4:11, 4:11] = True
    cube = next(item for item in load_catalogue() if item["id"] == "cube-6")
    result = select_modules(defect, (1, 1, 1), catalogue=[cube], max_blocks=1)
    assert len(result["blocks"]) == 1
    assert result["union_mask"].sum() == 6 ** 3
    assert result["covered_mm3"] == pytest.approx(6 ** 3)
    assert result["coverage_pct"] == pytest.approx(100 * 6 ** 3 / 7 ** 3)
    assert result["overshoot_pct"] == 0
