#!/usr/bin/env bash
# Builds the Parrot Browser Windows installer (NSIS) from a packaged build.
#
# Usage: scripts/build-installer.sh <parrot-<version>-windows-<x86_64|arm64>-package.zip> <output dir>
# Optional environment:
#   VC_REDIST_FILE  local vc_redist exe to embed (default: download the official x64 or arm64 one from Microsoft)
#   NO_VC_REDIST=1  do not embed the Visual C++ redistributable
#   UPDATER_DIR     folder with Parrot-WinUpdater.exe + ScheduledTask-*.ps1 (adds the optional component)
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }

[ "$#" -eq 2 ] || die "usage: $0 <package.zip> <output dir>"
PKG_ZIP="$1"
OUT_DIR="$2"
[ -f "$PKG_ZIP" ] || die "package not found: $PKG_ZIP"
command -v makensis >/dev/null || die "makensis not found (apt-get install nsis)"
command -v unzip >/dev/null || die "unzip not found"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NSI="$REPO_DIR/assets/installer/parrot-setup.nsi"
ICON="$REPO_DIR/themes/browser/branding/librewolf/firefox.ico"
[ -f "$NSI" ] || die "missing $NSI"

name="$(basename "$PKG_ZIP")"
if [[ "$name" =~ ^parrot-(.+)-windows-(x86_64|arm64)-package\.zip$ ]]; then
  VERSION="${BASH_REMATCH[1]}"
  ARCH="${BASH_REMATCH[2]}"
else
  die "unexpected package name '$name' (expected parrot-<version>-windows-<x86_64|arm64>-package.zip)"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/pkg" "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

echo "-> Extracting $name"
unzip -q "$PKG_ZIP" -d "$WORK/pkg"

# The zip has one top-level folder that contains parrot.exe
mapfile -t exes < <(find "$WORK/pkg" -maxdepth 2 -type f -name parrot.exe)
[ "${#exes[@]}" -eq 1 ] || die "expected exactly one parrot.exe in the package, found ${#exes[@]}"
PKG_DIR="$(dirname "${exes[0]}")"
if find "$WORK/pkg" -type f -iname librewolf.exe | grep -q .; then
  die "package still contains librewolf.exe"
fi
EST_SIZE_KB="$(du -sk "$PKG_DIR" | cut -f1)"

# a.b.c.d for the file properties (157.0.1-1 -> 157.0.1.1)
VERSION_NUM=""
if [[ "$VERSION" =~ ^([0-9]+)(\.([0-9]+))?(\.([0-9]+))?(-([0-9]+))?$ ]]; then
  VERSION_NUM="${BASH_REMATCH[1]}.${BASH_REMATCH[3]:-0}.${BASH_REMATCH[5]:-0}.${BASH_REMATCH[7]:-0}"
fi

args=(-V2 "-DPKG_VERSION=$VERSION" "-DPKG_ARCH=$ARCH" "-DPKG_DIR=$PKG_DIR" "-DEST_SIZE_KB=$EST_SIZE_KB")
OUT_FILE="$OUT_DIR/parrot-$VERSION-windows-$ARCH-setup.exe"
args+=("-DOUT_FILE=$OUT_FILE")
[ -n "$VERSION_NUM" ] && args+=("-DVERSION_NUM=$VERSION_NUM")
[ -f "$ICON" ] && args+=("-DICON_FILE=$ICON")

# Installer artwork (see scripts/make-installer-art.py); INSTALLER_DARK=0 gives the light scheme
ART="$REPO_DIR/assets/installer"
[ -f "$ART/banner.bmp" ] && args+=("-DBANNER_FILE=$ART/banner.bmp")
if [ "${INSTALLER_DARK:-1}" = "1" ]; then
  args+=("-DDARK=1")
  [ -f "$ART/header-dark.bmp" ] && args+=("-DHEADER_FILE=$ART/header-dark.bmp")
else
  [ -f "$ART/header-light.bmp" ] && args+=("-DHEADER_FILE=$ART/header-light.bmp")
fi

if [ "${NO_VC_REDIST:-0}" != "1" ]; then
  VC="$WORK/vc_redist.exe"
  if [ -n "${VC_REDIST_FILE:-}" ]; then
    cp "$VC_REDIST_FILE" "$VC"
  else
    if [ "$ARCH" = "arm64" ]; then VC_ARCH=arm64; else VC_ARCH=x64; fi
    echo "-> Downloading Visual C++ Redistributable ($VC_ARCH)"
    curl -fL --retry 3 -o "$VC" "https://aka.ms/vs/17/release/vc_redist.$VC_ARCH.exe"
  fi
  [ -s "$VC" ] || die "vc_redist.exe is empty"
  args+=("-DVC_REDIST=$VC")
fi

if [ -n "${UPDATER_DIR:-}" ]; then
  for f in Parrot-WinUpdater.exe ScheduledTask-Create.ps1 ScheduledTask-Remove.ps1; do
    [ -f "$UPDATER_DIR/$f" ] || die "UPDATER_DIR is missing $f"
  done
  args+=("-DUPDATER_DIR=$UPDATER_DIR")
fi

echo "-> Building installer ($VERSION, $ARCH)"
makensis "${args[@]}" "$NSI"
[ -s "$OUT_FILE" ] || die "makensis did not produce $OUT_FILE"

# Checksums in the "<sha256>  <file>" format Parrot-WinUpdater expects (sha256sums.txt)
(cd "$OUT_DIR" && sha256sum "$(basename "$OUT_FILE")" > sha256sums.txt)
echo "-> Done"
ls -l "$OUT_DIR"
cat "$OUT_DIR/sha256sums.txt"
