#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python -m py_compile \
    itd_v10.py \
    compare_scenarios.py \
    validate_release_v10.py

python itd_v10.py
python validate_release_v10.py
