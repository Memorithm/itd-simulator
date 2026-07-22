# Licence decision

## Current legal status

**Decided by the repository owner (Tarek Zekriti, 2026):** the source is
dual-licensed, matching the `Memorithm/scirust` model —

- **PolyForm Noncommercial License 1.0.0** for noncommercial and personal use
  (see [`LICENSE`](../LICENSE));
- a **separate written commercial licence**, required for any commercial use,
  obtained from the copyright holder (zekrititarek@gmail.com).

The dual-licensing terms and commercial contact are recorded in
[`LICENSING.md`](../LICENSING.md), and the package declares
`license = "PolyForm-Noncommercial-1.0.0"` with `LICENSE` and `LICENSING.md` as
license files. Public visibility alone does not grant commercial rights.

A separate inbound-contribution-rights policy has not yet been selected; until it
is, external code contributions are not accepted (see `CONTRIBUTING.md`).

The comparison below is retained as practical project guidance, not legal advice.
The owner should obtain qualified legal advice for patent, employment,
jurisdictional, and contribution questions.

| Option | SciRust integration | Academic reuse | Commercial reuse | Patent position | External contributions |
|---|---|---|---|---|---|
| Apache-2.0 | Generally permits integration and redistribution if notices and licence terms are preserved; downstream compatibility still must be checked | Permitted with attribution/notice obligations | Permitted | Includes an express contributor patent grant and patent-termination clause | Requires provenance and notice discipline; contributor patent grant applies |
| MIT OR Apache-2.0 | Recipients may choose either permissive path; useful when downstream ecosystems differ | Broadly permitted | Broadly permitted | Apache path has an express grant; MIT text has no comparable express patent clause | Contributions normally need to be available under both choices, which must be stated clearly |
| Proprietary / all rights reserved | No integration without a separate licence from the owner | Reading may be possible, but reuse/redistribution requires permission | Requires negotiated permission | Rights remain reserved; patent terms must be negotiated separately | Contributions should not be accepted without explicit assignment or contributor terms |
| Dual licensing | Can offer an open-source path plus a separate commercial/proprietary path, depending on chosen licences | Depends on the open path | Commercial terms can differ from the open path | Patent terms depend on both licences and agreements | Usually requires the owner to retain relicensing rights through assignment or a suitable contributor agreement |

## Decision considerations

If frictionless open SciRust and academic reuse is the priority, Apache-2.0
offers an explicit patent grant, while `MIT OR Apache-2.0` maximizes recipient
choice at the cost of a more complex contribution statement. If the owner needs
case-by-case control or a commercial negotiation, all-rights-reserved or a
purpose-designed dual model may fit better but blocks ordinary open-source
reuse until permission is granted.

The owner selected the last kind of model: a **noncommercial-plus-commercial dual
licence** (PolyForm Noncommercial 1.0.0 for noncommercial/personal use, with a
separate written commercial licence for commercial use). This mirrors the
`Memorithm/scirust` project and keeps commercial reuse under case-by-case owner
control while allowing free noncommercial and academic use.

A **contribution-rights policy** remains unselected. Before accepting code from
anyone other than Tarek Zekriti, choose that policy (for example a contributor
agreement compatible with the dual model). Until then, external code
contributions are not accepted (`CONTRIBUTING.md`).
