"""ITD-30.3 deterministic bounded campaign runner contracts.

The runner executes caller-supplied deterministic case evaluators in declared
order.  It enforces campaign budgets and fails closed on final-evaluation cases
unless an explicit authorization is bound to the exact protocol and final
source identity.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import dataclass

from itd_research.experiment_schema import SourceIdentity, SplitRole
from itd_research.result_schema import CampaignIdentityV1


def _validate_sha256(name: str, value: str) -> str:
    digest = value.lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be a SHA-256 hex digest.")
    return digest


@dataclass(frozen=True)
class CampaignCaseV1:
    """One immutable case in a bounded campaign."""

    case_id: str
    role: SplitRole
    input_source: SourceIdentity
    work_units: float

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        if not math.isfinite(self.work_units) or self.work_units <= 0.0:
            raise ValueError("work_units must be finite and positive.")

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "role": self.role.value,
            "input_source": self.input_source.as_dict(),
            "work_units": self.work_units,
        }


@dataclass(frozen=True)
class FinalEvaluationAuthorizationV1:
    """External authorization bound to one exact final source and protocol."""

    protocol_fingerprint: str
    final_source: SourceIdentity
    authorization_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "protocol_fingerprint",
            _validate_sha256("protocol_fingerprint", self.protocol_fingerprint),
        )
        object.__setattr__(
            self,
            "authorization_sha256",
            _validate_sha256("authorization_sha256", self.authorization_sha256),
        )


@dataclass(frozen=True)
class CampaignPlanV1:
    """Deterministic campaign plan with a frozen total work budget."""

    campaign: CampaignIdentityV1
    cases: tuple[CampaignCaseV1, ...]
    work_unit: str
    maximum_total_work: float
    plan_version: str = "itd-campaign-plan-v1"

    def __post_init__(self) -> None:
        if self.plan_version != "itd-campaign-plan-v1":
            raise ValueError("unsupported campaign plan version.")
        if not self.work_unit.strip():
            raise ValueError("work_unit must not be empty.")
        if not math.isfinite(self.maximum_total_work) or self.maximum_total_work <= 0.0:
            raise ValueError("maximum_total_work must be finite and positive.")
        if not self.cases:
            raise ValueError("campaign plan must contain at least one case.")

        identifiers = tuple(case.case_id for case in self.cases)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("campaign case identifiers must be unique.")
        declared_work = sum(case.work_units for case in self.cases)
        if declared_work > self.maximum_total_work:
            raise ValueError("declared campaign work exceeds maximum_total_work.")

    def as_dict(self) -> dict[str, object]:
        return {
            "plan_version": self.plan_version,
            "campaign": self.campaign.as_dict(),
            "cases": [case.as_dict() for case in self.cases],
            "work_unit": self.work_unit,
            "maximum_total_work": self.maximum_total_work,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def assert_final_authorized(
        self,
        authorization: FinalEvaluationAuthorizationV1 | None,
    ) -> None:
        final_cases = tuple(case for case in self.cases if case.role is SplitRole.FINAL)
        if not final_cases:
            return
        if authorization is None:
            raise ValueError("final campaign cases require explicit authorization.")
        if authorization.protocol_fingerprint != self.campaign.protocol_fingerprint:
            raise ValueError("final authorization protocol does not match campaign.")
        for case in final_cases:
            if case.input_source != authorization.final_source:
                raise ValueError("final case source does not match final authorization.")


@dataclass(frozen=True)
class CaseExecutionV1:
    """Observed result from one case evaluator."""

    case_id: str
    output_sha256: str
    work_units_used: float

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty.")
        object.__setattr__(
            self,
            "output_sha256",
            _validate_sha256("output_sha256", self.output_sha256),
        )
        if not math.isfinite(self.work_units_used) or self.work_units_used < 0.0:
            raise ValueError("work_units_used must be finite and non-negative.")

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "output_sha256": self.output_sha256,
            "work_units_used": self.work_units_used,
        }


@dataclass(frozen=True)
class CampaignRunV1:
    """Replayable execution record for one exact campaign plan."""

    plan_fingerprint: str
    executions: tuple[CaseExecutionV1, ...]
    run_version: str = "itd-campaign-run-v1"

    def __post_init__(self) -> None:
        if self.run_version != "itd-campaign-run-v1":
            raise ValueError("unsupported campaign run version.")
        object.__setattr__(
            self,
            "plan_fingerprint",
            _validate_sha256("plan_fingerprint", self.plan_fingerprint),
        )
        identifiers = tuple(item.case_id for item in self.executions)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("campaign execution identifiers must be unique.")

    def assert_replay_of(self, plan: CampaignPlanV1) -> None:
        if self.plan_fingerprint != plan.fingerprint():
            raise ValueError("campaign run does not match plan fingerprint.")
        expected = tuple(case.case_id for case in plan.cases)
        observed = tuple(item.case_id for item in self.executions)
        if observed != expected:
            raise ValueError("campaign execution order does not match plan.")

    def as_dict(self) -> dict[str, object]:
        return {
            "run_version": self.run_version,
            "plan_fingerprint": self.plan_fingerprint,
            "executions": [item.as_dict() for item in self.executions],
        }

    def fingerprint(self) -> str:
        payload = json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


CaseEvaluator = Callable[[CampaignCaseV1], CaseExecutionV1]


def run_bounded_campaign(
    plan: CampaignPlanV1,
    evaluator: CaseEvaluator,
    *,
    final_authorization: FinalEvaluationAuthorizationV1 | None = None,
) -> CampaignRunV1:
    """Run all cases in frozen order while enforcing per-case and total budgets."""

    plan.assert_final_authorized(final_authorization)
    executions: list[CaseExecutionV1] = []
    total_work = 0.0

    for case in plan.cases:
        execution = evaluator(case)
        if execution.case_id != case.case_id:
            raise ValueError("case evaluator returned a mismatched case_id.")
        if execution.work_units_used > case.work_units:
            raise ValueError("case evaluator exceeded its declared work budget.")
        total_work += execution.work_units_used
        if total_work > plan.maximum_total_work:
            raise ValueError("campaign evaluator exceeded maximum_total_work.")
        executions.append(execution)

    run = CampaignRunV1(
        plan_fingerprint=plan.fingerprint(),
        executions=tuple(executions),
    )
    run.assert_replay_of(plan)
    return run
