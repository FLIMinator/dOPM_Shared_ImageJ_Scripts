#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Reproducible dOPM Fiji environment builder - Linux x86_64
#
# No CPython/Python installation is required.
# Requires: curl, unzip
#
# This mirrors the validated Windows builder, including the pinned
# BigDataViewer compatibility stack required for BigStitcher Data Explorer/BDV.
#
# It DOES NOT install the dOPM Jython scripts.
# Copy the repository production .py files separately to:
#   Fiji.app/plugins/Scripts/dOPM
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SCRIPT_DIR}/Fiji_2.9.0_dOPM"
FIJI="${ROOT}/Fiji.app"
WORK="${TMPDIR:-/tmp}/dopm_fiji_2_9_0_build"

FIJI_URL="https://downloads.imagej.net/fiji/releases/2.9.0/fiji-2.9.0-linux64.zip"

BIGSTITCHER_URL="https://sites.imagej.net/BigStitcher/plugins/Big_Stitcher-0.8.3.jar-20211130143242"
MVR_URL="https://sites.imagej.net/BigStitcher/plugins/multiview_reconstruction-0.11.5.jar-20211201080417"
SPIM_URL="https://sites.imagej.net/BigStitcher/plugins/SPIM_Registration-0.0.1.jar-20180411172036"

BDV_CORE_URL="https://sites.imagej.net/Fiji.backup/jars/bigdataviewer-core-10.2.0.jar-20210222164216"
BDV_VISTOOLS_URL="https://sites.imagej.net/Fiji/jars/bigdataviewer-vistools-1.0.0-beta-28.jar-20210222164216"
BDV_FIJI_URL="https://sites.imagej.net/Java-8/plugins/bigdataviewer_fiji-6.2.1.jar-20210222164216"

CLIJ_URL="https://sites.imagej.net/clij/plugins/clij_-1.9.0.1.jar-20210613085830"
CLIJ2_URL="https://sites.imagej.net/clij2/plugins/clij2_-2.5.1.4.jar-20211023172143"

CLEARCL_URL="https://repo1.maven.org/maven2/net/haesleinhuepf/clij-clearcl/2.5.0.1/clij-clearcl-2.5.0.1.jar"
CLIJCORE_URL="https://repo1.maven.org/maven2/net/haesleinhuepf/clij-core/1.8.1.1/clij-core-1.8.1.1.jar"
COREMEM_URL="https://repo1.maven.org/maven2/net/haesleinhuepf/clij-coremem/2.3.0.4/clij-coremem-2.3.0.4.jar"
JOCL_URL="https://repo1.maven.org/maven2/org/jocl/jocl/2.0.2/jocl-2.0.2.jar"

echo
echo "============================================================================"
echo "dOPM Fiji 2.9.0 reproducible environment builder - Linux x86_64"
echo "============================================================================"
echo
echo "No CPython/Python installation is required."
echo "Output:"
echo "  ${ROOT}"
echo

for cmd in curl unzip; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "[ERROR] Required command not found: $cmd"
        echo "Install it with your Linux distribution package manager and rerun."
        exit 1
    fi
done

ARCH="$(uname -m)"
if [[ "$ARCH" != "x86_64" && "$ARCH" != "amd64" ]]; then
    echo "[ERROR] This installer currently supports Linux x86_64 only."
    echo "Detected architecture: $ARCH"
    exit 1
fi

if [[ -d "$ROOT" ]]; then
    read -r -p "Existing build found. Delete it and rebuild from scratch? [y/N] " reply
    case "$reply" in
        y|Y|yes|YES) rm -rf "$ROOT" ;;
        *) echo "Cancelled."; exit 0 ;;
    esac
fi

rm -rf "$WORK"
mkdir -p "$WORK" "$ROOT"

fail() {
    echo
    echo "============================================================================"
    echo "BUILD FAILED"
    echo "============================================================================"
    echo "Review the first error above."
    rm -rf "$WORK"
    exit 1
}

download() {
    local url="$1"
    local output="$2"
    echo "  -> $(basename "$output")"
    curl -L --fail --retry 3 --output "$output" "$url" || fail
}

