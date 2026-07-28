#!/usr/bin/env bash
# Mission 8 reproduction driver. Steps 1-3 run OFFLINE (no network) and are what CI runs.
# Steps 4-7 need outbound HTTPS and reproduce the real external results; they never run in
# normal CI. The offline fixture is SYNTHETIC and is never external evidence -- see the
# prominent warning in README.md about its verdicts.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="$PWD"
PY="${PYTHON:-python}"

echo "[1/7] verify environment (compare to repro/mission8/environment.txt)"
"$PY" --version; "$PY" -c "import numpy; print('NumPy', numpy.__version__)"

echo "[2/7] offline fixture validation (bounded, deterministic; ~10-30s)"
OUT="$(mktemp -d)"
"$PY" -m itd_research.mission8 validate --config configs/mission8/ci.toml --output "$OUT"

echo "[3/7] canonical reproducibility digests (must match repro/mission8/expected_checksums.txt)"
"$PY" - <<'PYEOF'
from itd_research.mission8.campaign import (
    canonical_result_digest, run_fixture_campaign, run_full_fixture_validation,
)
print("mission8_fixture_campaign.canonical ",
      canonical_result_digest(run_fixture_campaign().as_dict()))
print("mission8_full_validation.canonical  ",
      canonical_result_digest(run_full_fixture_validation()))
PYEOF

echo "[4/7] (network) re-fetch the six real JHTDB sequences pinned in source_manifest.jhtdb.json"
cat <<'NETEOF'
      DIR=/tmp/itd-m8-jhtdb
      # isotropic1024coarse: iso_topo(40f) @100,200,300 | run1(24f) @500,200,300
      #                      run2(24f)    @100,600,300  | run3(24f) @100,200,700
      # mhd1024:             mhd_topo(24f)@100,200,300  | mhd_run2(16f) @500,200,300
      # each: --size 24, dt 0.1, frame_NN.npz named by index
      for i in $(seq 0 39); do t=$(awk "BEGIN{printf \"%.2f\", $i*0.1}"); \
        python tools/datasets/fetch_jhtdb_cutout.py --dataset isotropic1024coarse \
          --origin 100 200 300 --size 24 --time "$t" \
          --output "$DIR/iso_topo/frame_$(printf %02d $i).npz"; done
      # ...repeat per sequence with the origins/frame-counts above.
NETEOF

echo "[5/7] verify fetched frame checksums against repro/mission8/source_manifest.jhtdb.json"
echo "[6/7] run the primary campaign on the LOCKED dev/holdout split (evaluations_allowed = 1)"
cat <<'RUNEOF'
      python -m itd_research.mission8 run \
        --dev iso_run1=$DIR/iso_topo_run1 --dev iso_run2=$DIR/iso_topo_run2 \
        --holdout iso_topo=$DIR/iso_topo --holdout iso_run3=$DIR/iso_topo_run3 \
        --output /tmp/m8ext
RUNEOF
echo "      expected (see EXTERNAL_STRUCTURAL_INCREMENTAL_VALUE_REPORT.md):"
echo "        established 0.519 | ITD-only 0.246 | augmented 0.344"
echo "        added value -0.168 CI [-0.175, -0.153] -> h61/h62 NOT supported"
echo "[7/7] regenerate reports from the result JSON (docs/research/MISSION8_*, *_REPORT.md)"
echo "done"
