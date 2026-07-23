"""CLI: ``python -m itd_research.validation_lab run --config <toml> --output DIR``.

Runs the deterministic channel-dependence (H11) and candidate-ablation (H12)
studies on the local 3D flow catalogue and writes a JSON report. In ``run`` it
checks a small set of robust invariants (the genuinely-3D channels stay
non-redundant; the sample count is reproducible) and exits non-zero on violation.
The scientific *findings* (which candidate wins, correlation values) are reported,
not asserted -- negative results are valid.
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

from itd_research.reporting import (
    environment_metadata,
    prepare_output_directory,
    write_json,
)
from itd_research.validation_lab.ablation import evaluate_candidate
from itd_research.validation_lab.candidates import CANDIDATES, Candidate
from itd_research.validation_lab.flows import lab_flows
from itd_research.validation_lab.sampling import sample_channels_from_flows
from itd_research.validation_lab.statistics import channel_dependence


def _baselines() -> dict[str, Candidate]:
    return {
        "intensity_only": Candidate("baseline-intensity", ("intensity",), "single-channel baseline"),
        "enstrophy_localization": Candidate(
            "baseline-enstrophy+localization", ("intensity", "localization"), "two-channel baseline"
        ),
    }


def _run(config: dict[str, object], output: Path) -> tuple[dict[str, object], list[str]]:
    sampling_config = config.get("sampling", {})
    assert isinstance(sampling_config, dict)
    nodes = int(sampling_config.get("nodes", 24))
    subcubes = int(sampling_config.get("subcubes_per_axis", 3))

    flows = lab_flows(nodes=nodes)
    samples = sample_channels_from_flows(flows, subcubes_per_axis=subcubes)
    dependence = channel_dependence(samples.matrix, samples.channels)

    candidates = dict(CANDIDATES)
    candidates.update(_baselines())
    ablation = [evaluate_candidate(samples, candidate).as_dict() for candidate in candidates.values()]

    report: dict[str, object] = {
        "environment": environment_metadata(),
        "flows": [{"name": f.name, "family": f.family} for f in flows],
        "n_samples": int(samples.matrix.shape[0]),
        "channel_dependence": dependence.as_dict(),
        "ablation_family_classification": ablation,
        "note": (
            "Ablation is leave-one-flow-out family classification (nearest standardized "
            "centroid). Findings are reported, not asserted; on this small controlled set "
            "the simple baselines may match or beat the full candidate."
        ),
    }

    failures: list[str] = []
    vif = dict(zip(dependence.channels, dependence.vif, strict=True))
    # Robust, reproducible invariant: the genuinely-3D channels are non-redundant.
    for channel in ("stretching_rate", "normalized_helicity"):
        if vif[channel] > 3.0:
            failures.append(f"H11 invariant: {channel} VIF {vif[channel]:.1f} > 3 (expected non-redundant)")
    expected_samples = len(flows) * subcubes**3
    if int(samples.matrix.shape[0]) != expected_samples:
        failures.append("sample count not reproducible")
    return report, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="itd_research.validation_lab")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run channel-dependence and ablation studies")
    run.add_argument("--config", required=True)
    run.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)

    config_path = Path(arguments.config)
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    directory = prepare_output_directory(arguments.output)
    report, failures = _run(config, directory)
    write_json(directory, "validation_lab.json", report, overwrite=True)
    if failures:
        print("validation_lab invariants FAILED:")
        for message in failures:
            print(f"  - {message}")
        return 1
    dependence = report["channel_dependence"]
    assert isinstance(dependence, dict)
    print(
        f"validation_lab: {report['n_samples']} samples, effective rank "
        f"{dependence['effective_rank']:.2f}/{len(dependence['channels'])}, invariants PASSED."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
