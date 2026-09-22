from pathlib import Path


def edit(path, old, new, count=1):
    p = Path(path)
    s = p.read_text()
    assert s.count(old) == count, (path, old, s.count(old))
    p.write_text(s.replace(old, new))


edit('itd_research/experiment_schema.py', '    role: SplitRole\n    source: SourceIdentity\n\n    def as_dict', '    role: SplitRole\n    source: SourceIdentity\n\n    def __post_init__(self) -> None:\n        object.__setattr__(self, "role", SplitRole(self.role))\n\n    def as_dict')
edit('itd_research/experiment_schema.py', '        if not self.name.strip():', '        object.__setattr__(self, "role", MetricRole(self.role))\n        object.__setattr__(self, "direction", MetricDirection(self.direction))\n        if not self.name.strip():')
edit('itd_research/experiment_schema.py', '        if not self.experiment_id.strip():', '        object.__setattr__(self, "splits", tuple(self.splits))\n        object.__setattr__(self, "metrics", tuple(self.metrics))\n        if not self.experiment_id.strip():')
edit('itd_research/experiment_schema.py', '        return next(split for split in self.splits if split.role is role)', '        resolved_role = SplitRole(role)\n        return next(split for split in self.splits if split.role is resolved_role)')
edit('itd_research/experiment_schema.py', '        if role is SplitRole.FINAL:', '        if SplitRole(role) is SplitRole.FINAL:')
edit('itd_research/itd3x_tracks.py', '    def assert_allowed(self) -> None:\n        if self.role is SplitRole.FINAL:', '''    def __post_init__(self) -> None:
        object.__setattr__(self, "role", SplitRole(self.role))
        for name, value in (
            ("search_space_frozen", self.search_space_frozen),
            ("compute_budget_frozen", self.compute_budget_frozen),
        ):
            if type(value) is not bool:
                raise ValueError(f"{name} must be a bool.")

    def assert_allowed(self) -> None:
        if self.role is SplitRole.FINAL:''')
for path, cls in {
    'itd_research/forge_search_adapter.py': 'ForgeSearchContractV1',
    'itd_research/neural_operator_adapter.py': 'OperatorSampleRef',
    'itd_research/auxiliary_supervision.py': 'AuxiliaryTrainingArm',
    'itd_research/tdi_trajectory_adapter.py': 'TdiTrajectoryStepRef',
    'itd_research/noiselab_adapter.py': 'NoiseInterventionRef',
    'itd_research/maa_adapter.py': 'MaaRouteRef',
}.items():
    p = Path(path)
    s = p.read_text()
    start = s.index('class ' + cls + ':')
    at = s.index('    def __post_init__(self) -> None:\n', start) + len('    def __post_init__(self) -> None:\n')
    p.write_text(s[:at] + '        object.__setattr__(self, "role", SplitRole(self.role))\n' + s[at:])
edit('itd_research/result_schema.py', '        if not self.campaign_id.strip():', '        object.__setattr__(self, "adapters", tuple(self.adapters))\n        if not self.campaign_id.strip():')
edit('itd_research/result_schema.py', '    @classmethod\n    def from_protocol(', '''    def assert_matches_protocol(self, protocol: ExperimentProtocolV1) -> None:
        """Check the protocol and implementation declared for this campaign."""
        if self.protocol_fingerprint != protocol.fingerprint():
            raise ValueError("campaign protocol fingerprint does not match protocol.")
        if self.implementation != protocol.implementation:
            raise ValueError("campaign implementation does not match protocol.")

    @classmethod
    def from_protocol(''')
edit('itd_research/result_schema.py', '        if not self.experiment_id.strip():', '''        object.__setattr__(self, "study_class", StudyClass(self.study_class))
        object.__setattr__(self, "outcome", StudyOutcome(self.outcome))
        object.__setattr__(self, "observations", tuple(self.observations))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        if not self.experiment_id.strip():''')
edit('itd_research/result_schema.py', '    def assert_matches_protocol(self, protocol: ExperimentProtocolV1) -> None:\n        if self.experiment_id', '''    def assert_matches_campaign(self, campaign: CampaignIdentityV1) -> None:
        """Check both campaign identity and its declared protocol binding.

        Also call assert_matches_protocol with the actual protocol to validate
        the experiment ID and metric declarations; a digest alone is not proof.
        """
        if self.campaign_fingerprint != campaign.fingerprint():
            raise ValueError("result campaign fingerprint does not match campaign.")
        if self.protocol_fingerprint != campaign.protocol_fingerprint:
            raise ValueError("result protocol fingerprint does not match campaign.")

    def assert_matches_protocol(self, protocol: ExperimentProtocolV1) -> None:
        if self.experiment_id''')
