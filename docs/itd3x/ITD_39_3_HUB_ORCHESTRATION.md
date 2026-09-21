# ITD-39.3 — SciRust Hub campaign orchestration

Status: **implementation slice active**

## Ownership

SciRust Hub owns component registration, capability discovery, execution orchestration, immutable artifact flow and execution provenance. ITD owns experiment protocols, budgets, holdout boundaries and scientific interpretation.

## Submission contract

`HubCampaignSubmission` binds:

- exact Memorithm/scirust-hub source identity;
- registered component identity;
- capability name;
- exact ITD campaign-plan fingerprint;
- parameter-payload SHA-256;
- maximum parallelism;
- maximum attempts;
- timeout.

Secrets and bearer tokens are intentionally absent from the contract.

## Run record

`HubRunRecord` records:

- run identity and lifecycle state;
- attempt count bounded by the submission;
- provenance SHA-256;
- immutable artifact identities and content SHA-256 values.

A successful run must retain at least one artifact.

## Security boundary

The current Hub execution model provides process supervision and authenticated transport options, not an OS sandbox. `claims_os_sandbox` is therefore hard-coded false.

## Scientific boundary

Hub success only means the declared capability completed under the retained execution provenance. `authorizes_scientific_conclusion` remains false; the resulting artifacts still require ITD protocol/result evaluation and, where required, SciRust-Verify dossier normalization.
