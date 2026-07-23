"""Explicit, evidence-anchored IRL maturity rubric and gap analysis (research, H16).

The assessment is a fixed, transparent rubric evaluated against **observable facts**
about this repository (deterministic core, oracle fixtures, offline CI, honest-scope
reports). Each criterion carries an explicit ``met`` / ``partial`` / ``unmet`` status
with an evidence pointer. Nothing here is auto-inflated: the level is the highest rung
whose criteria are all met, and the report lists every gap above it. This is a
maturity *self-assessment*, not a certification.
"""

from __future__ import annotations

from dataclasses import dataclass

# Integration/Industrial Readiness Level scale used throughout the reports.
IRL_SCALE: tuple[tuple[int, str], ...] = (
    (0, "idea / equations only"),
    (1, "reference implementation, ad hoc checks"),
    (2, "deterministic implementation with an automated test suite"),
    (3, "oracle-anchored numerics + offline reproducible CI"),
    (4, "falsifiable validation against independent diagnostics, honest scope"),
    (5, "external empirical validation (DNS/PIV) at matched conditions"),
    (6, "documented interfaces + performance envelope + versioned data contracts"),
    (7, "quality-managed process (reviews, change control, requirements trace)"),
    (8, "sector standard gap-closed, independent V&V, safety case"),
    (9, "formally certified for a regulated deployment"),
)


@dataclass(frozen=True)
class ReadinessCriterion:
    """One rubric criterion at a given IRL rung."""

    level: int
    requirement: str
    status: str  # "met" | "partial" | "unmet"
    evidence: str

    def as_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "requirement": self.requirement,
            "status": self.status,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class StandardGap:
    """A named external standard and what is missing to satisfy it."""

    standard: str
    scope: str
    status: str  # always "not satisfied" here; scientific validation != compliance
    missing: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "standard": self.standard,
            "scope": self.scope,
            "status": self.status,
            "missing": list(self.missing),
        }


@dataclass(frozen=True)
class ReadinessAssessment:
    """The overall maturity assessment."""

    achieved_level: int
    criteria: tuple[ReadinessCriterion, ...]
    next_gaps: tuple[ReadinessCriterion, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "achieved_level": self.achieved_level,
            "achieved_label": dict(IRL_SCALE)[self.achieved_level],
            "criteria": [c.as_dict() for c in self.criteria],
            "next_gaps": [c.as_dict() for c in self.next_gaps],
        }


_CRITERIA: tuple[ReadinessCriterion, ...] = (
    ReadinessCriterion(
        2, "deterministic implementation with an automated test suite", "met",
        "V29.18 core is deterministic; pytest suite; Rust oracle fixtures.",
    ),
    ReadinessCriterion(
        3, "oracle-anchored numerics + offline reproducible CI", "met",
        "Analytical oracles (Gate A), fixed seeds/threads, offline run_validation.sh in CI.",
    ),
    ReadinessCriterion(
        4, "falsifiable validation against independent diagnostics, honest scope", "met",
        "H1-H16 reported as falsifiable questions with negative/partial verdicts; "
        "comparison against Q/lambda2/swirl/enstrophy baselines.",
    ),
    ReadinessCriterion(
        5, "external empirical validation (DNS/PIV) at matched conditions", "partial",
        "External DNS/PIV comparisons exist on queried/synthetic data; no matched-condition "
        "quantitative validation against a governed external raw dataset in the authoritative path.",
    ),
    ReadinessCriterion(
        6, "documented interfaces + performance envelope + versioned data contracts", "partial",
        "Real-time envelope (H15) and a Rust interface spec are documented; a versioned, "
        "checksummed external data contract is only partially in place.",
    ),
    ReadinessCriterion(
        7, "quality-managed process (reviews, change control, requirements trace)", "unmet",
        "No formal requirements traceability matrix, controlled review records, or CM plan.",
    ),
    ReadinessCriterion(
        8, "sector standard gap-closed, independent V&V, safety case", "unmet",
        "No independent verification & validation; no safety case; see standard gaps.",
    ),
    ReadinessCriterion(
        9, "formally certified for a regulated deployment", "unmet",
        "No accredited certification of any kind.",
    ),
)


def assess_readiness() -> ReadinessAssessment:
    """Return the honest maturity level: the highest rung with all criteria met."""
    achieved = 1  # a reference implementation with ad hoc checks is the floor
    for criterion in _CRITERIA:
        if criterion.status == "met":
            achieved = max(achieved, criterion.level)
        else:
            break
    next_gaps = tuple(c for c in _CRITERIA if c.level > achieved or c.status != "met")
    return ReadinessAssessment(achieved, _CRITERIA, next_gaps)


def standard_gaps() -> tuple[StandardGap, ...]:
    """Named-standard gap analysis. Every status is 'not satisfied' by construction."""
    return (
        StandardGap(
            "ISO 9001", "quality management systems", "not satisfied",
            ("documented QMS", "controlled records", "management review", "internal audit"),
        ),
        StandardGap(
            "ISO/IEC 17025", "testing & calibration laboratory competence", "not satisfied",
            ("measurement uncertainty budget", "method validation records", "accreditation"),
        ),
        StandardGap(
            "IEC 61508", "functional safety of E/E/PE systems", "not satisfied",
            ("hazard & risk analysis", "SIL allocation", "safety lifecycle", "independent assessment"),
        ),
        StandardGap(
            "ISO 26262", "road-vehicle functional safety", "not satisfied",
            ("item definition", "ASIL decomposition", "safety case", "tool qualification"),
        ),
        StandardGap(
            "DO-178C", "airborne software", "not satisfied",
            ("DAL assignment", "requirements/design/code traceability", "MC/DC coverage", "DER review"),
        ),
        StandardGap(
            "IEC 62304", "medical device software lifecycle", "not satisfied",
            ("software safety classification", "risk management file", "SOUP analysis"),
        ),
    )
