# External CFD / PIV validation report

Status: **research report** for the post-V29 external-validation layer. This is
**not** a certified scientific revision and does **not** modify `ITD V29.18`
(equations, expected outputs, oracles, reference summaries, and the Rust fixture
are unchanged). It records what has and has not been established when the ITD
structural signature is compared with established vortex-identification
diagnostics on analytical, synthetic, and genuinely external data.

Reproduce every number with:

```
python -m itd_research.external_validation --quick --output <dir>
# full external fields (after downloading, see DATASET_PROVENANCE.md):
python -m itd_research.external_validation --output <dir> \
    --piv-npz <biofilm_full.npz> --jhtdb-npz <jhtdb_iso_32.npz>
```

## 1. What each data class can and cannot support

| Class | Cases | Supports |
|---|---|---|
| **analytical** | rigid rotation, pure strain, simple shear, strain+shear, Lamb-Oseen, vortex pair | code verification; exact shear-vs-rotation behaviour |
| **synthetic** | tanh mixing layer, Stuart roll-up, Taylor-Green, Karman street | qualitative diagnostic comparison; **not** empirical validation |
| **external (2D)** | biofilm PIV mean boundary layer (Zenodo 1175014, CC-BY-4.0) | genuine empirical evidence on measured velocities |
| **external (3D)** | JHTDB isotropic-turbulence DNS cutout (`isotropic1024coarse`) | genuine independent 3D CFD evidence for the 3D candidate |

Synthetic fields stand in for CFD solver output this environment cannot produce
(no OpenFOAM/VTK). **A synthetic field is never presented as external empirical
validation.**

## 2. Headline finding: shear versus rotation

ITD's rotational intensity, like enstrophy, is built on vorticity, which is large
in **both** shear and rotation. Q, swirling strength, Okubo-Weiss, and lambda_2
isolate **rotation**. The suite quantifies the gap with the Jaccard overlap
between the top-20 % vorticity-magnitude region and the rotation region `Q > 0`.

| Case | rms vorticity | rotation frac (Q>0) | Jaccard(high|ω|, Q>0) | rot. components | ITD intensity | ITD localization |
|---|--:|--:|--:|--:|--:|--:|
| rigid_rotation | 2.60 | 1.000 | 0.36* | 1 | 6.76 | 0.00 |
| pure_strain | ~0 | 0.000 | 0.00 | 0 | ~0 | 0.00 |
| **simple_shear** | **1.50** | **0.000** | **0.000** | **0** | **2.25** | 0.00 |
| strain_plus_shear | 1.50 | 0.000 | 0.000 | 0 | 2.25 | 0.00 |
| lamb_oseen | 0.58 | 0.058 | 0.286 | 1 | 0.35 | 18.97 |
| vortex_pair | 1.02 | 0.083 | 0.415 | 2 | 1.09 | 14.43 |
| mixing_layer_base (tanh) | 0.72 | 0.000 | 0.000 | 0 | 0.53 | 4.06 |
| kh_rollup (Stuart) | 2.70 | 0.008 | 0.039 | 1 | 7.54 | 166.5 |
| taylor_green | 1.00 | 0.493 | 0.406 | 7 | 1.00 | 1.25 |
| karman_street | 0.70 | 0.075 | 0.374 | 13 | 0.49 | 15.97 |

\* rigid rotation has spatially uniform `|omega|`, so the "top 20 %" quantile
region degenerates to the whole domain; the 0.36 is that degeneracy, not a
disagreement (the rotation fraction is exactly 1).

The decisive rows are **simple_shear** and **mixing_layer_base**: large vorticity
and non-zero ITD intensity, but **zero** rotation fraction and **zero**
high-vorticity/rotation overlap. Vorticity-based measures (enstrophy, ITD
intensity) count shear as if it were rotation; Q/swirling/Okubo-Weiss do not.
Conversely, `connected_components` of the rotation region recovers the correct
vortex count with no ITD input: 1 (Lamb-Oseen), 2 (vortex pair), 13 (Karman
street).

## 3. External experimental PIV (Zenodo 1175014, CC-BY-4.0)

Time-averaged PIV of a turbulent boundary layer over a biofilm-fouled plate
(Murphy et al. 2018). Full field, largest fully-valid interior rectangle
(`224 x 406`, `dx = dy = 0.1765 mm`):

| Quantity | Value |
|---|--:|
| rms vorticity | 27.0 s⁻¹ |
| mean Q | −1.73 (strain-dominated on average) |
| rotation fraction (Q>0) | 0.349 |
| Okubo-Weiss vortex fraction (W<0) | 0.371 |
| Jaccard(high |ω|, Q>0) | 0.245 |
| Dice(high |ω|, Q>0) | 0.393 |
| corr(|ω|, swirling strength) Pearson / Spearman | 0.537 / 0.439 |
| ITD intensity / enstrophy | 715 / 357 |
| ITD sign-mixing | 0.0012 |
| ITD heterogeneity / localization / roughness | 0.89 / 2.49 / 108.6 |

