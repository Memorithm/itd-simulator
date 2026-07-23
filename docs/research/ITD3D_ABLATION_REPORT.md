# ITD-3D candidate ablation report (H12)

Status: **research report**. Not a certified revision; does not modify `ITD V29.18`.
No candidate is certified. Reproduce with `python -m itd_research.validation_lab
run --config configs/validation_lab/ci.toml --output <dir>`.

## Question (H12, falsifiable)

Does a reduced or modified ITD-3D candidate improve the accuracy–robustness–cost
trade-off over the current full candidate, on a defined task?

## Candidates

| id | channels | rationale |
|---|---|---|
| A (full) | all 8 | the current experimental set |
| B (compact) | intensity, localization, orientation_dispersion, stretching_rate, normalized_helicity | magnitude + structure + genuinely-3D |
| C (orientation/stretching) | orientation_dispersion, normalized_helicity, stretching_rate, localization | drops magnitude channels |
| baseline-intensity | intensity | single-channel control |
| baseline-enstrophy+localization | intensity, localization | two-channel control |

## Task and protocol

Classify the flow family (laminar/coherent, transitional, turbulent) of a
sub-cube from a candidate's channel vector. **Leave-one-flow-out**: all sub-cubes
of a held-out flow form the test set; the classifier (nearest standardized
centroid) is fit on the other flows only, standardized with training statistics
only — so sub-cubes of one flow never appear in both train and test. Metric:
balanced accuracy (chance = 0.33 for three classes).

## Results (CI resolution `24^3`, 9 flows, 243 sub-cubes)

| candidate | channels | balanced accuracy |
|---|--:|--:|
| **baseline-intensity** | 1 | **0.593** |
| baseline-enstrophy+localization | 2 | 0.582 |
| ITD3D-Research-B | 5 | 0.537 |
| ITD3D-Research-C | 4 | 0.527 |
| ITD3D-Research-A (full) | 8 | 0.525 |

## H12 classification: **not supported (on this task/scope)**

On this controlled family-classification task the **simple baselines beat every
ITD-3D candidate**, and adding channels *hurts* (the full 8-channel candidate is
worst). Two honest reasons, both stated rather than hidden:

1. The flow families here differ strongly in vorticity intensity, so a single
   intensity channel already separates them well; the extra channels add
   variance to a nearest-centroid distance with only nine flows.
2. Leave-one-flow-out with nine flows is a small, high-variance evaluation; the
   redundant channels (report on H11) inflate the feature dimension without
   adding separating power for *this* target.

This is a genuine negative result for "more channels ⇒ better" on this task. It
does **not** show the channels are useless: on a task where intensity is
controlled (the equal-enstrophy H1 study, where the structural vector separates
fields a scalar cannot, and the H11 finding that helicity/stretching are
non-redundant), the structural channels carry information the baselines lack. The
correct conclusion is **task-dependent**: candidate ranking must be established
per target, and no single candidate dominates.

## Locked selection protocol (for a future, larger study)

Before any final selection: predefine the target tasks and datasets; hold out
flows/sources; rank candidates by a multi-objective front (accuracy, robustness,
cross-resolution stability, cost, interpretability); require an external held-out
confirmation; never select on the test set. Under the present evidence, **no
candidate is selected or certified** — the full candidate is retained as the
documented experimental reference, with the compact candidate B noted as the
leading reduction hypothesis pending a task where the structural channels are
needed.

## Limitations

Single task, single classifier family, nine local flows, modest resolution,
under-resolved turbulence. A different task (event prediction, equal-intensity
discrimination) can reverse the ranking; that is the point of reporting per-task.
