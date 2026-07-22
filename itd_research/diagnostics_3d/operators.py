"""Structured-grid gradient, vorticity, and velocity-gradient operators (research).

These operators live entirely outside the certified ``itd_v29_core`` and are used
by the external-validation and 3D-diagnostics research layers. They are explicit
about axis order and units and never assume equal spacing silently.

Array and axis convention
-------------------------
Fields are ``float64`` arrays. A 2D field has shape ``(ny, nx)`` (axis 0 = y,
axis 1 = x). A 3D field has shape ``(nz, ny, nx)`` (axis 0 = z, axis 1 = y,
axis 2 = x). Coordinates are supplied as explicit strictly increasing 1D arrays
``x`` (last axis), ``y`` (axis -2), and ``z`` (axis -3).

The velocity-gradient tensor is ``J[..., i, j] = d u_i / d x_j`` with component
order ``(u, v, w)`` and direction order ``(x, y, z)``.

Boundary modes
--------------
``finite`` uses NumPy second-order interior/edge differences (``edge_order=2``)
against the supplied coordinates. ``periodic`` requires uniform spacing and uses
centred circular differences implemented with ``numpy.roll``.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]

BOUNDARY_MODES = ("finite", "periodic")


def validate_boundary_mode(boundary_mode: str) -> str:
    if not isinstance(boundary_mode, str):
        raise ValueError("boundary_mode must be a string.")
    normalized = boundary_mode.strip().lower()
    if normalized not in BOUNDARY_MODES:
        allowed = ", ".join(BOUNDARY_MODES)
        raise ValueError(f"Unknown boundary mode {boundary_mode!r}. Allowed: {allowed}.")
    return normalized


def validate_axis_coordinates(coordinates: object, name: str) -> FloatArray:
    """Return strictly increasing finite 1D coordinates with at least 3 points."""
    if isinstance(coordinates, (str, bytes)):
        raise ValueError(f"{name} coordinates must be a numeric sequence.")
    array = np.asarray(coordinates, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} coordinates must be one-dimensional.")
    if array.size < 3:
        raise ValueError(f"{name} axis must contain at least three coordinates.")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} coordinates contain a non-finite value.")
    if not np.all(np.diff(array) > 0.0):
        raise ValueError(f"{name} coordinates must be strictly increasing.")
    return array


def _uniform_spacing(coordinates: FloatArray, name: str) -> float:
    differences = np.diff(coordinates)
    mean = float(np.mean(differences))
    tolerance = 128.0 * np.finfo(np.float64).eps * max(1.0, abs(mean))
    if not np.allclose(differences, mean, rtol=1.0e-12, atol=tolerance):
        raise ValueError(f"periodic mode requires uniform {name} spacing.")
    return mean


def partial_derivative(
    field: FloatArray,
    coordinates: FloatArray,
    axis: int,
    boundary_mode: str = "finite",
) -> FloatArray:
    """Second-order derivative of ``field`` along ``axis`` against ``coordinates``."""
    boundary_mode = validate_boundary_mode(boundary_mode)
    array = np.asarray(field, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise ValueError("field contains a non-finite value.")
    if array.shape[axis] != coordinates.shape[0]:
        raise ValueError("field extent does not match the coordinate length.")

    if boundary_mode == "finite":
        return np.asarray(
            np.gradient(array, coordinates, axis=axis, edge_order=2), dtype=np.float64
        )

    spacing = _uniform_spacing(coordinates, "axis")
    forward = np.roll(array, -1, axis=axis)
    backward = np.roll(array, 1, axis=axis)
    return np.asarray((forward - backward) / (2.0 * spacing), dtype=np.float64)


def _finite_field(field: object, name: str, ndim: int) -> FloatArray:
    array = np.asarray(field, dtype=np.float64)
    if array.ndim != ndim:
        raise ValueError(f"{name} must be a {ndim}D array.")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains a non-finite value.")
    return array


def velocity_gradient_2d(
    u: FloatArray,
    v: FloatArray,
    x: object,
    y: object,
    boundary_mode: str = "finite",
) -> FloatArray:
    """Return the 2x2 velocity-gradient field ``J[..., i, j] = d u_i / d x_j``.

    Output shape is ``(ny, nx, 2, 2)`` with component/direction order ``(x, y)``.
    """
    boundary_mode = validate_boundary_mode(boundary_mode)
    x_coords = validate_axis_coordinates(x, "x")
    y_coords = validate_axis_coordinates(y, "y")
    u_field = _finite_field(u, "u", 2)
    v_field = _finite_field(v, "v", 2)
    if u_field.shape != v_field.shape:
        raise ValueError("u and v must share a shape.")
    if u_field.shape != (y_coords.size, x_coords.size):
        raise ValueError("velocity shape does not match the (y, x) coordinates.")

    du_dx = partial_derivative(u_field, x_coords, axis=1, boundary_mode=boundary_mode)
    du_dy = partial_derivative(u_field, y_coords, axis=0, boundary_mode=boundary_mode)
    dv_dx = partial_derivative(v_field, x_coords, axis=1, boundary_mode=boundary_mode)
    dv_dy = partial_derivative(v_field, y_coords, axis=0, boundary_mode=boundary_mode)

    gradient = np.empty(u_field.shape + (2, 2), dtype=np.float64)
    gradient[..., 0, 0] = du_dx
    gradient[..., 0, 1] = du_dy
    gradient[..., 1, 0] = dv_dx
    gradient[..., 1, 1] = dv_dy
    return gradient


def velocity_gradient_3d(
    u: FloatArray,
    v: FloatArray,
    w: FloatArray,
    x: object,
    y: object,
    z: object,
    boundary_mode: str = "finite",
) -> FloatArray:
    """Return the 3x3 velocity-gradient field ``J[..., i, j] = d u_i / d x_j``.

    Output shape is ``(nz, ny, nx, 3, 3)`` with component/direction order
    ``(x, y, z)``.
    """
    boundary_mode = validate_boundary_mode(boundary_mode)
    x_coords = validate_axis_coordinates(x, "x")
    y_coords = validate_axis_coordinates(y, "y")
    z_coords = validate_axis_coordinates(z, "z")
    components = [_finite_field(c, name, 3) for c, name in ((u, "u"), (v, "v"), (w, "w"))]
    shape = components[0].shape
    if any(component.shape != shape for component in components[1:]):
        raise ValueError("u, v, and w must share a shape.")
    if shape != (z_coords.size, y_coords.size, x_coords.size):
        raise ValueError("velocity shape does not match the (z, y, x) coordinates.")

    axis_coords = (x_coords, y_coords, z_coords)
    axis_index = (2, 1, 0)  # direction j -> array axis (x->2, y->1, z->0)

    gradient = np.empty(shape + (3, 3), dtype=np.float64)
    for i, component in enumerate(components):
        for j in range(3):
            gradient[..., i, j] = partial_derivative(
                component, axis_coords[j], axis=axis_index[j], boundary_mode=boundary_mode
            )
    return gradient


def vorticity_2d_from_gradient(gradient: FloatArray) -> FloatArray:
    """Out-of-plane vorticity ``omega_z = dv/dx - du/dy`` from a 2x2 J field."""
    return np.asarray(gradient[..., 1, 0] - gradient[..., 0, 1], dtype=np.float64)


def vorticity_3d_from_gradient(gradient: FloatArray) -> FloatArray:
    """Vorticity vector field ``(omega_x, omega_y, omega_z)`` from a 3x3 J field.

    ``omega_x = dw/dy - dv/dz``, ``omega_y = du/dz - dw/dx``,
    ``omega_z = dv/dx - du/dy``.
    """
    omega_x = gradient[..., 2, 1] - gradient[..., 1, 2]
    omega_y = gradient[..., 0, 2] - gradient[..., 2, 0]
    omega_z = gradient[..., 1, 0] - gradient[..., 0, 1]
    return np.stack((omega_x, omega_y, omega_z), axis=-1).astype(np.float64)
