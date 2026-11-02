#!/usr/bin/env python3
"""Print the ProductVersion string of parrot.exe.

Usage: scripts/exe-version.py <parrot-*-package.zip | some.exe>

Parrot-WinUpdater compares this value (ProductVersion of the installed parrot.exe) with the
tag of the latest GitHub release, so the release tag must be exactly this string.
Needs the "pefile" package (pip install pefile).
"""
import posixpath
import sys
import zipfile

import pefile


def product_version(data: bytes) -> str:
    try:
        pe = pefile.PE(data=data, fast_load=True)
    except pefile.PEFormatError as exc:
        raise SystemExit(f"error: not a valid Windows executable ({exc})")
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
    )
    for info in getattr(pe, "FileInfo", None) or []:
        for entry in info if isinstance(info, list) else [info]:
            if getattr(entry, "Key", b"") != b"StringFileInfo":
                continue
            for table in entry.StringTable:
                value = table.entries.get(b"ProductVersion")
                if value:
                    return value.decode("utf-8", "replace").strip()
    raise SystemExit("error: no ProductVersion found in the executable")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if posixpath.basename(n).lower() == "parrot.exe"]
            if len(names) != 1:
                raise SystemExit(f"error: expected exactly one parrot.exe in {path}, found {len(names)}")
            data = z.read(names[0])
    else:
        with open(path, "rb") as f:
            data = f.read()
    print(product_version(data))


if __name__ == "__main__":
    main()
