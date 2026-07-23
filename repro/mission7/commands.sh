#!/usr/bin/env bash
# Mission 7 reproduction driver. Steps 1-2 + 7 run OFFLINE (no network). Steps 3-6 need
# outbound HTTPS and reproduce the external evidence; they never run in normal CI.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH="$PWD"
PY="${PYTHON:-python}"

echo "[1/7] verify environment"; "$PY" --version; "$PY" -c "import numpy; print('NumPy', numpy.__version__)"
echo "[2/7] offline fixture campaign (deterministic; compare to repro/mission7/expected_checksums.txt)"
OUT="$(mktemp -d)"; "$PY" -m itd_research.mission7 validate --output "$OUT"
"$PY" - "$OUT/mission7_external.json" <<'PYEOF'
import json,hashlib,sys
d=json.load(open(sys.argv[1])); d.pop("environment",None)
print("fixture campaign sha256:", hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest())
PYEOF

echo "[3/7] (network) fetch the JHTDB short sequence -> a scratch dir (see small_public_subset_manifest.json)"
echo "      DIR=/tmp/itd-m7-jhtdb; mkdir -p \$DIR"
echo "      for i in \$(seq 0 15); do t=\$(awk \"BEGIN{printf \\\"%.2f\\\", \$i*0.1}\"); \\"
echo "        \$PY tools/datasets/fetch_jhtdb_cutout.py --dataset isotropic1024coarse --origin 128 256 384 \\"
echo "        --size 16 --time \$t --output \$DIR/frame_\$(printf %02d \$i).npz; done"
echo "[4/7] (network) fetch the biofilm PIV control"
echo "      \$PY tools/datasets/fetch_dataset.py --id biofilm_piv_boundary_layer --output \$DIR"
echo "[5/7] run the external campaign on the fetched sequence"
echo "      \$PY -m itd_research.mission7 run --data \$DIR --source-id jhtdb_isotropic1024coarse --output \$OUT"
echo "[6/7] compare frame checksums to repro/mission7/source_manifest.jhtdb.json"
echo "[7/7] regenerate reports from the result JSON (docs/research/MISSION7_*)"
echo "done"
