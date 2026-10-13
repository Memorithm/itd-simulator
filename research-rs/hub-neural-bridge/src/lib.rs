#![forbid(unsafe_code)]
//! Development-only real Hub/process bridge. ITD's periodic diagnostic subset
//! and NeuralOperator's isotropic residual remain their owners' implementations.
//! Neither is a trained model or the certified V29.18 signature.

use itd_field::Field2D;
use neural_operator_rust::{Budget, Forcing, Grid, darcy_residual};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::error::Error;

pub const HUB_SHA: &str = "01cf5f1e6d96573d57eef8d2aea22a5a8b0da02f";
pub const NEURAL_SHA: &str = "2eba990da4779aeecfea1c4c288d8a6e552c48d8";
pub const ITD_SHA: &str = env!("ITD_SOURCE_SHA");
pub const CONTRACT: &str = "itd.hub-neural-development@1.0.0";
pub const INPUT_LIMIT: usize = 262_144;
pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

#[derive(Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub contract: String,
    pub split: String,
    pub itd_sha: String,
    pub hub_sha: String,
    pub neural_operator_sha: String,
    pub input_sha256: String,
}

impl Request {
    pub fn validate(&self) -> Result<()> {
        if self.contract != CONTRACT
            || self.split != "development"
            || self.itd_sha != ITD_SHA
            || self.hub_sha != HUB_SHA
            || self.neural_operator_sha != NEURAL_SHA
            || self.itd_sha.len() != 40
            || !self
                .itd_sha
                .bytes()
                .all(|x| x.is_ascii_digit() || (b'a'..=b'f').contains(&x))
            || self.input_sha256.len() != 64
            || !self
                .input_sha256
                .bytes()
                .all(|x| x.is_ascii_digit() || (b'a'..=b'f').contains(&x))
        {
            return Err("unsupported contract, split or exact source/input identity".into());
        }
        Ok(())
    }
}

#[derive(Serialize, Deserialize, Clone)]
#[serde(deny_unknown_fields)]
pub struct DevelopmentFields {
    pub schema_version: u32,
    pub split: String,
    pub rows: usize,
    pub columns: usize,
    pub spacing: f64,
    pub length_x: f64,
    pub length_y: f64,
    pub velocity_u: Vec<f64>,
    pub velocity_v: Vec<f64>,
    pub solution: Vec<f64>,
    pub permeability: Vec<f64>,
    pub forcing: Vec<f64>,
}

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Observation {
    pub schema_version: u32,
    pub contract: String,
    pub split: String,
    pub itd_sha: String,
    pub hub_sha: String,
    pub neural_operator_sha: String,
    pub input_sha256: String,
    pub itd_diagnostic_subset: [f64; 5],
    pub darcy_residual: Vec<f64>,
    pub numerical_output_sha256: String,
    pub grid_points: usize,
    pub interior_points: usize,
    pub scalar_ops: usize,
    pub scientific_claim: String,
    pub isolation_claim: String,
}

pub fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

pub fn execute(request: &Request, bytes: &[u8]) -> Result<Observation> {
    request.validate()?;
    if bytes.len() > INPUT_LIMIT || sha256(bytes) != request.input_sha256 {
        return Err("immutable Development input byte identity mismatch or bound exceeded".into());
    }
    let data: DevelopmentFields = serde_json::from_slice(bytes)?;
    let n = data
        .rows
        .checked_mul(data.columns)
        .ok_or("grid shape overflow")?;
    if data.schema_version != 1
        || data.split != "development"
        || data.rows < 3
        || data.columns < 3
        || n > 4096
        || !data.spacing.is_finite()
        || data.spacing <= 0.0
        || !data.length_x.is_finite()
        || !data.length_y.is_finite()
        || data.length_x <= 0.0
        || data.length_y <= 0.0
    {
        return Err("Development field contract/bounds refused".into());
    }
    for field in [
        &data.velocity_u,
        &data.velocity_v,
        &data.solution,
        &data.permeability,
        &data.forcing,
    ] {
        if field.len() != n || field.iter().any(|x| !x.is_finite()) {
            return Err("invalid bounded finite field".into());
        }
    }
    let u = Field2D::new(data.rows, data.columns, data.velocity_u);
    let v = Field2D::new(data.rows, data.columns, data.velocity_v);
    let diagnostic = itd_diagnostics::diagnostics(&u, &v, data.spacing).as_array();
    let residual = darcy_residual(
        Grid {
            rows: data.rows,
            columns: data.columns,
            length_x: data.length_x,
            length_y: data.length_y,
        },
        &data.solution,
        &data.permeability,
        Forcing::Field(&data.forcing),
        Budget {
            max_grid_points: 4096,
            max_scalar_ops: 30 * 4096 + 4,
            max_output_bytes: 8 * 4096,
        },
    )?;
    if diagnostic
        .iter()
        .chain(&residual.values)
        .any(|x| !x.is_finite())
    {
        return Err("non-finite numerical observation".into());
    }
    let output = serde_json::to_vec(&(diagnostic, &residual.values))?;
    Ok(Observation {
        schema_version: 1,
        contract: CONTRACT.into(),
        split: "development".into(),
        itd_sha: ITD_SHA.into(),
        hub_sha: HUB_SHA.into(),
        neural_operator_sha: NEURAL_SHA.into(),
        input_sha256: request.input_sha256.clone(),
        itd_diagnostic_subset: diagnostic,
        darcy_residual: residual.values,
        numerical_output_sha256: sha256(&output),
        grid_points: residual.cost.grid_points,
        interior_points: residual.cost.interior_points,
        scalar_ops: residual.cost.scalar_ops,
        scientific_claim: "finite_Development_observation_not_V29_18_or_trained_model_quality"
            .into(),
        isolation_claim: "supervised_process_not_OS_sandbox".into(),
    })
}

