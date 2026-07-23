"""Bidirectional competent-baseline cross-code transfer (research, Mission 6, H37-H42).

Trains a leakage-safe predictor on one solver's Taylor-Green runs and evaluates it on
the other solver's runs, in BOTH directions, under several fair normalizations. The
decisive tests are:

* **H38** -- does ITD still beat a *competent* established baseline? The Mission 5
  established diagnostics anti-transferred (AUC ~0.03) because they are scale/amplitude
  dependent across codes. Here we give the established baseline its best fair shot: a
  normalization is *selected on development folds only* to MAXIMISE the established
  cross-code AUC, then ITD is compared against that competent baseline on the holdout.
* **H39** -- does adding ITD to the competent baseline add credible value (paired
  grouped bootstrap, margin 0.02, CI excludes 0)?

Selecting the normalization that helps the *established* baseline most is deliberately
adversarial to ITD: if a normalized established baseline transfers just as well, ITD's
Mission 5 advantage was normalization, not structure (the honest, likely outcome). Train
and test always use disjoint seeds so a seed's two-code runs never leak across the split.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from itd_research.cross_code.comparison import simulate_taylorgreen_fd_raw
from itd_research.cross_code.normalization import METHODS, normalize_runs
from itd_research.hard_prediction.evaluation import (
    added_value,
    build_labeled,
    feature_set_auc,
)
from itd_research.hard_prediction.flows import (
    ESTABLISHED_FEATURES,
    ITD_FEATURES,
    HardRun,
    features_from_raw,
    simulate_taylorgreen_raw,
)

_ITD_STRUCTURAL = ("heterogeneity", "localization", "roughness", "sign_mixing", "temporal_deformation")
_ESTABLISHED = tuple(ESTABLISHED_FEATURES)
_ITD_FULL = tuple(ITD_FEATURES)
_AUG = _ESTABLISHED + _ITD_FULL
_DIRECTIONS = ("spectral_to_fd", "fd_to_spectral")


def transfer_auc(
    train_runs: list[HardRun], test_runs: list[HardRun], names: tuple[str, ...],
    method: str, horizon: int = 4,
) -> float:
    """Held-out cross-code AUC for a feature set under a normalization method."""
    dev = build_labeled(normalize_runs(train_runs, method), horizon)
    holdout = build_labeled(normalize_runs(test_runs, method), horizon)
    if not dev or not holdout:
        return float("nan")
    return feature_set_auc(dev, holdout, names)


@dataclass(frozen=True)
class DirectionResult:
    """One transfer direction: AUCs by feature set, plus the competent added-value."""

    direction: str
    normalization: str
    established_raw_auc: float
    established_competent_auc: float
    itd_structural_auc: float
    itd_full_auc: float
    combined_auc: float
    added_value_diff: float
    added_value_ci_low: float
    added_value_ci_high: float
    added_value_verdict: str
    competent_above_chance: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "direction": self.direction,
            "normalization": self.normalization,
            "established_raw_auc": self.established_raw_auc,
            "established_competent_auc": self.established_competent_auc,
            "itd_structural_auc": self.itd_structural_auc,
            "itd_full_auc": self.itd_full_auc,
            "combined_auc": self.combined_auc,
            "added_value_diff": self.added_value_diff,
            "added_value_ci_low": self.added_value_ci_low,
            "added_value_ci_high": self.added_value_ci_high,
            "added_value_verdict": self.added_value_verdict,
            "competent_above_chance": self.competent_above_chance,
        }


def evaluate_direction(
    train_runs: list[HardRun], test_runs: list[HardRun], direction: str,
    competent_method: str, *, horizon: int = 4, bootstrap: int = 2000,
) -> DirectionResult:
    """Evaluate one transfer direction with a competent (normalized) baseline."""
    raw_established = transfer_auc(train_runs, test_runs, _ESTABLISHED, "raw", horizon)
    competent_established = transfer_auc(train_runs, test_runs, _ESTABLISHED, competent_method, horizon)
    itd_structural = transfer_auc(train_runs, test_runs, _ITD_STRUCTURAL, competent_method, horizon)
    itd_full = transfer_auc(train_runs, test_runs, _ITD_FULL, competent_method, horizon)
    combined = transfer_auc(train_runs, test_runs, _AUG, competent_method, horizon)

    # H39 added value: competent+ITD vs competent, on the competent-normalized features.
    dev = build_labeled(normalize_runs(train_runs, competent_method), horizon)
    holdout = build_labeled(normalize_runs(test_runs, competent_method), horizon)
    if dev and holdout:
        value = added_value(dev, holdout, _ESTABLISHED, _AUG, margin=0.02, bootstrap=bootstrap)
        diff, lo, hi, verdict = value.diff_mean, value.diff_ci_low, value.diff_ci_high, value.verdict
    else:
        diff = lo = hi = float("nan")
        verdict = "inconclusive"

    return DirectionResult(
        direction=direction, normalization=competent_method,
        established_raw_auc=raw_established, established_competent_auc=competent_established,
        itd_structural_auc=itd_structural, itd_full_auc=itd_full, combined_auc=combined,
        added_value_diff=diff, added_value_ci_low=lo, added_value_ci_high=hi,
        added_value_verdict=verdict,
        competent_above_chance=(not np.isnan(competent_established)) and competent_established > 0.5,
    )


_COMPETENT_METHODS = tuple(m for m in METHODS if m != "raw")


def select_competent_method(
    spec_train: list[HardRun], fd_train: list[HardRun],
    spec_devtest: list[HardRun], fd_devtest: list[HardRun],
    *, methods: tuple[str, ...] = _COMPETENT_METHODS, horizon: int = 4,
) -> tuple[str, dict[str, float]]:
    """Pick the normalization that MAXIMISES the established baseline on DEV folds.

    Candidates are the genuinely *normalized* baselines (``raw`` is excluded -- it is the
    degenerate Mission 5 reference, reported separately). Selection trains on the dev-train
    seeds and scores the disjoint dev-test seeds, for both directions, and never touches
    the final-holdout seeds. Maximising the established AUC (not ITD's) gives the baseline
    its fair shot; a below-chance method is never selected over an above-chance one because
    we maximise AUC, not |AUC-0.5|.
    """
    table: dict[str, float] = {}
    for method in methods:
        aucs: list[float] = []
        for direction in _DIRECTIONS:
            spec_tr, fd_te = (spec_train, fd_devtest) if direction == "spectral_to_fd" else (fd_train, spec_devtest)
            aucs.append(transfer_auc(spec_tr, fd_te, _ESTABLISHED, method, horizon))
        finite = [a for a in aucs if not np.isnan(a)]
        table[method] = float(np.mean(finite)) if finite else float("nan")
    ranked = [m for m in methods if not np.isnan(table[m])]
    best = max(ranked, key=lambda m: table[m]) if ranked else "raw"
    return best, table


@dataclass(frozen=True)
class CampaignResult:
    """Development selection plus the single competent-baseline holdout evaluation."""

    competent_method_selected: str
    dev_established_auc_by_method: dict[str, float]
    holdout_directions: list[DirectionResult] = field(default_factory=list)
    descriptive_holdout: list[dict[str, object]] = field(default_factory=list)
    quick: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "competent_method_selected": self.competent_method_selected,
            "dev_established_auc_by_method": self.dev_established_auc_by_method,
            "holdout_directions": [d.as_dict() for d in self.holdout_directions],
            "descriptive_holdout_all_methods": self.descriptive_holdout,
            "quick": self.quick,
        }


def _descriptive_grid(
    spec_dev: list[HardRun], fd_dev: list[HardRun],
    spec_holdout: list[HardRun], fd_holdout: list[HardRun],
    methods: tuple[str, ...], horizon: int,
) -> list[dict[str, object]]:
    """All-methods x both-directions holdout AUCs, for TRANSPARENCY only.

    This descriptive table is *not* used to pick the verdict -- the competent baseline is
    the dev-selected method (never re-chosen on the holdout). It exists so a reader can see
    that no hidden normalization made the established baseline look better.
    """
    rows: list[dict[str, object]] = []
    for direction in _DIRECTIONS:
        train_runs, test_runs = (
            (spec_dev, fd_holdout) if direction == "spectral_to_fd" else (fd_dev, spec_holdout)
        )
        for method in methods:
            rows.append({
                "direction": direction,
                "normalization": method,
                "established_auc": transfer_auc(train_runs, test_runs, _ESTABLISHED, method, horizon),
                "itd_structural_auc": transfer_auc(train_runs, test_runs, _ITD_STRUCTURAL, method, horizon),
                "itd_full_auc": transfer_auc(train_runs, test_runs, _ITD_FULL, method, horizon),
            })
    return rows


def _simulate(kind: str, seeds: tuple[int, ...], quick: bool) -> list[HardRun]:
    kwargs = {"nodes": 16, "steps": 500, "record_every": 40} if quick else {}
    sim = simulate_taylorgreen_raw if kind == "spectral" else simulate_taylorgreen_fd_raw
    return [features_from_raw(sim(s, **kwargs)) for s in seeds]


def run_competent_campaign(
    *, quick: bool = False, horizon: int = 4, bootstrap: int = 2000,
    methods: tuple[str, ...] = METHODS,
) -> CampaignResult:
    """Bidirectional competent-baseline cross-code campaign (H37-H42).

    1. Simulate both codes on the dev seeds (split into dev-train / dev-test) and the
       holdout seeds. 2. Select the competent normalization on dev folds only. 3. Evaluate
       that single method on the holdout, both directions -- the decisive H38/H39 numbers.
    """
    dev_train_seeds: tuple[int, ...]
    dev_test_seeds: tuple[int, ...]
    holdout_seeds: tuple[int, ...]
    if quick:
        dev_train_seeds, dev_test_seeds, holdout_seeds = (10, 11), (12, 13), (90, 91, 92)
        boot = 200
    else:
        dev_train_seeds, dev_test_seeds, holdout_seeds = (10, 11, 12), (13, 14, 15), (90, 91, 92, 93, 94, 95)
        boot = bootstrap

    competent_candidates = tuple(m for m in methods if m != "raw")

    spec_train = _simulate("spectral", dev_train_seeds, quick)
    fd_train = _simulate("fd", dev_train_seeds, quick)
    spec_devtest = _simulate("spectral", dev_test_seeds, quick)
    fd_devtest = _simulate("fd", dev_test_seeds, quick)

    selected, dev_table = select_competent_method(
        spec_train, fd_train, spec_devtest, fd_devtest, methods=competent_candidates, horizon=horizon
    )

    # Final holdout: train on ALL dev seeds, score the disjoint holdout seeds. Evaluated once.
    spec_dev_all = spec_train + spec_devtest
    fd_dev_all = fd_train + fd_devtest
    spec_holdout = _simulate("spectral", holdout_seeds, quick)
    fd_holdout = _simulate("fd", holdout_seeds, quick)

    holdout_directions = []
    for direction in _DIRECTIONS:
        if direction == "spectral_to_fd":
            train_runs, test_runs = spec_dev_all, fd_holdout
        else:
            train_runs, test_runs = fd_dev_all, spec_holdout
        holdout_directions.append(
            evaluate_direction(train_runs, test_runs, direction, selected, horizon=horizon, bootstrap=boot)
        )

    descriptive = _descriptive_grid(
        spec_dev_all, fd_dev_all, spec_holdout, fd_holdout, methods, horizon
    )

    return CampaignResult(
        competent_method_selected=selected,
        dev_established_auc_by_method=dev_table,
        holdout_directions=holdout_directions,
        descriptive_holdout=descriptive,
        quick=quick,
    )
