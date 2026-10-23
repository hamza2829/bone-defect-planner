import csv
import json
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path.cwd() / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from .geometry import segment, volume_mm3, bounding_box, dice, mesh_from_mask, mesh_metrics
from .io import Volume, save_volume, load_volume
from .phantom import make_phantom
from .modules import select_modules


def _overlay(volume, segmentation, defect, path):
    k = int(np.argwhere(defect)[:, 2].mean())
    extent = [-volume.spacing[0]/2, (volume.data.shape[0]-.5)*volume.spacing[0],
              -volume.spacing[1]/2, (volume.data.shape[1]-.5)*volume.spacing[1]]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(volume.data[:, :, k].T, origin='lower', cmap='gray', extent=extent, vmin=0, vmax=1100)
    ax.imshow(np.ma.masked_where(~segmentation[:, :, k].T, segmentation[:, :, k].T), origin='lower',
              cmap=matplotlib.colors.ListedColormap(['#16c79a']), alpha=.35, extent=extent, vmin=0, vmax=1)
    ax.imshow(np.ma.masked_where(~defect[:, :, k].T, defect[:, :, k].T), origin='lower',
              cmap=matplotlib.colors.ListedColormap(['#ff675c']), alpha=.8, extent=extent, vmin=0, vmax=1)
    ax.set(xlabel='x (mm, image axes)', ylabel='y (mm, image axes)',
           title=f'Learning phantom, slice z={k*volume.spacing[2]:g} mm\nGreen: segmentation. Red: known defect.')
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _render(bone_mesh, defect_mesh, module_mesh, path):
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection='3d')
    for mesh, color, alpha in [(bone_mesh, '#c4cbd1', .18), (defect_mesh, '#ff675c', .5), (module_mesh, '#00a58b', .8)]:
        if mesh is None:
            continue
        collection = Poly3DCollection(mesh.triangles, facecolor=color, edgecolor='none', alpha=alpha, rasterized=True)
        ax.add_collection3d(collection)
    lo, hi = bone_mesh.bounds
    ax.set(xlim=(lo[0]-2, hi[0]+2), ylim=(lo[1]-2, hi[1]+2), zlim=(lo[2]-2, hi[2]+2),
           xlabel='x (mm)', ylabel='y (mm)', zlabel='z (mm)',
           title='Educational geometry only\nGray: bone. Red: defect. Green: selected voxel modules.')
    ax.set_box_aspect(hi-lo)
    ax.view_init(elev=23, azim=-35)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run_phantom(output_dir=Path('artifacts'), figure_dir=Path('docs')):
    output_dir, figure_dir = Path(output_dir), Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for case in ('nominal', 'low_contrast', 'thin_defect'):
        phantom = make_phantom(case)
        original = phantom['volume']
        volume_path = output_dir / f'{case}-volume.nii.gz'
        save_volume(original, volume_path)
        volume = load_volume(volume_path)
        segmentation = segment(volume.data, volume.spacing)
        defect = phantom['defect_truth']
        for name, mask in [('segmentation', segmentation), ('bone-truth', phantom['bone_truth']), ('defect-truth', defect)]:
            save_volume(Volume(mask,volume.spacing,volume.origin,volume.direction), output_dir / f'{case}-{name}.nii.gz')
        # Known phantom defect is used for fitting. It is not inferred from segmentation.
        fit = select_modules(defect, volume.spacing)
        union = fit.pop('union_mask')
        fit['bone_overlap_mm3'] = volume_mm3(union & phantom['bone_truth'], volume.spacing)
        bone_mesh = mesh_from_mask(segmentation, volume.spacing, volume.origin, volume.direction)
        defect_mesh = mesh_from_mask(defect, volume.spacing, volume.origin, volume.direction)
        bone_mesh.export(output_dir / f'{case}-bone.stl')
        defect_mesh.export(output_dir / f'{case}-defect.stl')
        module_mesh = mesh_from_mask(union, volume.spacing) if union.any() else None
        if module_mesh is not None:
            module_mesh.export(output_dir / f'{case}-modules.stl')
        truth_volume = volume_mm3(phantom['bone_truth'], volume.spacing)
        segmented_volume = volume_mm3(segmentation, volume.spacing)
        # Nominal analytic shell volume is intentionally distinct from digital truth.
        analytic_shell = float(np.pi * (14**2 - 8**2) * 48)
        record = dict(case=case, seed=7, shape_xyz=list(volume.data.shape), spacing_mm=list(volume.spacing),
                      threshold=400, closing_radius_mm=.8,
                      segmentation_dice=dice(segmentation, phantom['bone_truth']),
                      true_bone_volume_mm3=truth_volume, segmented_bone_volume_mm3=segmented_volume,
                      bone_volume_error_pct=100*abs(segmented_volume-truth_volume)/truth_volume,
                      intact_digital_volume_mm3=volume_mm3(phantom['intact_truth'], volume.spacing),
                      analytic_intact_cylinder_volume_mm3=analytic_shell,
                      defect_volume_mm3=volume_mm3(defect, volume.spacing),
                      defect_bbox=bounding_box(defect, volume.spacing),
                      bone_mesh=mesh_metrics(bone_mesh), defect_mesh=mesh_metrics(defect_mesh), modules=fit)
        record['defect_mesh_volume_error_pct'] = 100*abs(record['defect_mesh']['volume_mm3']-record['defect_volume_mm3'])/record['defect_volume_mm3']
        records.append(record)
        if case == 'nominal':
            _overlay(volume, segmentation, defect, figure_dir / 'slice-overlay.png')
            _render(bone_mesh, defect_mesh, module_mesh, figure_dir / 'mesh-render.png')
    report = dict(disclaimer='Learning prototype. Not medical software. No real biomechanical simulation.',
                  units='mm, mm2, mm3; ndarray axis order xyz; voxel-centre coordinates', cases=records)
    (output_dir / 'results.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    columns = ['case', 'segmentation_dice', 'bone_volume_error_pct', 'defect_volume_mm3',
               'coverage_pct', 'overshoot_pct', 'bone_overlap_mm3', 'block_count', 'fit_quality']
    with (output_dir / 'results.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in records:
            writer.writerow({**{k:r[k] for k in columns[:4]},
                             **{k:r['modules'][k] for k in ('coverage_pct','overshoot_pct','bone_overlap_mm3','fit_quality')},
                             'block_count':len(r['modules']['blocks'])})
    return report


def run_volume(input_path, defect_path, output_dir, threshold=400.):
    """Optional public-data path. A defect mask must be explicitly supplied."""
    volume = load_volume(input_path)
    defect_volume = load_volume(defect_path)
    if not (volume.data.shape == defect_volume.data.shape and np.allclose(volume.spacing, defect_volume.spacing)
            and np.allclose(volume.origin, defect_volume.origin) and np.allclose(volume.direction, defect_volume.direction)):
        raise ValueError('Defect mask must have the same shape, spacing, origin and direction as the scan')
    defect = defect_volume.data > 0
    if not defect.any():
        raise ValueError('Defect mask is empty; automatic clinical defect detection is not implemented')
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    seg = segment(volume.data, volume.spacing, threshold) & ~defect
    mesh = mesh_from_mask(seg, volume.spacing, volume.origin, volume.direction)
    mesh.export(out / 'segmentation.stl')
    fit = select_modules(defect, volume.spacing)
    union = fit.pop('union_mask')
    fit['bone_overlap_mm3'] = volume_mm3(union & seg,volume.spacing)
    mesh_from_mask(defect,volume.spacing,volume.origin,volume.direction).export(out / 'defect.stl')
    if union.any():
        mesh_from_mask(union,volume.spacing,volume.origin,volume.direction).export(out / 'modules.stl')
    report = dict(source=str(input_path), disclaimer='Learning prototype, no ground truth or clinical accuracy claim.',
                  segmentation_volume_mm3=volume_mm3(seg, volume.spacing), mesh=mesh_metrics(mesh),
                  defect_volume_mm3=volume_mm3(defect, volume.spacing), defect_bbox=bounding_box(defect, volume.spacing),
                  modules=fit, module_coordinate_frame='image axes in mm; world = origin + direction @ local')
    (out / 'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def public_demo(input_path, output_dir, threshold=400.):
    """Create a deliberately artificial small defect in a public scan, no annotation claim."""
    volume = load_volume(input_path)
    segmentation = segment(volume.data, volume.spacing, threshold)
    if not segmentation.any():
        raise ValueError('Threshold produced no foreground; inspect intensities and choose a threshold')
    indices = np.argwhere(segmentation)
    # Pick a surface voxel near the middle slice, not a clinical/anatomical landmark.
    mid_z = int(np.median(indices[:, 2]))
    plane = indices[abs(indices[:, 2] - mid_z) <= 1]
    center = plane[np.argmax(plane[:, 0])]
    half = np.maximum(1, np.ceil(5 / np.array(volume.spacing)).astype(int))
    low = np.maximum(0, center-half)
    high = np.minimum(volume.data.shape, center+half+1)
    defect = np.zeros(volume.data.shape, dtype=bool)
    roi = tuple(slice(int(a), int(b)) for a, b in zip(low, high))
    defect[roi] = segmentation[roi]
    out = Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    mask_path = out / 'artificial-defect-mask.nii.gz'
    save_volume(Volume(defect,volume.spacing,volume.origin,volume.direction),mask_path)
    result = run_volume(input_path,mask_path,out,threshold)
    result['defect_kind'] = 'Artificial removal of a surface ROI, not a patient diagnosis or annotation'
    result['threshold_intensity_units'] = 'Stored CT intensities; HU calibration not independently established'
    result['origin_lps_mm'] = list(volume.origin)
    result['direction'] = volume.direction.tolist()
    (out / 'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
