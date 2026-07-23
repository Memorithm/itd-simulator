# Mission 7 reproduction bundle

This bundle lets an independent user reproduce the Mission 7 external-evidence results.
It never commits third-party raw data; it commits **provenance and checksums** plus the
exact commands to regenerate the data legally from its authoritative source.

## Contents

| file | purpose |
|---|---|
| `environment.txt` | Python / NumPy / Rust versions used |
| `commands.sh` | end-to-end driver (offline steps 1–2, 7; network steps 3–6) |
| `expected_checksums.txt` | SHA-256 of the **offline** fixture campaign JSON (determinism proof) |
| `source_manifest.jhtdb.json` | provenance + per-frame SHA-256 of the real JHTDB short sequence |
| `small_public_subset_manifest.json` | how to regenerate the tiny reproducible subset + its checksums |

## Offline reproduction (no network — this is what CI runs)

```bash
PYTHONHASHSEED=0 PYTHONPATH=$PWD python -m itd_research.mission7 validate --output /tmp/m7
```

The campaign JSON (with the `environment` block removed) must hash to the value in
`expected_checksums.txt`. This proves the pipeline is deterministic and reproducible. The
fixture is **synthetic** and is never external evidence.

## Network reproduction (needs outbound HTTPS; never runs in CI)

Run `bash repro/mission7/commands.sh` and follow the printed network steps, or:

```bash
DIR=/tmp/itd-m7-jhtdb; mkdir -p "$DIR"
for i in $(seq 0 15); do
  t=$(awk "BEGIN{printf \"%.2f\", $i*0.1}")
  python tools/datasets/fetch_jhtdb_cutout.py --dataset isotropic1024coarse \
    --origin 128 256 384 --size 16 --time "$t" --output "$DIR/frame_$(printf %02d $i).npz"
done
python -m itd_research.mission7 run --data "$DIR" --source-id jhtdb_isotropic1024coarse --output /tmp/m7ext
```

Then compare the fetched frame SHA-256 values to `source_manifest.jhtdb.json`. The biofilm
PIV control regenerates with
`python tools/datasets/fetch_dataset.py --id biofilm_piv_boundary_layer --output "$DIR"`
(SHA-256 pinned in the dataset registry and the subset manifest).

## Data provenance and licences

- **JHTDB isotropic1024coarse** — Johns Hopkins Turbulence Database. Respect the JHTDB
  terms of use and citation policy (https://turbulence.pha.jhu.edu). The public testing
  token permits small queries. Raw cutouts are **not** committed.
- **biofilm PIV** — Zenodo record 1175014, CC-BY-4.0 (USNA / U. Virginia). Time-averaged
  boundary-layer PIV; a shear **control**, never coherent-vortex validation.

## Independent replication (H60)

Reproducing the offline fixture campaign in a *different* environment (second machine, OS,
Python build, or by another person) and matching `expected_checksums.txt` completes H60.
A re-run inside the original environment demonstrates reproducibility (H59) but is **not**
independent replication — see `docs/research/INDEPENDENT_REPLICATION_REPORT.md`.
