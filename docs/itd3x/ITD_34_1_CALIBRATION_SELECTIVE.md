# ITD-34.1 — Calibration and selective prediction

Status: **implementation slice active**

## Calibration

`calibration_summary` computes two deterministic measurements from declared confidence/correctness pairs:

- equal-width expected calibration error (ECE);
- binary Brier score.

The function does not fit confidence values or choose bin count from final results. The caller must freeze the bin count when the experiment requires preregistration.

Only populated bins are reported, with explicit bounds, sample count, mean confidence and empirical accuracy.

## Selective prediction

`risk_coverage_curve` evaluates an explicit strictly increasing threshold sequence using the ITD-34.0 selective-risk primitive.

Each point reports:

- threshold;
- coverage;
- selective risk;
- false confidence on OOD samples.

The function does not search for a favorable threshold.

## Risk/coverage area

`trapezoidal_risk_coverage_area` integrates risk only over the coverage interval actually represented by the supplied points. It is not silently relabeled as a full-domain AURC if the thresholds do not span the full range.

## Boundary

These are generic evaluation primitives. They do not make ITD descriptors probabilistic uncertainties and must be compared with competent non-ITD UQ baselines.
