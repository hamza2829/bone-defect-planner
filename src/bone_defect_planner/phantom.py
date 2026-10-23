"""Synthetic annular cylinder, not a simulation of human tissue."""
import numpy as np
from .io import Volume


def make_phantom(case='nominal', seed=7):
    if case not in {'nominal', 'low_contrast', 'thin_defect'}:
        raise ValueError('Unknown phantom case')
    spacing = (.6, .6, 1.0)
    shape = (80, 80, 64)
    x, y, z = np.ogrid[:shape[0], :shape[1], :shape[2]]
    x, y, z = (x - 39.5) * spacing[0], (y - 39.5) * spacing[1], z * spacing[2]
    r2 = x*x + y*y
    intact = (r2 <= 14**2) & (r2 >= 8**2) & (z >= 8) & (z <= 55)
    width = 2.0 if case == 'thin_defect' else 12.0
    defect = intact & (x >= 8) & (abs(y) <= 6) & (abs(z - 31) <= width/2)
    bone = intact & ~defect
    rng = np.random.default_rng(seed)
    bone_intensity, noise = (440, 180) if case == 'low_contrast' else (950, 35)
    data = np.where(bone, bone_intensity, 60).astype(np.float32)
    data += rng.normal(0, noise, shape).astype(np.float32)
    # Disconnected high-intensity artifact exercises largest-component cleanup.
    data[3:5, 3:5, 3:5] = 1100
    return dict(volume=Volume(data, spacing), bone_truth=bone, defect_truth=defect,
                intact_truth=intact, seed=seed, case=case)
