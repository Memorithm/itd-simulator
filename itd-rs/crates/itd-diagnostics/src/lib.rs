//! A well-defined SUBSET of ITD-related scalar diagnostics on a 2D field.
//!
//! Reproduces exactly the periodic-central-difference quantities the Python reference
//! `tools/rust/generate_diagnostics_fixture.py` computes: enstrophy `0.5<omega^2>`,
//! vorticity RMS, localization `<omega^4>/<omega^2>^2 - 1`, palinstrophy
//! `0.5<|grad omega|^2>`, and vorticity flatness `<omega^4>/<omega^2>^2`. It does NOT
//! reproduce the certified V29.18 signature (finite-boundary operator +
//! structural_metrics / multiscale); that remains Python-only.
#![forbid(unsafe_code)]

use itd_field::{grad_sq_mean, vorticity, Field2D};

/// The reproduced diagnostic subset.
#[derive(Clone, Debug, PartialEq)]
pub struct Diagnostics {
    pub enstrophy: f64,
    pub vorticity_rms: f64,
    pub localization: f64,
    pub palinstrophy: f64,
    pub vorticity_flatness: f64,
}

impl Diagnostics {
    /// Fixed field order, matching the Python fixture's expected-value line.
    pub fn as_array(&self) -> [f64; 5] {
        [
            self.enstrophy,
            self.vorticity_rms,
            self.localization,
            self.palinstrophy,
            self.vorticity_flatness,
        ]
    }
}

/// Compute the diagnostic subset from a 2D velocity field with spacing `h`.
pub fn diagnostics(u: &Field2D, v: &Field2D, h: f64) -> Diagnostics {
    let w = vorticity(u, v, h);
    let n = w.data.len() as f64;
    // Deterministic reductions: fixed order, separate accumulators for <w^2>, <w^4>.
    let mut m2 = 0.0_f64;
    let mut m4 = 0.0_f64;
    for &x in &w.data {
        let x2 = x * x;
        m2 += x2;
        m4 += x2 * x2;
    }
    m2 /= n;
    m4 /= n;
    let localization = if m2 > 0.0 { m4 / (m2 * m2) - 1.0 } else { 0.0 };
    let vorticity_flatness = if m2 > 0.0 { m4 / (m2 * m2) } else { 0.0 };
    Diagnostics {
        enstrophy: 0.5 * m2,
        vorticity_rms: m2.max(0.0).sqrt(),
        localization,
        palinstrophy: 0.5 * grad_sq_mean(&w, h),
        vorticity_flatness,
    }
}
