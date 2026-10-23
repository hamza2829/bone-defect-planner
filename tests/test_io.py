"""Roundtrip an anisotropic volume with a non-identity physical transform."""

import numpy as np

from bone_defect_planner.io import Volume, load_volume, save_volume


def test_nifti_roundtrip_preserves_array_and_geometry(tmp_path):
    source = Volume(
        data=np.arange(4 * 5 * 6, dtype=np.int16).reshape(4, 5, 6),
        spacing=(0.7, 1.2, 2.5),
        origin=(13.0, -7.0, 4.5),
        direction=((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    )
    path = tmp_path / "anisotropic.nii.gz"
    save_volume(source, path)
    restored = load_volume(path)
    np.testing.assert_array_equal(restored.data, source.data)
    np.testing.assert_allclose(restored.spacing, source.spacing, atol=1e-6)
    np.testing.assert_allclose(restored.origin, source.origin, atol=1e-6)
    np.testing.assert_allclose(restored.direction, source.direction, atol=1e-6)
