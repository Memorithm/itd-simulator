# Licence decision required

## Current legal status

No licence preference is present in the repository or owner instructions. No
`LICENSE` file or package licence metadata has therefore been added. Public
visibility alone does not grant permission to copy, modify, redistribute, or
commercially reuse the code. This is the one remediation decision that requires
owner approval.

This comparison is practical project guidance, not legal advice. The owner
should obtain qualified legal advice for patent, employment, and jurisdictional
questions.

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

Before accepting code from anyone other than Tarek Zekriti, choose both a
licence and a contribution-rights policy. Do not copy a licence template into
the repository until that choice is explicit. Once selected, add the exact
`LICENSE`, package metadata, README/CONTRIBUTING updates, and a dated changelog
entry in one reviewed change.
