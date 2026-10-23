"""Deterministic greedy voxel packing. No structural or implant model."""
import json
from itertools import permutations, product
from pathlib import Path
import numpy as np
from .geometry import _mask, _spacing, bounding_box


def load_catalogue(path=None):
    path = Path(path) if path else Path(__file__).with_name('blocks.json')
    blocks = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(blocks, list) or not blocks:
        raise ValueError('Catalogue must be a nonempty list')
    ids = set()
    for block in blocks:
        if not block.get('id') or block['id'] in ids:
            raise ValueError('Every block needs a unique ID')
        ids.add(block['id'])
        if block.get('shape') == 'cuboid':
            dims = np.asarray(block['size_mm'], dtype=float)
        elif block.get('shape') == 'cylinder':
            dims = np.asarray([block['diameter_mm'], block['diameter_mm'], block['height_mm']], dtype=float)
        else:
            raise ValueError('Unsupported block shape')
        if dims.shape != (3,) or not np.isfinite(dims).all() or np.any(dims <= 0):
            raise ValueError('Module dimensions must be finite and positive')
    return blocks


def _orientations(block):
    if block['shape'] == 'cuboid':
        return [('xyz', np.array(d)) for d in sorted(set(permutations(block['size_mm'])))]
    d, h = block['diameter_mm'], block['height_mm']
    return [(axis, np.array([h if i == a else d for i in range(3)])) for a, axis in enumerate('xyz')]


def _indices(shape, spacing, block, center, orientation, dimensions):
    """Rasterize voxel centres; count each selected voxel once, including overshoot."""
    lower, upper = center - dimensions / 2, center + dimensions / 2
    if np.any(lower < -.5 * spacing) or np.any(upper > (np.array(shape) - .5) * spacing):
        return np.array([], dtype=np.int64)
    lo = np.maximum(0, np.ceil(lower / spacing - 1e-8).astype(int))
    # Use half-open bounding intervals so exact dimension ties do not add a voxel.
    hi = np.minimum(shape, np.ceil(upper / spacing - 1e-8).astype(int))
    if np.any(hi <= lo):
        return np.array([], dtype=np.int64)
    coords = np.meshgrid(*[np.arange(a, b) for a, b in zip(lo, hi)], indexing='ij')
    delta = [c * s - m for c, s, m in zip(coords, spacing, center)]
    if block['shape'] == 'cylinder':
        axis = 'xyz'.index(orientation)
        radial = sum(delta[i] ** 2 for i in range(3) if i != axis)
        keep = (radial <= (block['diameter_mm'] / 2) ** 2 + 1e-8) & (np.abs(delta[axis]) <= block['height_mm'] / 2 + 1e-8)
    else:
        keep = np.ones(coords[0].shape, dtype=bool)
    return np.ravel_multi_index(tuple(c[keep] for c in coords), shape)


def select_modules(defect, spacing, catalogue=None, max_blocks=4, min_thickness_mm=3.0):
    defect = _mask(defect)
    spacing = _spacing(spacing)
    if not defect.any():
        raise ValueError('Cannot fit an empty defect')
    if not isinstance(max_blocks, int) or isinstance(max_blocks, bool) or max_blocks < 1:
        raise ValueError('max_blocks must be a positive integer')
    if not np.isfinite(min_thickness_mm) or min_thickness_mm <= 0:
        raise ValueError('Minimum thickness must be positive')
    catalogue = load_catalogue() if catalogue is None else catalogue
    bbox = bounding_box(defect, spacing)
    lower, upper = np.array(bbox['lower_mm']), np.array(bbox['upper_mm'])
    # Bounded lattice search, at most 5 anchors per axis plus exact bbox centre.
    anchors = [np.unique(np.r_[np.linspace(lo + s/2, hi - s/2, min(5, max(1, int((hi-lo)/3)+1))), (lo+hi)/2])
               for lo, hi, s in zip(lower, upper, spacing)]
    target = defect.ravel()
    candidates, rejected = [], []
    for block in catalogue:
        orientations = _orientations(block)
        thickness = float(min(orientations[0][1]))
        if thickness < min_thickness_mm:
            rejected.append(dict(id=block['id'], thickness_mm=thickness, reason='below minimum solid-module thickness'))
            continue
        for orientation, dims in orientations:
            for point in product(*anchors):
                center = np.asarray(point)
                indices = _indices(defect.shape, spacing, block, center, orientation, dims)
                if indices.size and target[indices].any():
                    candidates.append((block, orientation, dims, center, indices))
    occupied = np.zeros(target.shape, dtype=bool)
    selected = []
    sum_voxels = 0
    for _ in range(max_blocks):
        best, best_key = None, (0, 0, 0)
        for i, (_, _, _, _, indices) in enumerate(candidates):
            fresh = indices[~occupied[indices]]
            hits = np.count_nonzero(target[fresh])
            outside = len(fresh) - hits
            # Penalize each new outside-target voxel equally to a newly covered voxel.
            key = (hits - outside, -outside, hits)
            if hits and key > best_key:
                best, best_key = i, key
        if best is None:
            break
        block, orientation, dims, center, indices = candidates.pop(best)
        occupied[indices] = True
        sum_voxels += len(indices)
        selected.append(dict(id=block['id'], shape=block['shape'], center_mm=center.tolist(),
                             orientation=orientation, dimensions_mm=dims.tolist(),
                             minimum_thickness_mm=float(min(dims))))
        if np.count_nonzero(occupied & target) / np.count_nonzero(target) >= .95:
            break
    hits = int(np.count_nonzero(occupied & target))
    outside = int(np.count_nonzero(occupied & ~target))
    n = int(np.count_nonzero(target))
    voxel = float(np.prod(spacing))
    return dict(coverage_pct=100 * hits / n, overshoot_pct=100 * outside / n,
                covered_mm3=hits*voxel, overshoot_mm3=outside*voxel,
                union_volume_mm3=float(occupied.sum()*voxel),
                overlapping_modules_mm3=float((sum_voxels-occupied.sum())*voxel),
                blocks=selected, rejected_thin=rejected, union_mask=occupied.reshape(defect.shape),
                minimum_thickness_rule_mm=min_thickness_mm,
                thickness_check='pass' if selected else 'no modules selected',
                fit_quality='acceptable demo fit' if 100*hits/n >= 90 and 100*outside/n <= 20 else 'poor fit',
                objective='greedy new covered voxels minus new overshoot voxels; not a global optimum')
