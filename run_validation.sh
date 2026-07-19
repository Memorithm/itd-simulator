#!/usr/bin/env bash
set -Eeuo pipefail

readonly ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly PYTHON_BIN="${PYTHON:-python}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

usage() {
    printf 'Usage: %s [--legacy-v10]\n' "${0##*/}" >&2
}

run_legacy=false
case "${1:-}" in
    "") ;;
    --legacy-v10) run_legacy=true ;;
    *) usage; exit 2 ;;
esac

readonly TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/itd-v29-validation.XXXXXX")"
cleanup() {
    local status=$?
    trap - EXIT INT TERM
    rm -rf -- "${TEMP_DIR}"
    exit "${status}"
}
trap cleanup EXIT INT TERM

cd -- "${ROOT_DIR}"
readonly STATUS_BEFORE="$(git status --porcelain=v1 --untracked-files=no)"

printf '%s\n' '[1/8] Compile current Python sources'
"${PYTHON_BIN}" -m compileall -q \
    itd_v29.py \
    compare_scenarios.py \
    oracle_harness.py \
    itd_simulator \
    itd_v29_core \
    tools \
    tests

printf '%s\n' '[2/8] Run the V29.18 pytest validator suite'
"${PYTHON_BIN}" -m pytest -q

printf '%s\n' '[3/8] Verify modular architecture dependencies'
"${PYTHON_BIN}" tools/test_dependency_analyser.py

printf '%s\n' '[4/8] Run independent-process deterministic smoke checks'
"${PYTHON_BIN}" tools/deterministic_smoke.py > "${TEMP_DIR}/smoke-a.json"
"${PYTHON_BIN}" tools/deterministic_smoke.py > "${TEMP_DIR}/smoke-b.json"
cmp --silent "${TEMP_DIR}/smoke-a.json" "${TEMP_DIR}/smoke-b.json"

printf '%s\n' '[5/8] Run the current V29 simulator and certify its summary'
mkdir -- "${TEMP_DIR}/main"
(
    cd -- "${TEMP_DIR}/main"
    "${PYTHON_BIN}" "${ROOT_DIR}/itd_v29.py"
) > "${TEMP_DIR}/itd_v29.log"
summary_arguments=(
    "${ROOT_DIR}/itd_v29_results/summary.csv"
    "${TEMP_DIR}/main/itd_v29_results/summary.csv"
)
if [[ "$("${PYTHON_BIN}" -c 'import numpy; print(numpy.__version__)')" == '2.5.1' ]]; then
    summary_arguments+=(--exact)
fi
"${PYTHON_BIN}" tools/check_v29_summary.py "${summary_arguments[@]}"

printf '%s\n' '[6/8] Verify the complete public manifest'
"${PYTHON_BIN}" tools/check_manifest.py

printf '%s\n' '[7/8] Generate and compare the Rust oracle reference'
"${PYTHON_BIN}" oracle_harness.py "${TEMP_DIR}/oracle_data.rs" \
    > "${TEMP_DIR}/oracle-generate.log"
"${PYTHON_BIN}" oracle_harness.py \
    --check tests/fixtures/oracle_data.rs \
    > "${TEMP_DIR}/oracle-check.log"

if [[ "${run_legacy}" == true ]]; then
    printf '%s\n' '[optional] Run the historical V10-only validator'
    mkdir -- "${TEMP_DIR}/legacy"
    (
        cd -- "${TEMP_DIR}/legacy"
        "${PYTHON_BIN}" "${ROOT_DIR}/itd_v10.py"
        "${PYTHON_BIN}" "${ROOT_DIR}/validate_release_v10.py"
    ) > "${TEMP_DIR}/legacy-v10.log"
fi

printf '%s\n' '[8/8] Verify validation did not modify tracked files'
readonly STATUS_AFTER="$(git status --porcelain=v1 --untracked-files=no)"
if [[ "${STATUS_AFTER}" != "${STATUS_BEFORE}" ]]; then
    printf '%s\n' 'Tracked repository state changed during validation.' >&2
    diff -u \
        <(printf '%s\n' "${STATUS_BEFORE}") \
        <(printf '%s\n' "${STATUS_AFTER}") >&2 || true
    exit 1
fi

printf '%s\n' 'ITD V29.18 validation: PASSED'
