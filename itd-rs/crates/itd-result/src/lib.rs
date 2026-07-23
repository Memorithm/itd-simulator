//! A minimal product result contract with provenance and abstention (pure std).
//!
//! Mirrors the Python `ITDAnalysisResult` guard: an emitted alarm must carry
//! confidence, calibration domain, and provenance. JSON is serialized by hand (no
//! external crates), with a fixed key order for deterministic output.
#![forbid(unsafe_code)]

/// A self-describing analysis result for one frame.
#[derive(Clone, Debug, PartialEq)]
pub struct AnalysisResult {
    pub enstrophy: f64,
    pub vorticity_rms: f64,
    pub localization: f64,
    pub prediction: f64,
    pub confidence: f64,
    pub ood_score: f64,
    pub abstained: bool,
    pub abstention_reason: String,
    pub calibration_profile: String,
    pub provenance: String,
    pub commit: String,
}

impl AnalysisResult {
    /// An emitted alarm must carry confidence, a calibration domain, and provenance.
    pub fn is_bare_alarm(&self) -> bool {
        let alarm = !self.abstained && self.prediction >= 0.5;
        if !alarm {
            return false;
        }
        let ok_conf = self.confidence >= 0.0 && self.confidence <= 1.0;
        let ok_domain = matches!(
            self.calibration_profile.as_str(),
            "in-domain" | "borderline" | "out-of-domain"
        );
        let ok_prov = !self.provenance.is_empty() && self.provenance != "unknown";
        !(ok_conf && ok_domain && ok_prov)
    }

    /// Deterministic JSON (fixed key order, no external crates).
    pub fn to_json(&self) -> String {
        format!(
            concat!(
                "{{\"enstrophy\":{},\"vorticity_rms\":{},\"localization\":{},",
                "\"prediction\":{},\"confidence\":{},\"ood_score\":{},",
                "\"abstained\":{},\"abstention_reason\":\"{}\",",
                "\"calibration_profile\":\"{}\",\"provenance\":\"{}\",\"commit\":\"{}\"}}"
            ),
            self.enstrophy,
            self.vorticity_rms,
            self.localization,
            self.prediction,
            self.confidence,
            self.ood_score,
            self.abstained,
            self.abstention_reason,
            self.calibration_profile,
            self.provenance,
            self.commit,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn base() -> AnalysisResult {
        AnalysisResult {
            enstrophy: 1.0,
            vorticity_rms: 1.4,
            localization: 0.2,
            prediction: 0.9,
            confidence: 0.8,
            ood_score: 1.0,
            abstained: false,
            abstention_reason: String::new(),
            calibration_profile: "in-domain".to_string(),
            provenance: "test".to_string(),
            commit: "abc".to_string(),
        }
    }

    #[test]
    fn valid_alarm_is_not_bare() {
        assert!(!base().is_bare_alarm());
    }

    #[test]
    fn alarm_without_provenance_is_bare() {
        let mut r = base();
        r.provenance = "unknown".to_string();
        assert!(r.is_bare_alarm());
    }

    #[test]
    fn abstained_is_never_an_alarm() {
        let mut r = base();
        r.abstained = true;
        r.provenance = "unknown".to_string();
        assert!(!r.is_bare_alarm());
    }

    #[test]
    fn json_has_fixed_keys() {
        let json = base().to_json();
        assert!(json.starts_with("{\"enstrophy\":"));
        assert!(json.contains("\"provenance\":\"test\""));
    }
}