Interpretation, kept to what the data supports:

* The mean field is **shear-dominated**: only ~35 % of nodes are rotation
  -dominated, and the two independent rotation criteria (Q>0 and Okubo-Weiss
  W<0) agree closely (0.349 vs 0.371).
* The high-vorticity region overlaps the rotation region only weakly
  (Jaccard 0.245), and `|omega|` correlates with swirling strength at only 0.54
  (Pearson) — versus ~0.95 for the coherent-vortex cases. On real shear-driven
  data, ITD's vorticity basis and rotation-based identification see **different**
  structure.
* **ITD sign-mixing is ~0**: the mean boundary-layer vorticity is single-signed
  (mean shear `dU/dy` of one sign), which the sign-mixing component correctly
  reports. This is a genuine, physically expected property recovered from
  measured data.

This is a real-data realisation of the analytical "simple shear" case: large
vorticity, little coherent rotation.

## 4. Transport versus deformation (H3)

A pattern advected by a known uniform velocity (spectral pure translation, 64²
periodic) gives a large Eulerian change but a small transport-compensated
residual:

| Quantity | Value |
|---|--:|
| rms Eulerian change | 0.538 |
| rms advective term | 0.538 |
| rms residual (compensated) | 0.0176 |
| residual / Eulerian | 0.033 |

Transport compensation removes ~97 % of the translation-induced Eulerian signal,
demonstrating that raw Eulerian temporal change over-reports mere transport.

## 5. Resolution stability (H4)

Same external field and region, decimated by 1×/2×/3×:

| metric | 1× (224×406) | 2× | 3× |
|---|--:|--:|--:|
| rotation fraction | 0.349 | 0.348 | 0.340 |
| Jaccard(high |ω|, Q>0) | 0.245 | 0.244 | 0.243 |
| ITD sign-mixing | 0.0012 | 0.0007 | 0.0006 |
| ITD heterogeneity | 0.894 | 0.890 | 0.891 |
| corr(|ω|, swirl) | 0.537 | 0.540 | 0.539 |

The comparison metrics are stable under a 3× resolution change.

## 5b. Equal enstrophy, different ITD vector (H1)

Two velocity fields are built with **identical enstrophy** — a distributed
Taylor-Green checkerboard and a single concentrated Lamb-Oseen vortex, the latter
rescaled so its enstrophy matches exactly. The magnitude-based ITD components are
amplitude-invariant, so the rescaling removes the only scalar that could separate
them without manufacturing the result:

| Quantity | Distributed (A) | Concentrated (B) |
|---|--:|--:|
| enstrophy | 0.49840 | 0.49840 (matched to 1e-6) |
| ITD heterogeneity | 0.73 | 5.79 |
| ITD localization | 1.25 | 68.6 |

Enstrophy cannot tell the two fields apart; the ITD localization separates them by
**~55×** and heterogeneity by **8×**. This is the central ITD claim, shown
quantitatively: the structural vector carries organisation information a scalar
does not.

## 5c. Transition detection across a vortex merger (H2 mechanism, synthetic)

A kinematic sequence of two co-rotating vortices at decreasing separation. The
count of **significant** rotation regions (connected `Q > 0` components of at
least 8 cells, filtering strain-fragmentation) is an ITD-independent transition
marker:

| separation | 3.0 | 2.5 | 2.0 | 1.5 | 1.2 | 1.0 | 0.6 | 0.3 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| significant rotation regions | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| ITD localization | 29.1 | 29.1 | 29.1 | 28.5 | 27.6 | 28.3 | 40.9 | 53.9 |
| ITD intensity | 0.235 | 0.235 | 0.235 | 0.237 | 0.248 | 0.267 | 0.350 | 0.432 |

The region count drops 2 → 1 at the merger, and ITD localization/intensity rise as
the merged core concentrates. This demonstrates the mechanism H2 relies on — an
ITD-independent marker flags a topological transition while the ITD channels
co-vary — but it is a **synthetic** demonstration, not a test on externally
annotated data.

## 6. Hypothesis assessment (H1–H6)

Each status states the evidence class explicitly.

