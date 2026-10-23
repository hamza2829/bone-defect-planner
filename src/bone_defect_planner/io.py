"""All arrays are indexed x, y, z. Physical coordinates are millimetres, LPS."""
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import SimpleITK as sitk


@dataclass
class Volume:
    data: np.ndarray
    spacing: tuple[float, float, float]
    origin: tuple[float, float, float] = (0., 0., 0.)
    direction: np.ndarray = field(default_factory=lambda: np.eye(3))

    def __post_init__(self):
        self.data = np.asarray(self.data)
        self.spacing = tuple(float(s) for s in self.spacing)
        self.origin = tuple(float(x) for x in self.origin)
        self.direction = np.asarray(self.direction, dtype=float).reshape(3, 3)
        if self.data.ndim != 3 or not all(n > 0 for n in self.data.shape):
            raise ValueError('Need a nonempty 3D volume')
        if len(self.spacing) != 3 or not np.isfinite(self.spacing).all() or min(self.spacing) <= 0:
            raise ValueError('Spacing must contain three finite positive mm values')
        if len(self.origin) != 3 or not np.isfinite(self.origin).all():
            raise ValueError('Origin must contain three finite coordinates')
        if not np.isfinite(self.direction).all() or not np.allclose(self.direction.T @ self.direction, np.eye(3), atol=1e-6):
            raise ValueError('Direction must be an orthonormal matrix')


def load_volume(path):
    image = sitk.ReadImage(str(path))
    if image.GetDimension() != 3 or image.GetNumberOfComponentsPerPixel() != 1:
        raise ValueError('Only scalar 3D images are supported')
    # SimpleITK gives numpy z,y,x. Explicitly transpose to our x,y,z convention.
    data = sitk.GetArrayFromImage(image).transpose(2, 1, 0)
    return Volume(data, image.GetSpacing(), image.GetOrigin(), np.array(image.GetDirection()).reshape(3, 3))


def save_volume(volume, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = volume.data.astype(np.uint8) if volume.data.dtype == bool else volume.data
    image = sitk.GetImageFromArray(np.ascontiguousarray(data.transpose(2, 1, 0)))
    image.SetSpacing(volume.spacing)
    image.SetOrigin(volume.origin)
    image.SetDirection(tuple(volume.direction.ravel()))
    sitk.WriteImage(image, str(path), True)
