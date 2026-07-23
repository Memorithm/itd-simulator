"""Velocity-gradient-tensor vortex diagnostics (research).

Given a velocity-gradient field ``J[..., i, j] = d u_i / d x_j`` (2x2 or 3x3),
these functions compute established vortex-identification diagnostics. They are
pure tensor operations, so they can be validated against exact hand-derived
matrices (see ``tests/test_diagnostics_3d.py``). None of these is asserted to be
superior to ITD; they are the reference diagnostics ITD is compared against.

Definitions
-----------
* strain rate ``S = 0.5 (J + J^T)`` (symmetric)
* rotation ``Omega = 0.5 (J - J^T)`` (antisymmetric)
* Q-criterion ``Q = 0.5 (||Omega||_F^2 - ||S||_F^2)`` (3D; a 2D analogue for 2x2)
* lambda2: the middle eigenvalue (``lambda_1 >= lambda_2 >= lambda_3``) of the
  symmetric tensor ``S^2 + Omega^2``; a vortex region is ``lambda_2 < 0``
* swirling strength: the magnitude of the imaginary part of the complex-conjugate
  eigenvalue pair of ``J`` (zero when all eigenvalues are real)
* Okubo-Weiss (2D) ``W = s_n^2 + s_s^2 - omega^2`` with normal strain
  ``s_n = du/dx - dv/dy``, shear strain ``s_s = dv/dx + du/dy``, and
  ``omega = dv/dx - du/dy``
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


def _validate_gradient(gradient: object) -> FloatArray:
    array = np.asarray(gradient, dtype=np.float64)
    if array.ndim < 2 or array.shape[-1] != array.shape[-2]:
        raise ValueError("gradient must have square trailing dimensions (n, n).")
    if array.shape[-1] not in (2, 3):
        raise ValueError("gradient trailing dimensions must be 2x2 or 3x3.")
    if not np.all(np.isfinite(array)):
        raise ValueError("gradient contains a non-finite value.")
    return array


def strain_rate_tensor(gradient: FloatArray) -> FloatArray:
    """Symmetric strain-rate tensor ``S = 0.5 (J + J^T)``."""
    array = _validate_gradient(gradient)
    return 0.5 * (array + np.swapaxes(array, -1, -2))


def rotation_tensor(gradient: FloatArray) -> FloatArray:
    """Antisymmetric rotation tensor ``Omega = 0.5 (J - J^T)``."""
    array = _validate_gradient(gradient)
    return 0.5 * (array - np.swapaxes(array, -1, -2))


def _frobenius_squared(tensor: FloatArray) -> FloatArray:
    return np.sum(tensor**2, axis=(-1, -2))


def q_criterion(gradient: FloatArray) -> FloatArray:
    """Q-criterion field ``0.5 (||Omega||^2 - ||S||^2)``.

    For a 3x3 gradient this is the standard 3D Q. For a 2x2 gradient it is the 2D
    analogue (labelled as such), not the full 3D criterion.
    """
    array = _validate_gradient(gradient)
    strain = 0.5 * (array + np.swapaxes(array, -1, -2))
    rotation = 0.5 * (array - np.swapaxes(array, -1, -2))
    return np.asarray(
        0.5 * (_frobenius_squared(rotation) - _frobenius_squared(strain)),
        dtype=np.float64,
    )


def strain_rate_magnitude(gradient: FloatArray) -> FloatArray:
    """Frobenius norm of the strain-rate tensor ``||S||_F``."""
    strain = strain_rate_tensor(gradient)
    return np.sqrt(_frobenius_squared(strain))


def lambda2(gradient: FloatArray) -> FloatArray:
    """The Jeong-Hussain lambda_2 field (middle eigenvalue of ``S^2 + Omega^2``).

    Requires a 3x3 gradient. Eigenvalues are ordered ``lambda_1 >= lambda_2 >=
    lambda_3``; a vortex region is conventionally ``lambda_2 < 0``.
    """
    array = _validate_gradient(gradient)
    if array.shape[-1] != 3:
        raise ValueError("lambda2 requires a 3x3 velocity-gradient tensor.")
    strain = 0.5 * (array + np.swapaxes(array, -1, -2))
    rotation = 0.5 * (array - np.swapaxes(array, -1, -2))
    symmetric = np.matmul(strain, strain) + np.matmul(rotation, rotation)
    # Symmetrise defensively against round-off before the symmetric eigensolver.
    symmetric = 0.5 * (symmetric + np.swapaxes(symmetric, -1, -2))
    eigenvalues = np.linalg.eigvalsh(symmetric)  # ascending: [lambda_3, lambda_2, lambda_1]
    return np.asarray(eigenvalues[..., 1], dtype=np.float64)


def swirling_strength(gradient: FloatArray) -> FloatArray:
    """Swirling strength: magnitude of the imaginary part of ``J``'s eigenvalues.

    Zero where all eigenvalues are real (e.g. pure shear or pure strain). Works
    for 2x2 and 3x3 gradients.
    """
    array = _validate_gradient(gradient)
    eigenvalues = np.linalg.eigvals(array)
    return np.asarray(np.max(np.abs(eigenvalues.imag), axis=-1), dtype=np.float64)


def swirling_strength_with_axis(
    gradient: FloatArray,
    conditioning_tolerance: float = 1.0e-9,
) -> dict[str, FloatArray]:
    """3D swirling strength plus the real-eigenvector swirl axis and conditioning.

    Returns a mapping with ``strength`` (imaginary eigenvalue magnitude), ``axis``
    (unit real eigenvector where well conditioned, else zeros), and
    ``well_conditioned`` (a boolean field). The axis is only reported where the
    eigenvalue is a genuine real value accompanied by a complex-conjugate pair.
    """
    array = _validate_gradient(gradient)
    if array.shape[-1] != 3:
        raise ValueError("swirling_strength_with_axis requires a 3x3 tensor.")
    eigenvalues, eigenvectors = np.linalg.eig(array)
    imaginary = np.abs(eigenvalues.imag)
    strength = np.max(imaginary, axis=-1)
    # The real eigenvalue is the one with the smallest imaginary part.
    real_index = np.argmin(imaginary, axis=-1)
    index = real_index[..., None, None]
    selected = np.take_along_axis(eigenvectors, index, axis=-1)[..., 0]
    axis = np.real(selected)
    norm = np.linalg.norm(axis, axis=-1, keepdims=True)
    well_conditioned = (strength > conditioning_tolerance) & (
        norm[..., 0] > conditioning_tolerance
    )
    safe_norm = np.where(norm > 0.0, norm, 1.0)
    axis = np.where(well_conditioned[..., None], axis / safe_norm, 0.0)
    return {
        "strength": np.asarray(strength, dtype=np.float64),
        "axis": np.asarray(axis, dtype=np.float64),
        "well_conditioned": np.asarray(well_conditioned, dtype=bool),
    }


def okubo_weiss_2d(gradient: FloatArray) -> FloatArray:
    """Okubo-Weiss parameter ``W = s_n^2 + s_s^2 - omega^2`` for a 2x2 gradient.

    ``W < 0`` marks rotation-dominated (vortex) regions.
    """
    array = _validate_gradient(gradient)
    if array.shape[-1] != 2:
        raise ValueError("okubo_weiss_2d requires a 2x2 velocity-gradient tensor.")
    normal_strain = array[..., 0, 0] - array[..., 1, 1]
    shear_strain = array[..., 1, 0] + array[..., 0, 1]
    vorticity = array[..., 1, 0] - array[..., 0, 1]
    return np.asarray(
        normal_strain**2 + shear_strain**2 - vorticity**2, dtype=np.float64
    )