check_file() {
    local path="$1"
    local label="$2"
    if [[ -s "$path" ]]; then
        echo "  [PASS] $label"
    else
        echo "  [FAIL] $label - missing or zero-byte file"
        BAD=1
    fi
}

echo
echo "[1/13] Downloading official Fiji 2.9.0 linux64..."
download "$FIJI_URL" "$WORK/fiji.zip"

echo
echo "[2/13] Extracting Fiji..."
unzip -q "$WORK/fiji.zip" -d "$ROOT" || fail

if [[ ! -f "$FIJI/ImageJ-linux64" ]]; then
    echo "[ERROR] Fiji extracted but ImageJ-linux64 was not found."
    fail
fi
chmod +x "$FIJI/ImageJ-linux64" || true

echo
echo "[3/13] Removing incompatible bundled BigStitcher / MVR / BDV components..."
rm -f "$FIJI"/plugins/Big_Stitcher*.jar
rm -f "$FIJI"/plugins/BigStitcher*.jar
rm -f "$FIJI"/plugins/multiview_reconstruction*.jar
rm -f "$FIJI"/plugins/SPIM_Registration*.jar
rm -f "$FIJI"/jars/bigdataviewer-core*.jar
rm -f "$FIJI"/jars/bigdataviewer-vistools*.jar
rm -f "$FIJI"/plugins/bigdataviewer_fiji*.jar
rm -f "$FIJI"/jars/bigdataviewer_fiji*.jar

echo
echo "[4/13] Installing BigStitcher 0.8.3..."
download "$BIGSTITCHER_URL" "$FIJI/plugins/Big_Stitcher-0.8.3.jar"

echo
echo "[5/13] Installing Multiview Reconstruction 0.11.5..."
download "$MVR_URL" "$FIJI/plugins/multiview_reconstruction-0.11.5.jar"

echo
echo "[6/13] Installing SPIM Registration compatibility JAR 0.0.1..."
download "$SPIM_URL" "$FIJI/plugins/SPIM_Registration-0.0.1.jar"

echo
echo "[7/13] Installing BigDataViewer compatibility stack..."
download "$BDV_CORE_URL" "$FIJI/jars/bigdataviewer-core-10.2.0.jar"
download "$BDV_VISTOOLS_URL" "$FIJI/jars/bigdataviewer-vistools-1.0.0-beta-28.jar"
download "$BDV_FIJI_URL" "$FIJI/plugins/bigdataviewer_fiji-6.2.1.jar"

echo
echo "[8/13] Installing CLIJ 1.9.0.1..."
rm -f "$FIJI"/plugins/clij_*.jar
download "$CLIJ_URL" "$FIJI/plugins/clij_-1.9.0.1.jar"

echo
echo "[9/13] Installing CLIJ2 2.5.1.4..."
rm -f "$FIJI"/plugins/clij2_*.jar
download "$CLIJ2_URL" "$FIJI/plugins/clij2_-2.5.1.4.jar"

echo
echo "[10/13] Installing CLIJ Java dependencies..."
rm -f "$FIJI"/jars/clij-clearcl*.jar
rm -f "$FIJI"/jars/clij-core-*.jar
rm -f "$FIJI"/jars/clij-coremem*.jar
download "$CLEARCL_URL" "$FIJI/jars/clij-clearcl-2.5.0.1.jar"
download "$CLIJCORE_URL" "$FIJI/jars/clij-core-1.8.1.1.jar"
download "$COREMEM_URL" "$FIJI/jars/clij-coremem-2.3.0.4.jar"

echo
echo "[11/13] Installing JOCL 2.0.2 for CLIJ/OpenCL..."
rm -f "$FIJI"/jars/jocl-*.jar
download "$JOCL_URL" "$FIJI/jars/jocl-2.0.2.jar"

