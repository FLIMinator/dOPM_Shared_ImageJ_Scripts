#!/usr/bin/env bash
set -euo pipefail

# Reproducible dOPM Fiji environment builder - Linux x86_64
# No CPython/Python installation is required.
# Requires: bash, curl, unzip
#
# This creates the same Java/plugin version set as the validated Windows build.
# GPU MIP generation additionally requires a working OpenCL runtime/driver.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/Fiji_2.9.0_dOPM_linux"
FIJI="${ROOT}/Fiji.app"
WORK="${TMPDIR:-/tmp}/dopm_fiji_2_9_0_build_$$"

FIJI_URL="https://downloads.imagej.net/fiji/releases/2.9.0/fiji-2.9.0-linux64.zip"
MVR_URL="https://sites.imagej.net/BigStitcher/plugins/multiview_reconstruction-0.11.5.jar-20211201080417"
SPIM_URL="https://sites.imagej.net/BigStitcher/plugins/SPIM_Registration-0.0.1.jar-20180411172036"
CLIJ_URL="https://sites.imagej.net/clij/plugins/clij_-1.9.0.1.jar-20210613085830"
CLIJ2_URL="https://sites.imagej.net/clij2/plugins/clij2_-2.5.1.4.jar-20211023172143"
CLEARCL_URL="https://repo1.maven.org/maven2/net/haesleinhuepf/clij-clearcl/2.5.0.1/clij-clearcl-2.5.0.1.jar"
CLIJCORE_URL="https://repo1.maven.org/maven2/net/haesleinhuepf/clij-core/1.8.1.1/clij-core-1.8.1.1.jar"
COREMEM_URL="https://repo1.maven.org/maven2/net/haesleinhuepf/clij-coremem/2.3.0.4/clij-coremem-2.3.0.4.jar"
JOCL_URL="https://repo1.maven.org/maven2/org/jocl/jocl/2.0.2/jocl-2.0.2.jar"

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "[ERROR] Required command not found: $1" >&2
        exit 1
    }
}

fetch() {
    local url="$1"
    local dest="$2"
    echo "  -> $(basename "$dest")"
    curl -L --fail --retry 3 --output "$dest" "$url"
    [[ -s "$dest" ]] || { echo "[ERROR] Missing/empty file: $dest" >&2; exit 1; }
}

need_cmd curl
need_cmd unzip

cat <<EOF
============================================================================
dOPM Fiji 2.9.0 reproducible environment builder - Linux x86_64
============================================================================
No CPython/Python installation is required.
Output: $ROOT
EOF

if [[ -e "$ROOT" ]]; then
    read -r -p "Existing build found. Delete it and rebuild from scratch? [y/N] " ans
    case "$ans" in
        y|Y|yes|YES) rm -rf "$ROOT" ;;
        *) echo "Cancelled."; exit 0 ;;
    esac
fi

mkdir -p "$WORK" "$ROOT"

echo "[1/10] Downloading official Fiji 2.9.0 linux64..."
fetch "$FIJI_URL" "$WORK/fiji.zip"

echo "[2/10] Extracting Fiji..."
unzip -q "$WORK/fiji.zip" -d "$ROOT"
[[ -d "$FIJI" ]] || { echo "[ERROR] Fiji.app was not extracted." >&2; exit 1; }

# Historical Fiji launchers vary slightly. Keep any launcher executable.
find "$FIJI" -maxdepth 1 -type f \( -name 'ImageJ-linux64' -o -name 'ImageJ-linux*' -o -name 'ImageJ' \) -exec chmod +x {} + 2>/dev/null || true

echo "[3/10] Installing Multiview Reconstruction 0.11.5..."
rm -f "$FIJI"/plugins/multiview_reconstruction*.jar
fetch "$MVR_URL" "$FIJI/plugins/multiview_reconstruction-0.11.5.jar"

echo "[4/10] Installing SPIM Registration 0.0.1..."
rm -f "$FIJI"/plugins/SPIM_Registration*.jar
fetch "$SPIM_URL" "$FIJI/plugins/SPIM_Registration-0.0.1.jar"

echo "[5/10] Installing CLIJ 1.9.0.1..."
rm -f "$FIJI"/plugins/clij_*.jar
fetch "$CLIJ_URL" "$FIJI/plugins/clij_-1.9.0.1.jar"

echo "[6/10] Installing CLIJ2 2.5.1.4..."
rm -f "$FIJI"/plugins/clij2_*.jar
fetch "$CLIJ2_URL" "$FIJI/plugins/clij2_-2.5.1.4.jar"

echo "[7/10] Installing CLIJ Java dependencies..."
rm -f "$FIJI"/jars/clij-clearcl*.jar "$FIJI"/jars/clij-core-*.jar "$FIJI"/jars/clij-coremem*.jar
fetch "$CLEARCL_URL" "$FIJI/jars/clij-clearcl-2.5.0.1.jar"
fetch "$CLIJCORE_URL" "$FIJI/jars/clij-core-1.8.1.1.jar"
fetch "$COREMEM_URL" "$FIJI/jars/clij-coremem-2.3.0.4.jar"

echo "[8/10] Installing JOCL 2.0.2..."
rm -f "$FIJI"/jars/jocl-*.jar
fetch "$JOCL_URL" "$FIJI/jars/jocl-2.0.2.jar"

echo "[9/10] Verifying files..."
required=(
  "$FIJI/plugins/multiview_reconstruction-0.11.5.jar"
  "$FIJI/plugins/SPIM_Registration-0.0.1.jar"
  "$FIJI/plugins/clij_-1.9.0.1.jar"
  "$FIJI/plugins/clij2_-2.5.1.4.jar"
  "$FIJI/jars/clij-clearcl-2.5.0.1.jar"
  "$FIJI/jars/clij-core-1.8.1.1.jar"
  "$FIJI/jars/clij-coremem-2.3.0.4.jar"
  "$FIJI/jars/jocl-2.0.2.jar"
)
for f in "${required[@]}"; do
    [[ -s "$f" ]] || { echo "[ERROR] Missing/empty: $f" >&2; exit 1; }
    echo "  [PASS] $(basename "$f")"
done

echo "[10/10] Writing environment record..."
cat > "$ROOT/DOPM_FIJI_ENVIRONMENT.txt" <<EOF
dOPM Fiji reproducible environment
Base: official Fiji 2.9.0 linux64

Added/replaced components:
multiview_reconstruction-0.11.5.jar
SPIM_Registration-0.0.1.jar
clij_-1.9.0.1.jar
clij2_-2.5.1.4.jar
clij-clearcl-2.5.0.1.jar
clij-core-1.8.1.1.jar
clij-coremem-2.3.0.4.jar
jocl-2.0.2.jar

dOPM Jython scripts are NOT installed by this script.
Copy the repository production scripts to:
Fiji.app/plugins/Scripts/dOPM
EOF

cat <<EOF
============================================================================
BUILD COMPLETE
============================================================================
Fiji: $FIJI

Next:
  1. Copy the dOPM repository production scripts into:
     $FIJI/plugins/Scripts/dOPM
  2. Launch Fiji.
  3. Run validation/Test_dOPM_EndToEnd_v3_faithful.py on the test dataset.
  4. Do not run the Fiji updater before validation.

Linux note: CLIJ2 MIPs require a working system OpenCL implementation/driver.
EOF