/// A deterministic synthetic Development fixture; no dataset or final labels.
pub fn fixture() -> DevelopmentFields {
    let mut u = Vec::new();
    let mut v = Vec::new();
    let mut solution = Vec::new();
    for row in 0..6 {
        for column in 0..8 {
            u.push(-(row as f64));
            v.push(column as f64);
            solution.push((row * row + column * column) as f64);
        }
    }
    DevelopmentFields {
        schema_version: 1,
        split: "development".into(),
        rows: 6,
        columns: 8,
        spacing: 1.0,
        length_x: 7.0,
        length_y: 5.0,
        velocity_u: u,
        velocity_v: v,
        solution,
        permeability: vec![1.0; 48],
        forcing: vec![1.0; 48],
    }
}

pub fn request_for(bytes: &[u8]) -> Request {
    Request {
        contract: CONTRACT.into(),
        split: "development".into(),
        itd_sha: ITD_SHA.into(),
        hub_sha: HUB_SHA.into(),
        neural_operator_sha: NEURAL_SHA.into(),
        input_sha256: sha256(bytes),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn owner_kernels_and_input_causality_are_executed() {
        let mut data = fixture();
        let bytes = serde_json::to_vec(&data).unwrap();
        let first = execute(&request_for(&bytes), &bytes).unwrap();
        // For u=-y,v=x the periodic central differences give this exact subset.
        assert_eq!(
            first.itd_diagnostic_subset,
            [2.5, 5.0_f64.sqrt(), 63.0 / 25.0 - 1.0, 1.75, 63.0 / 25.0]
        );
        assert!(first.darcy_residual.iter().all(|x| *x == -5.0));
        data.forcing.fill(2.0);
        let changed = serde_json::to_vec(&data).unwrap();
        let second = execute(&request_for(&changed), &changed).unwrap();
        assert!(second.darcy_residual.iter().all(|x| *x == -6.0));
        assert_ne!(first.input_sha256, second.input_sha256);
        assert_ne!(
            first.numerical_output_sha256,
            second.numerical_output_sha256
        );
        assert_eq!(first.itd_diagnostic_subset, second.itd_diagnostic_subset);
    }

    #[test]
    fn non_development_stale_sources_hash_shape_and_unknown_fields_fail_closed() {
        let bytes = serde_json::to_vec(&fixture()).unwrap();
        let mut request = request_for(&bytes);
        request.split = "final".into();
        assert!(execute(&request, &bytes).is_err());
        request = request_for(&bytes);
        request.hub_sha = "0".repeat(40);
        assert!(execute(&request, &bytes).is_err());
        request = request_for(&bytes);
        request.input_sha256 = "0".repeat(64);
        assert!(execute(&request, &bytes).is_err());
        let mut data = fixture();
        data.rows = usize::MAX;
        let bad = serde_json::to_vec(&data).unwrap();
        assert!(execute(&request_for(&bad), &bad).is_err());
        let mut data = fixture();
        data.split = "final".into();
        let bad = serde_json::to_vec(&data).unwrap();
        assert!(execute(&request_for(&bad), &bad).is_err());
        assert!(serde_json::from_slice::<Request>(br#"{"contract":"x","split":"development","itd_sha":"x","hub_sha":"x","neural_operator_sha":"x","input_sha256":"x","authorized":true}"#).is_err());
    }
}