echo
echo "[12/13] Verifying installed components..."
BAD=0
check_file "$FIJI/plugins/Big_Stitcher-0.8.3.jar" "BigStitcher 0.8.3"
check_file "$FIJI/plugins/multiview_reconstruction-0.11.5.jar" "Multiview Reconstruction 0.11.5"
check_file "$FIJI/plugins/SPIM_Registration-0.0.1.jar" "SPIM Registration 0.0.1"
check_file "$FIJI/jars/bigdataviewer-core-10.2.0.jar" "BigDataViewer core 10.2.0"
check_file "$FIJI/jars/bigdataviewer-vistools-1.0.0-beta-28.jar" "BigDataViewer vistools beta-28"
check_file "$FIJI/plugins/bigdataviewer_fiji-6.2.1.jar" "BigDataViewer Fiji 6.2.1"
check_file "$FIJI/plugins/clij_-1.9.0.1.jar" "CLIJ 1.9.0.1"
check_file "$FIJI/plugins/clij2_-2.5.1.4.jar" "CLIJ2 2.5.1.4"
check_file "$FIJI/jars/clij-clearcl-2.5.0.1.jar" "CLIJ ClearCL 2.5.0.1"
check_file "$FIJI/jars/clij-core-1.8.1.1.jar" "CLIJ core 1.8.1.1"
check_file "$FIJI/jars/clij-coremem-2.3.0.4.jar" "CLIJ coremem 2.3.0.4"
check_file "$FIJI/jars/jocl-2.0.2.jar" "JOCL 2.0.2"

if [[ -e "$FIJI/jars/bigdataviewer-core-10.4.3.jar" ]]; then
    echo "  [FAIL] Incompatible BigDataViewer core 10.4.3 is still present"
    BAD=1
fi

shopt -s nullglob
bdv_cores=( "$FIJI"/jars/bigdataviewer-core*.jar )
shopt -u nullglob

echo "  BigDataViewer core JAR count: ${#bdv_cores[@]}"
for jar in "${bdv_cores[@]}"; do
    echo "    $(basename "$jar")"
done

if [[ ${#bdv_cores[@]} -ne 1 ]]; then
    echo "  [FAIL] Expected exactly one bigdataviewer-core JAR."
    BAD=1
fi

if [[ "$BAD" -ne 0 ]]; then
    fail
fi

echo
echo "[13/13] Writing environment record..."
cat > "$ROOT/DOPM_FIJI_ENVIRONMENT.txt" <<'TXT'
dOPM Fiji reproducible environment
=================================

Base:
  Fiji 2.9.0 linux64

BigStitcher / Multiview:
  Big_Stitcher-0.8.3.jar
  multiview_reconstruction-0.11.5.jar
  SPIM_Registration-0.0.1.jar

BigDataViewer:
  bigdataviewer-core-10.2.0.jar
  bigdataviewer-vistools-1.0.0-beta-28.jar
  bigdataviewer_fiji-6.2.1.jar

CLIJ:
  clij_-1.9.0.1.jar
  clij2_-2.5.1.4.jar
  clij-clearcl-2.5.0.1.jar
  clij-core-1.8.1.1.jar
  clij-coremem-2.3.0.4.jar
  jocl-2.0.2.jar

dOPM Jython scripts are NOT installed by this shell script.

Copy repository production scripts to:
  Fiji.app/plugins/Scripts/dOPM

IMPORTANT:
Do not update Fiji or BigStitcher before validating this environment.
TXT

rm -rf "$WORK"

echo
echo "============================================================================"
echo "BUILD COMPLETE"
echo "============================================================================"
echo
echo "Fiji:"
echo "  $FIJI"
echo
echo "Next:"
echo "  1. Copy the dOPM repository production scripts into:"
echo "       $FIJI/plugins/Scripts/dOPM"
echo
echo "  2. Launch Fiji:"
echo "       $FIJI/ImageJ-linux64"
echo
echo "  3. Test BigStitcher / Data Explorer and the BDV viewer."
echo
echo "  4. Run validation/Test_dOPM_EndToEnd_v3_faithful.py on the test dataset."
echo
echo "  5. Do NOT run Help > Update before validation."
echo
echo "NOTE: CLIJ2 requires a working OpenCL runtime/driver on the Linux machine."
