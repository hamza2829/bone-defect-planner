import numpy as np
from scipy import ndimage as ndi
from skimage.measure import marching_cubes
import trimesh


def _spacing(spacing):
    spacing = np.asarray(spacing, dtype=float)
    if spacing.shape != (3,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError('Need three finite positive spacing values')
    return spacing


def _mask(mask):
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 3:
        raise ValueError('Mask must be 3D')
    return mask


def volume_mm3(mask, spacing):
    return float(np.count_nonzero(_mask(mask)) * np.prod(_spacing(spacing)))


def bounding_box(mask, spacing):
    spacing = _spacing(spacing)
    indices = np.argwhere(_mask(mask))
    if not len(indices):
        raise ValueError('Empty mask has no bounding box')
    lo, hi = indices.min(axis=0), indices.max(axis=0) + 1
    return dict(min_index=lo.tolist(), max_index_exclusive=hi.tolist(),
                lower_mm=((lo - .5) * spacing).tolist(), upper_mm=((hi - .5) * spacing).tolist(),
                size_mm=((hi - lo) * spacing).tolist())


def dice(a, b):
    a, b = _mask(a), _mask(b)
    if a.shape != b.shape:
        raise ValueError('Dice masks must have matching shapes')
    total = np.count_nonzero(a) + np.count_nonzero(b)
    return float(2 * np.count_nonzero(a & b) / total) if total else 1.0


def segment(data, spacing, threshold=400., closing_mm=.8):
    """Intensity threshold, physical-radius closing, then largest 6-connected component."""
    spacing = _spacing(spacing)
    data = np.asarray(data)
    if data.ndim != 3 or not np.isfinite(data).all():
        raise ValueError('Need a finite 3D intensity volume')
    if not np.isfinite(threshold) or not np.isfinite(closing_mm) or closing_mm < 0:
        raise ValueError('Invalid segmentation parameter')
    mask = data >= threshold
    if closing_mm > 0:
        half = np.ceil(closing_mm / spacing).astype(int)
        grids = np.ogrid[tuple(slice(-h, h + 1) for h in half)]
        footprint = sum((grid * s) ** 2 for grid, s in zip(grids, spacing)) <= closing_mm ** 2
        # Pad so closing does not remove border-touching components silently.
        pad = [(int(h), int(h)) for h in half]
        padded = np.pad(mask, pad)
        closed = ndi.binary_closing(padded, structure=footprint)
        mask = closed[tuple(slice(h, -h) if h else slice(None) for h in half)]
    labels, n = ndi.label(mask)
    if not n:
        return np.zeros(data.shape, dtype=bool)
    counts = np.bincount(labels.ravel())
    counts[0] = 0
    return labels == counts.argmax()


def mesh_from_mask(mask, spacing, origin=(0., 0., 0.), direction=None):
    mask = _mask(mask)
    spacing = _spacing(spacing)
    if not mask.any():
        raise ValueError('Cannot mesh an empty mask')
    # Zero padding closes surfaces even when a mask touches the image boundary.
    vertices, faces, _, _ = marching_cubes(np.pad(mask, 1).astype(np.float32), level=.5,
                                          spacing=tuple(spacing), allow_degenerate=False)
    vertices -= spacing
    direction = np.eye(3) if direction is None else np.asarray(direction).reshape(3, 3)
    vertices = vertices @ direction.T + np.asarray(origin)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    # Preserve relative winding of enclosed cavity surfaces. Per-body inversion
    # would incorrectly add cavity volumes instead of subtracting them.
    mesh.fix_normals(multibody=False)
    return mesh


def mesh_metrics(mesh):
    valid = bool(mesh.is_volume)
    return dict(volume_mm3=float(mesh.volume) if valid else None,
                surface_area_mm2=float(mesh.area), watertight=bool(mesh.is_watertight),
                valid_volume=valid, vertices=len(mesh.vertices), faces=len(mesh.faces))
