"""CLI: ``python -m itd_research.ood {validate,run} --output DIR``.

Fits the OOD reference on in-distribution vortex-merger features, then scores genuinely
different flows -- a 3D Taylor-Green midplane (different solver/physics) and the real
biofilm PIV field (shear-dominated) -- as out-of-distribution. Reports OOD detection
quality and whether abstaining on high-OOD samples lowers selective risk without
collapsing in-domain coverage (H23). ``validate`` is a tiny CI form.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from itd_research.hard_prediction.evaluation import build_labeled
from itd_research.hard_prediction.flows import (
    ALL_FEATURES,
    extract_features_2d,
    features_from_raw,
    simulate_merger_raw,
    simulate_taylorgreen_raw,
)
from itd_research.hard_prediction.models import LogisticRegression
from itd_research.ood.abstention import abstention_benefit, risk_coverage_curve
from itd_research.ood.reference import fit_reference
from itd_research.prediction.evaluation import roc_auc
from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)

_ROOT = Path(__file__).resolve().parents[2]
_BIOFILM = _ROOT / "tests" / "fixtures" / "external" / "biofilm_piv_excerpt.npz"


def _feature_matrix(run) -> np.ndarray:  # type: ignore[no-untyped-def]
    return np.column_stack([run.features[name] for name in ALL_FEATURES])


def _biofilm_samples() -> np.ndarray:
    data = np.load(_BIOFILM)
    u, v, x = data["u"], data["v"], data["x"]
    spacing = float(abs(x[1] - x[0])) if x.size > 1 else 1.0
    ny, nx = u.shape
    rows = []
    # the whole field plus four quadrant sub-windows -> a few real OOD samples
    windows = [(slice(None), slice(None))]
    windows += [(slice(a, a + ny // 2), slice(b, b + nx // 2)) for a in (0, ny // 2) for b in (0, nx // 2)]
    for sy, sx in windows:
        feats = extract_features_2d(np.ascontiguousarray(u[sy, sx]), np.ascontiguousarray(v[sy, sx]), spacing)
        rows.append([feats[name] for name in ALL_FEATURES])
    return np.asarray(rows, dtype=np.float64)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.ood")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        p = sub.add_parser(name)
        p.add_argument("--output", required=True)
        p.add_argument("--quick", action="store_true")
    arguments = parser.parse_args(argv)
    quick = arguments.command == "validate" or arguments.quick

    merger_kwargs = {"nodes": 56, "steps": 2000, "record_every": 100} if quick else {}
    tg_kwargs = {"nodes": 16, "steps": 700, "record_every": 50} if quick else {}
    in_seeds = (10, 11, 12) if quick else (10, 11, 12, 13)
    test_seed = 14
    tg_seeds = (90,) if quick else (90, 91)

    in_runs = [features_from_raw(simulate_merger_raw(s, **merger_kwargs)) for s in in_seeds]
    in_matrix = np.vstack([_feature_matrix(r) for r in in_runs])
    reference = fit_reference(in_matrix)

    # In-domain error signal: train established+ITD on in-dist, error on a held-out merger.
    dev = build_labeled(in_runs, horizon_frames=4)
    test_run = features_from_raw(simulate_merger_raw(test_seed, **merger_kwargs))
    test_labeled = build_labeled([test_run], horizon_frames=4)
    from itd_research.hard_prediction.evaluation import (
        _matrix as _lab_matrix,  # noqa: PLC0415
    )

    train_x, train_y = _lab_matrix(dev, ALL_FEATURES)
    mean, std = train_x.mean(axis=0), train_x.std(axis=0)
    std = np.where(std < 1e-12, 1.0, std)
    model = LogisticRegression().fit((train_x - mean) / std, train_y.astype(np.float64))
    if test_labeled:
        tx, ty = _lab_matrix(test_labeled, ALL_FEATURES)
        preds = model.predict_proba((tx - mean) / std)
        in_error = np.abs(preds - ty)
        in_features = tx
    else:
        in_features = in_matrix
        in_error = np.full(in_matrix.shape[0], 0.1)

    # OOD samples: Taylor-Green midplane frames + real biofilm PIV.
    tg_runs = [features_from_raw(simulate_taylorgreen_raw(s, **tg_kwargs)) for s in tg_seeds]
    tg_matrix = np.vstack([_feature_matrix(r) for r in tg_runs])
    piv_matrix = _biofilm_samples()
    ood_features = np.vstack([tg_matrix, piv_matrix])
    ood_error = np.ones(ood_features.shape[0])  # any confident prediction here is unjustified

    features = np.vstack([in_features, ood_features])
    error = np.concatenate([in_error, ood_error])
    is_ood = np.concatenate([np.zeros(in_features.shape[0], bool), np.ones(ood_features.shape[0], bool)])
    scores = reference.score(features)

    detection_auc = roc_auc(scores, is_ood.astype(np.int64))
    result, supported, verdict = abstention_benefit(scores, error, is_ood)
    curve = risk_coverage_curve(scores, error)

    report = {
        "environment": environment_metadata(),
        "quick": quick,
        "n_in_domain": int(in_features.shape[0]),
        "n_ood_taylorgreen": int(tg_matrix.shape[0]),
        "n_ood_piv": int(piv_matrix.shape[0]),
        "mean_score_in_domain": float(np.mean(scores[~is_ood])),
        "mean_score_ood": float(np.mean(scores[is_ood])),
        "ood_detection_auc": detection_auc,
        "selective": result.as_dict(),
        "risk_coverage_curve": [{"coverage": c, "selective_risk": r} for c, r in curve],
        "h23_verdict": verdict,
    }
    directory = prepare_output_directory(arguments.output)
    write_json(directory, "ood.json", report, overwrite=True)

    print(f"ood: in-domain={in_features.shape[0]} ood(TG)={tg_matrix.shape[0]} ood(PIV)={piv_matrix.shape[0]}")
    print(f"  mean OOD score in-domain={np.mean(scores[~is_ood]):.2f} ood={np.mean(scores[is_ood]):.2f} "
          f"detection AUC={detection_auc:.3f}")
    print(f"  abstention: coverage={result.coverage:.2f} selective_risk={result.selective_risk:.3f} "
          f"full_risk={result.full_risk:.3f} false_conf={result.false_confidence_rate:.3f}")
    print(f"  H23 verdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
