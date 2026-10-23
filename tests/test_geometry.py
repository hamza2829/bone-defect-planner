"""Physical geometry checks on simple arrays with independently known answers."""

import numpy as np
import pytest

from bone_defect_planner.geometry import bounding_box, dice, mesh_from_mask, volume_mm3


def test_volume_uses_all_three_spacing_values():
    mask = np.zeros((4, 5, 6), dtype=bool)
    mask[1:3, 1:4, 2:6] = True
    assert volume_mm3(mask, (0.5, 2.0, 3.0)) == pytest.approx(72.0)


def test_bounding_box_keeps_xyz_order_and_half_voxel_faces():
    mask = np.zeros((5, 7, 9), dtype=bool)
    mask[1:3, 2:6, 3:8] = True
    box = bounding_box(mask, (0.5, 2.0, 3.0))
    assert box["min_index"] == [1, 2, 3]
    assert box["max_index_exclusive"] == [3, 6, 8]
    assert box["lower_mm"] == pytest.approx([0.25, 3.0, 7.5])
    assert box["upper_mm"] == pytest.approx([1.25, 11.0, 22.5])
    assert box["size_mm"] == pytest.approx([1.0, 8.0, 15.0])


def test_empty_volume_is_zero_but_empty_bbox_and_mesh_are_undefined():
    empty = np.zeros((4, 5, 6), dtype=bool)
    assert volume_mm3(empty, (1.0, 1.0, 1.0)) == 0.0
    with pytest.raises(ValueError):
        bounding_box(empty, (1.0, 1.0, 1.0))
    with pytest.raises(ValueError):
        mesh_from_mask(empty, (1.0, 1.0, 1.0))


@pytest.mark.parametrize("spacing", [(0, 1, 1), (-1, 1, 1), (1, 1), (1, np.nan, 1)])
def test_volume_rejects_invalid_spacing(spacing):
    with pytest.raises(ValueError):
        volume_mm3(np.ones((2, 2, 2), dtype=bool), spacing)


def test_dice_has_known_overlap_and_empty_convention():
    a = np.zeros((2, 3, 4), dtype=bool)
    b = np.zeros_like(a)
    a[0, 0, :3] = True
    b[0, 0, 1:] = True
    assert dice(a, b) == pytest.approx(2.0 / 3.0)
    assert dice(a, a) == 1.0
    assert dice(np.zeros_like(a), np.zeros_like(a)) == 1.0
    assert dice(a, np.zeros_like(a)) == 0.0


def test_mesh_is_closed_positive_and_uses_physical_coordinates():
    mask = np.zeros((8, 9, 10), dtype=bool)
    mask[2:6, 3:7, 2:8] = True
    mesh = mesh_from_mask(mask, (0.5, 2.0, 3.0), origin=(10, -2, 5))
    assert mesh.is_watertight
    assert mesh.volume > 0
    assert mesh.area > 0
    np.testing.assert_allclose(mesh.bounds, [[10.75, 3.0, 9.5], [12.75, 11.0, 27.5]])


def test_mesh_padding_closes_a_component_touching_array_edge():
    mask = np.zeros((5, 6, 7), dtype=bool)
    mask[:3, 1:5, 1:6] = True
    mesh = mesh_from_mask(mask, (1, 1, 1))
    assert mesh.is_watertight
    assert mesh.volume > 0
    assert mesh.bounds[0, 0] == pytest.approx(-0.5)


def test_enclosed_cavity_subtracts_mesh_volume_instead_of_adding_it():
    solid = np.zeros((18, 18, 18), dtype=bool)
    solid[3:15, 3:15, 3:15] = True
    cavity = np.zeros_like(solid)
    cavity[7:11, 7:11, 7:11] = True
    outer_mesh = mesh_from_mask(solid, (1, 1, 1))
    hollow_mesh = mesh_from_mask(solid & ~cavity, (1, 1, 1))
    cavity_mesh = mesh_from_mask(cavity, (1, 1, 1))
    assert hollow_mesh.is_watertight
    assert hollow_mesh.is_volume
    assert 0 < hollow_mesh.volume < outer_mesh.volume
    removed = outer_mesh.volume - hollow_mesh.volume
    assert removed == pytest.approx(cavity_mesh.volume)
    # Marching cubes rounds binary voxel corners: about 58.667 versus 64 mm3.
    assert removed == pytest.approx(4 ** 3, rel=0.1)
