//! Typed 2D field container with deterministic, periodic central-difference operators.
//!
//! Row-major storage (`ny` rows by `nx` cols). All reductions iterate in a fixed
//! row-major order with a single accumulator, so results are bit-for-bit deterministic
//! and independent of thread count. This crate is a research reference; it never
//! replaces the Python scientific oracle.
#![forbid(unsafe_code)]

/// A dense 2D scalar field, row-major (`data[r * nx + c]`).
#[derive(Clone, Debug, PartialEq)]
pub struct Field2D {
    pub ny: usize,
    pub nx: usize,
    pub data: Vec<f64>,
}

impl Field2D {
    /// Create a field from row-major data; panics if the length is inconsistent.
    pub fn new(ny: usize, nx: usize, data: Vec<f64>) -> Self {
        assert_eq!(data.len(), ny * nx, "data length must equal ny*nx");
        Field2D { ny, nx, data }
    }

    #[inline]
    pub fn at(&self, r: usize, c: usize) -> f64 {
        self.data[r * self.nx + c]
    }

    /// Deterministic mean (fixed row-major order, single accumulator).
    pub fn mean(&self) -> f64 {
        let mut acc = 0.0_f64;
        for &x in &self.data {
            acc += x;
        }
        acc / (self.data.len() as f64)
    }
}

/// Periodic central-difference vorticity `omega = dv/dx - du/dy` with spacing `h`.
///
/// Axis convention: `x` runs along columns, `y` along rows -- matching the Python
/// reference (`np.roll` on axes 1 and 0). Boundaries wrap periodically.
pub fn vorticity(u: &Field2D, v: &Field2D, h: f64) -> Field2D {
    assert_eq!((u.ny, u.nx), (v.ny, v.nx), "u and v must share a shape");
    let (ny, nx) = (u.ny, u.nx);
    let mut w = vec![0.0_f64; ny * nx];
    for r in 0..ny {
        let rp = (r + 1) % ny;
        let rm = (r + ny - 1) % ny;
        for c in 0..nx {
            let cp = (c + 1) % nx;
            let cm = (c + nx - 1) % nx;
            let dv_dx = (v.at(r, cp) - v.at(r, cm)) / (2.0 * h);
            let du_dy = (u.at(rp, c) - u.at(rm, c)) / (2.0 * h);
            w[r * nx + c] = dv_dx - du_dy;
        }
    }
    Field2D::new(ny, nx, w)
}

/// Mean squared gradient `<(df/dx)^2 + (df/dy)^2>` via periodic central differences.
///
/// Same axis convention and spacing as [`vorticity`]. Used for palinstrophy
/// `0.5 * <|grad omega|^2>`. Deterministic row-major accumulation.
pub fn grad_sq_mean(f: &Field2D, h: f64) -> f64 {
    let (ny, nx) = (f.ny, f.nx);
    let inv = 1.0 / (2.0 * h);
    let mut acc = 0.0_f64;
    for r in 0..ny {
        let rp = (r + 1) % ny;
        let rm = (r + ny - 1) % ny;
        for c in 0..nx {
            let cp = (c + 1) % nx;
            let cm = (c + nx - 1) % nx;
            let df_dx = (f.at(r, cp) - f.at(r, cm)) * inv;
            let df_dy = (f.at(rp, c) - f.at(rm, c)) * inv;
            acc += df_dx * df_dx + df_dy * df_dy;
        }
    }
    acc / ((ny * nx) as f64)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mean_of_ones_is_one() {
        let f = Field2D::new(2, 3, vec![1.0; 6]);
        assert!((f.mean() - 1.0).abs() < 1e-15);
    }

    #[test]
    fn solid_rotation_has_constant_vorticity() {
        // u = -y, v = x on a periodic grid gives (nearly) constant vorticity 2 away
        // from the wrap seam; check an interior point.
        let n = 8;
        let h = 1.0;
        let mut u = vec![0.0; n * n];
        let mut v = vec![0.0; n * n];
        for r in 0..n {
            for c in 0..n {
                u[r * n + c] = -(r as f64);
                v[r * n + c] = c as f64;
            }
        }
        let uf = Field2D::new(n, n, u);
        let vf = Field2D::new(n, n, v);
        let w = vorticity(&uf, &vf, h);
        assert!((w.at(4, 4) - 2.0).abs() < 1e-12);
    }
}
