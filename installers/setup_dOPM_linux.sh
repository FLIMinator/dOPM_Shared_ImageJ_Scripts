#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# dOPM repository bootstrap - Linux x86_64
#
# Recommended one-step setup entry point.
# Builds Fiji if missing, creates the dOPM Fiji script folder, and copies all
# repository-root .py files into it. Source files are copied, never moved.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALLER="${SCRIPT_DIR}/build_dOPM_Fiji_linux.sh"
FIJI_ROOT="${REPO_ROOT}/Fiji_2.9.0_dOPM"
FIJI="${FIJI_ROOT}/Fiji.app"
DOPM_DEST="${FIJI}/plugins/Scripts/dOPM"

echo
echo "============================================================================"
echo "dOPM complete setup - Linux x86_64"
echo "============================================================================"
echo
echo "Repository:"
echo "  ${REPO_ROOT}"
echo
echo "Fiji target:"
echo "  ${FIJI}"
echo

if [[ ! -x "${FIJI}/ImageJ-linux64" ]]; then
    echo "[1/3] Fiji environment not found. Building it now..."
    bash "${INSTALLER}"
else
    echo "[1/3] Existing Fiji environment found; keeping it."
fi

if [[ ! -f "${FIJI}/ImageJ-linux64" ]]; then
    echo "[ERROR] Fiji executable is missing after setup:"
    echo "  ${FIJI}/ImageJ-linux64"
    exit 1
fi
chmod +x "${FIJI}/ImageJ-linux64" || true

echo
echo "[2/3] Creating dOPM Fiji script folder..."
mkdir -p "${DOPM_DEST}"

echo
echo "[3/3] Copying repository Python/Jython scripts into Fiji..."
shopt -s nullglob
py_files=( "${REPO_ROOT}"/*.py )
shopt -u nullglob

if [[ ${#py_files[@]} -eq 0 ]]; then
    echo "[ERROR] No repository-root .py files were found to deploy."
    exit 1
fi

for src in "${py_files[@]}"; do
    cp -f "$src" "${DOPM_DEST}/"
    echo "  [COPIED] $(basename "$src")"
done

echo
echo "============================================================================"
echo "SETUP COMPLETE"
echo "============================================================================"
echo
echo "Copied ${#py_files[@]} Python/Jython files to:"
echo "  ${DOPM_DEST}"
echo
echo "Generated Fiji lives at:"
echo "  ${FIJI_ROOT}"
echo
echo "Validation script remains in:"
echo "  ${REPO_ROOT}/validation/Test_dOPM_EndToEnd_v3_faithful.py"
echo
echo "Launch Fiji with:"
echo "  ${FIJI}/ImageJ-linux64"