| # | Hypothesis | Status | Evidence |
|---|---|---|---|
| **H1** | At similar global enstrophy, the ITD structural vector distinguishes differently organised fields | **supported** | Controlled equal-enstrophy pair (§5b): identical enstrophy (0.49840), ITD localization separated ~55× and heterogeneity 8×. Demonstrated on constructed fields, not yet on an external equal-enstrophy pair |
| **H2** | ITD temporal channels detect annotated transitions better than intensity alone | **partially supported (synthetic)** | Vortex-merger sequence (§5c): an ITD-independent marker (significant rotation regions) transitions 2 → 1 while ITD localization/intensity co-vary. Mechanism shown on synthetic data; **not** tested on externally annotated transitions |
| **H3** | Transport compensation reduces false temporal response from pure translation | **supported** | Synthetic pure translation: residual/Eulerian = 0.033 (~97 % removed). Genuine time-resolved DNS (§7b): 48 % of the raw Eulerian change of \|omega\| removed, the rest genuine deformation (stretching). The transport-vs-deformation split works on real external data |
| **H4** | ITD components are stable under reasonable mesh/PIV-processing changes | **supported** | External field metrics stable under 1×/2×/3× decimation (§5); consistent with the Mission-1 convergence/sensitivity studies |
| **H5** | ITD is complementary to Q/swirling/lambda_2, not a duplicate | **supported** | On real data Jaccard(high|ω|,Q>0)=0.245 and corr(|ω|,swirl)=0.54; on pure shear the overlap is exactly 0. ITD's vorticity basis captures different structure than rotation-based methods |
| **H6** | A meaningful 3D extension needs orientation/stretching/helicity channels | **supported** | Confirmed on a genuine JHTDB DNS cutout (§9): orientation dispersion 0.88, normalized helicity ≈ 0, and a **positive** mean vortex-stretching rate (+2.9) — all genuinely 3D, physically correct, and without 2D analogue. Analytical oracles (ABC helicity = 1, Burgers stretching = a) confirm the code. Remaining: multiple regions/datasets and volumetric experimental data |

## 7. Decision gates (unchanged conclusion)

Per `EXTERNAL_CFD_PIV_3D_VALIDATION_SPEC.md` §8, **no new certified revision is
warranted**. Met: at least one real public PIV dataset processed with complete
provenance (Zenodo 1175014); genuine independent 3D DNS processed (JHTDB, §7b);
complementary diagnostic information demonstrated; metrics stable under
preprocessing; explicit dimensional conventions; limitations documented.
**Not met**: reproducible independent CFD *solver run* executed here (environment
lacks a solver — the JHTDB DNS is queried, not solved locally; the 2D CFD cases
are synthetic stand-ins); an externally *annotated* transition processed (H2); a
time-resolved external series for H2/H3 on real data; the 3D candidate validated
across *multiple* DNS regions/datasets and on *volumetric experimental* data
(a single 32³ cutout is evidence, not a campaign). Independent review is
recommended before any certification is considered. The 3D candidate remains
experimental.

## 7b. External 3D DNS turbulence (JHTDB)

A `32^3` block of native grid nodes from the JHU Turbulence Database forced
isotropic turbulence DNS (`isotropic1024coarse`, `GetVelocity` point query,
public testing token; `tools/datasets/fetch_jhtdb_cutout.py`) — genuine
independent 3D CFD, component rms 0.5524, raw data not committed per JHTDB terms.

| Quantity | Value | Expectation |
|---|--:|---|
| ITD orientation dispersion | 0.880 | ≈ 1 (near-isotropic orientation) |
| ITD normalized helicity | −0.044 | ≈ 0 (no preferred handedness) |
| ITD vortex-stretching rate | +2.88 | > 0 (net stretching, the cascade) |
| Q>0 fraction / lambda_2<0 fraction | 0.281 / 0.266 | comparable |
| Jaccard(Q>0, lambda_2<0) | 0.872 | high (both detect rotation) |
| corr(\|omega\|, swirling strength) | 0.890 | high, < 1 |

The genuinely 3D ITD channels — which have no 2D analogue — are all physically
correct on real turbulence, and the two established rotation criteria (Q and
lambda_2) agree at Jaccard 0.87.

An **ensemble of six `24^3` cutouts** at different origins confirms robustness:
the vortex-stretching rate is **positive in all six boxes** (+2.33 ± 0.91), the
normalized helicity scatters symmetrically about zero (+0.03 ± 0.13), and
Jaccard(Q, lambda_2) is 0.892 ± 0.009. A **time-resolved** query of one box
(`dt = 0.002`) shows transport compensation removing 48 % of the raw Eulerian
change of \|omega\|, the remainder being genuine deformation (stretching) — the
honest real-data counterpart to the 97 %-removed synthetic pure translation.
Full details in `ITD_3D_CANDIDATE_REPORT.md` §4. This is one dataset and a small
ensemble: early evidence, not a full statistical campaign.

## 8. Limitations

* No CFD solver in this environment: cases A–C/E of the spec are represented by
  **synthetic** analogues (Karman street, Stuart roll-up), not solver output.
* The external PIV field is a **time-averaged mean**; the 4000 instantaneous
  fields (22 GB) were not downloaded, so instantaneous coherent structures and
  the temporal hypotheses (H2) are not addressed on external data.
* Correlations are statistical associations on single snapshots, not causal or
  dynamical claims.
