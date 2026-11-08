#!/usr/bin/env bash
# Builds the Parrot Browser MSI (x64) with wixl (msitools) from a packaged build.
#
# Usage: scripts/build-msi.sh <parrot-<version>-windows-x86_64-package.zip> <output dir>
# Needs: wixl (apt-get install wixl), unzip, python3.
# ARM64 is not supported yet: wixl cannot mark a package as ARM64.
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }

[ "$#" -eq 2 ] || die "usage: $0 <package.zip> <output dir>"
PKG_ZIP="$1"
OUT_DIR="$2"
[ -f "$PKG_ZIP" ] || die "package not found: $PKG_ZIP"
command -v wixl >/dev/null || die "wixl not found (apt-get install wixl)"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICON="$REPO_DIR/themes/browser/branding/librewolf/firefox.ico"
[ -f "$ICON" ] || die "missing $ICON"

name="$(basename "$PKG_ZIP")"
if [[ "$name" =~ ^parrot-(.+)-windows-x86_64-package\.zip$ ]]; then
  VERSION="${BASH_REMATCH[1]}"
elif [[ "$name" =~ ^parrot-(.+)-windows-arm64-package\.zip$ ]]; then
  die "ARM64 MSI is not supported yet (wixl has no arm64 platform)"
else
  die "unexpected package name '$name'"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/pkg" "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

unzip -q "$PKG_ZIP" -d "$WORK/pkg"
mapfile -t exes < <(find "$WORK/pkg" -maxdepth 2 -type f -name parrot.exe)
[ "${#exes[@]}" -eq 1 ] || die "expected exactly one parrot.exe in the package, found ${#exes[@]}"
PKG_DIR="$(dirname "${exes[0]}")"
if find "$WORK/pkg" -type f -iname librewolf.exe | grep -q .; then
  die "package still contains librewolf.exe"
fi

python3 "$REPO_DIR/scripts/gen-msi-wxs.py" "$PKG_DIR" "$VERSION" "$ICON" "$WORK/parrot.wxs"
OUT_FILE="$OUT_DIR/parrot-$VERSION-windows-x86_64.msi"
wixl -a x64 -o "$OUT_FILE" "$WORK/parrot.wxs"
[ -s "$OUT_FILE" ] || die "wixl did not produce $OUT_FILE"
ls -l "$OUT_FILE"