edit('itd_research/campaign_runner.py', 'from itd_research.experiment_schema import SourceIdentity, SplitRole', 'from itd_research.experiment_schema import ExperimentProtocolV1, SourceIdentity, SplitRole')
p = Path('itd_research/campaign_runner.py')
s = p.read_text()
start = s.index('class CampaignCaseV1:')
at = s.index('    def __post_init__(self) -> None:\n', start) + len('    def __post_init__(self) -> None:\n')
p.write_text(s[:at] + '        object.__setattr__(self, "role", SplitRole(self.role))\n' + s[at:])
edit('itd_research/campaign_runner.py', '        if self.plan_version != "itd-campaign-plan-v1":', '        object.__setattr__(self, "cases", tuple(self.cases))\n        if self.plan_version != "itd-campaign-plan-v1":')
edit('itd_research/campaign_runner.py', '    def assert_final_authorized(', '''    def assert_matches_protocol(self, protocol: ExperimentProtocolV1) -> None:
        """Bind a plan to actual source identities and its declared budget."""
        self.campaign.assert_matches_protocol(protocol)
        if self.work_unit != protocol.compute_budget.unit:
            raise ValueError("campaign work unit does not match protocol.")
        if self.maximum_total_work > protocol.compute_budget.maximum:
            raise ValueError("campaign budget exceeds protocol budget.")
        for case in self.cases:
            if case.input_source != protocol.split(case.role).source:
                raise ValueError("campaign case source does not match protocol split.")

    def assert_final_authorized(''')
edit('itd_research/campaign_runner.py', '        if self.run_version != "itd-campaign-run-v1":', '        object.__setattr__(self, "executions", tuple(self.executions))\n        if self.run_version != "itd-campaign-run-v1":')
edit('itd_research/campaign_runner.py', '            raise ValueError("campaign execution order does not match plan.")', '''            raise ValueError("campaign execution order does not match plan.")
        total_work = 0.0
        for case, execution in zip(plan.cases, self.executions, strict=True):
            _assert_case_execution(case, execution)
            total_work += execution.work_units_used
        if not math.isfinite(total_work) or total_work > plan.maximum_total_work:
            raise ValueError("recorded campaign exceeds its total work budget.")''')
edit('itd_research/campaign_runner.py', 'CaseEvaluator = Callable[[CampaignCaseV1], CaseExecutionV1]', '''def _assert_case_execution(case: CampaignCaseV1, execution: CaseExecutionV1) -> None:
    """One accounting rule for returned and restored execution records."""
    if not isinstance(execution, CaseExecutionV1):
        raise ValueError("case evaluator must return CaseExecutionV1.")
    if execution.case_id != case.case_id:
        raise ValueError("case evaluator returned a mismatched case_id.")
    if execution.work_units_used > case.work_units:
        raise ValueError("case evaluator exceeded its declared work budget.")


CaseEvaluator = Callable[[CampaignCaseV1], CaseExecutionV1]''')
edit('itd_research/campaign_runner.py', '    final_authorization: FinalEvaluationAuthorizationV1 | None = None,', '    final_authorization: FinalEvaluationAuthorizationV1 | None = None,\n    protocol: ExperimentProtocolV1 | None = None,')
edit('itd_research/campaign_runner.py', '    """Run all cases in frozen order while enforcing per-case and total budgets."""\n\n    plan.assert_final_authorized(final_authorization)', '''    """Run cases in frozen order and check reported work against budgets.

    Supply protocol for source/implementation/budget validation before any case
    runs. Legacy calls without it validate plan metadata only. Neither path
    authenticates external permission or imposes OS CPU/RAM/time containment.
    """

    if protocol is not None:
        plan.assert_matches_protocol(protocol)
    plan.assert_final_authorized(final_authorization)
    plan_fingerprint = plan.fingerprint()''')
edit('itd_research/campaign_runner.py', '''        if execution.case_id != case.case_id:
            raise ValueError("case evaluator returned a mismatched case_id.")
        if execution.work_units_used > case.work_units:
            raise ValueError("case evaluator exceeded its declared work budget.")''', '        _assert_case_execution(case, execution)')
edit('itd_research/campaign_runner.py', '        plan_fingerprint=plan.fingerprint(),', '        plan_fingerprint=plan_fingerprint,')
