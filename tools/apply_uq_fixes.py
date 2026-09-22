from pathlib import Path

p = Path('itd_research/uq.py')
s = p.read_text()
s = s.replace('from dataclasses import dataclass\n', 'from dataclasses import dataclass\n\nimport numpy as np\n')
start = s.index('@dataclass(frozen=True)\nclass SelectiveRiskPoint:')
end = s.index('\n\n@dataclass(frozen=True)\nclass CalibrationBin:')
s = s[:start] + '''def _boolean_flags(values: Sequence[bool], name: str) -> tuple[bool, ...]:
    """Accept actual Python/NumPy booleans, never truthy strings or numbers."""
    if any(not isinstance(value, (bool, np.bool_)) for value in values):
        raise ValueError(f"{name} must contain only boolean flags.")
    return tuple(bool(value) for value in values)


def _nonnegative_mean(values: Sequence[float]) -> float:
    """Avoid overflow of a finite non-negative mean's intermediate sum."""
    scale = max(values)
    if scale == 0.0:
        return 0.0
    return scale * (math.fsum(value / scale for value in values) / len(values))


@dataclass(frozen=True)
class SelectiveRiskPoint:
    """Conditional ratios use None when their denominator is absent."""

    threshold: float
    coverage: float
    selective_risk: float | None
    false_confidence: float | None

    def __post_init__(self) -> None:
        for name, value in (("threshold", self.threshold), ("coverage", self.coverage)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError("coverage must be in [0, 1].")
        if self.coverage == 0.0:
            if self.selective_risk is not None:
                raise ValueError("selective_risk must be undefined at zero coverage.")
        elif self.selective_risk is None:
            raise ValueError("selective_risk is required at positive coverage.")
        if self.selective_risk is not None and (
            not math.isfinite(self.selective_risk) or self.selective_risk < 0.0
        ):
            raise ValueError("selective_risk must be finite and non-negative when defined.")
        if self.false_confidence is not None and (
            not math.isfinite(self.false_confidence)
            or not 0.0 <= self.false_confidence <= 1.0
        ):
            raise ValueError("false_confidence must be finite and in [0, 1] when defined.")


def selective_risk_point(
    scores: Sequence[float],
    errors: Sequence[float],
    is_ood: Sequence[bool],
    *,
    threshold: float,
) -> SelectiveRiskPoint:
    """Evaluate one deterministic abstention threshold without fitting it.

    Samples with score <= threshold are covered. Errors must be finite and
    non-negative. Risk is the mean error among covered samples, or None when
    coverage is zero. False confidence is the fraction of OOD samples covered,
    or None when no OOD sample exists. Neither absence is a measured zero.
    """

    if not math.isfinite(threshold):
        raise ValueError("threshold must be finite.")
    if not (len(scores) == len(errors) == len(is_ood)):
        raise ValueError("scores, errors and is_ood must have equal length.")
    if len(scores) == 0:
        raise ValueError("at least one sample is required.")

    normalized_scores = tuple(float(value) for value in scores)
    normalized_errors = tuple(float(value) for value in errors)
    ood_flags = _boolean_flags(is_ood, "is_ood")
    if any(not math.isfinite(value) for value in normalized_scores):
        raise ValueError("scores must be finite.")
    if any(not math.isfinite(value) or value < 0.0 for value in normalized_errors):
        raise ValueError("errors must be finite and non-negative.")

    covered = tuple(score <= threshold for score in normalized_scores)
    covered_errors = tuple(
        error for error, keep in zip(normalized_errors, covered, strict=True) if keep
    )
    ood_count = sum(ood_flags)
    covered_ood = sum(keep and ood for keep, ood in zip(covered, ood_flags, strict=True))
    return SelectiveRiskPoint(
        threshold=threshold,
        coverage=len(covered_errors) / len(covered),
        selective_risk=_nonnegative_mean(covered_errors) if covered_errors else None,
        false_confidence=covered_ood / ood_count if ood_count else None,
    )
''' + s[end:]
s = s.replace('    if not confidence:\n', '    if len(confidence) == 0:\n')
s = s.replace('    if bin_count < 1:\n        raise ValueError("bin_count must be positive.")', '    if type(bin_count) is not int or bin_count < 1:\n        raise ValueError("bin_count must be a positive integer.")')
s = s.replace('    outcomes = tuple(bool(value) for value in correct)', '    outcomes = _boolean_flags(correct, "correct")')
s = s.replace('        mean_confidence = sum(bucket_confidence[index]) / len(bucket_confidence[index])', '        mean_confidence = _nonnegative_mean(bucket_confidence[index])')
s = s.replace('    brier = sum(\n', '    brier = math.fsum(\n')
s = s.replace('    """Integrate risk over the covered coverage interval of supplied points."""', '''    """Integrate only the supplied interval, rejecting undefined risk points.

    Zero-coverage points do not define an interpolation endpoint. Callers must
    explicitly choose a measured interval; this function never invents an origin.
    """''')
s = s.replace('    coverages = tuple(point.coverage for point in resolved)', '''    if any(point.selective_risk is None for point in resolved):
        raise ValueError("cannot integrate undefined selective risk.")
    coverages = tuple(point.coverage for point in resolved)''')
s = s.replace('''    area = 0.0
    for left, right in zip(resolved, resolved[1:], strict=False):
        width = right.coverage - left.coverage
        area += width * 0.5 * (left.selective_risk + right.selective_risk)
    return area''', '''    areas = []
    for left, right in zip(resolved, resolved[1:], strict=False):
        if left.selective_risk is None or right.selective_risk is None:
            raise ValueError("cannot integrate undefined selective risk.")
        width = right.coverage - left.coverage
        areas.append(width * (0.5 * left.selective_risk + 0.5 * right.selective_risk))
    return math.fsum(areas)''')
p.write_text(s)
