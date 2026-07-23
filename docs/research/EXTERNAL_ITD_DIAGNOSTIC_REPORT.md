# External ITD diagnostic report (H51/H54) — descriptive analysis on JHTDB DNS

Status: **research report**. Preregistration SHA-256
`35c46735d694a9af78d471c38b52931e598f0cacdc4f0ce781bfbe5f7552d0f9`. Evidence class:
**external-DNS**. Evidence level **E7** (diagnostics executed). Descriptive only — no
predictive claim is made here.

## H51 — ITD is physically interpretable on external data (**supported**)

On the JHTDB isotropic-turbulence sequence, every ITD-3D channel is finite and behaves
sensibly. `intensity` tracks the enstrophy trajectory almost exactly (rank correlation
**+0.994**), as expected since both are vorticity-magnitude measures. The channels respond
to the enstrophy burst (frames rise and fall together), confirming the diagnostics compute
meaningfully on genuine external turbulence, not just on local Taylor-Green flows.

## H54 — complementarity (**partially supported**)

Rank correlation of each ITD channel with the primary established scalar (enstrophy),
16-frame sequence:

| ITD channel | ρ vs enstrophy | distinct (|ρ|<0.3)? |
|---|---|---|
| intensity | +0.994 | no (redundant) |
| roughness | +0.626 | no |
| localization | −0.062 | **yes** |
| heterogeneity | −0.059 | **yes** |

`localization` and `heterogeneity` are statistically **distinct** from enstrophy — they
carry information the primary established scalar does not. **But**: (a) which channels are
distinct is not stable across sequences (the 48-frame run flagged `roughness` and
`orientation_dispersion` instead), and (b) statistical distinctness did **not** convert to
predictive value — the distinct channels do not track the enstrophy event, and adding ITD
gave zero incremental AUC (`EXTERNAL_INCREMENTAL_VALUE_M7_REPORT.md`).

**Verdict: H54 partially supported** — some ITD channels are demonstrably not captured by
enstrophy on external data, but the complementarity is sequence-dependent and has no
demonstrated downstream value. Reported descriptively, not as evidence of ITD value.
