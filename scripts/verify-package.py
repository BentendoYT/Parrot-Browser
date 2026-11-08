#!/usr/bin/env python3
"""Checks a packaged Parrot build before it is uploaded or released.

Usage: scripts/verify-package.py <package> <windows|linux> <x86_64|arm64>

windows: <package> is a .zip. It must contain exactly one parrot.exe (top-level folder), no
         librewolf.exe, and parrot.exe must be built for the requested CPU (read from the PE header).
linux:   <package> is a .tar.xz. It must contain exactly one parrot and one parrot-bin (top-level
         folder), no librewolf binary, and parrot-bin must be an ELF for the requested CPU.
"""
import posixpath
import struct
import sys
import tarfile
import zipfile

PE_MACHINE = {"x86_64": 0x8664, "arm64": 0xAA64}
ELF_MACHINE = {"x86_64": 0x3E, "arm64": 0xB7}


def base(name):
    return posixpath.basename(name.rstrip("/")).lower()


def depth_ok(name):
    return name.rstrip("/").count("/") <= 1


def check_windows(path, arch):
    problems = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        exes = [n for n in names if base(n) == "parrot.exe"]
        old = [n for n in names if base(n) == "librewolf.exe"]
        if len(exes) != 1 or not depth_ok(exes[0]):
            problems.append(f"expected exactly one top-level parrot.exe, found {exes}")
        if old:
            problems.append(f"package still contains librewolf.exe: {old}")
        if len(exes) == 1:
            data = z.read(exes[0])
            offset = struct.unpack_from("<I", data, 0x3C)[0] if data[:2] == b"MZ" and len(data) > 0x40 else -1
            if offset < 0 or data[offset:offset + 4] != b"PE\0\0":
                problems.append("parrot.exe is not a valid Windows executable")
                return problems
            machine = struct.unpack_from("<H", data, offset + 4)[0]
            if machine != PE_MACHINE[arch]:
                problems.append(f"parrot.exe has machine type {machine:#x}, expected {PE_MACHINE[arch]:#x} ({arch})")
            else:
                print(f"parrot.exe machine type {machine:#x} = {arch}")
    return problems


def check_linux(path, arch):
    problems = []
    with tarfile.open(path, "r:xz") as t:
        members = [m for m in t.getmembers() if not m.isdir()]
        names = [m.name for m in members]
        binaries = [n for n in names if base(n) == "parrot"]
        bins = [n for n in names if base(n) == "parrot-bin"]
        old = [n for n in names if base(n) in ("librewolf", "librewolf-bin")]
        if len(binaries) != 1 or not depth_ok(binaries[0]):
            problems.append(f"expected exactly one top-level parrot, found {binaries}")
        if len(bins) != 1 or not depth_ok(bins[0]):
            problems.append(f"expected exactly one top-level parrot-bin, found {bins}")
        if old:
            problems.append(f"package still contains librewolf binaries: {old}")
        if len(bins) == 1:
            head = t.extractfile(bins[0]).read(20)
            if head[:4] != b"\x7fELF":
                problems.append("parrot-bin is not an ELF file")
            else:
                machine = struct.unpack_from("<H", head, 18)[0]
                if machine != ELF_MACHINE[arch]:
                    problems.append(f"parrot-bin has ELF machine {machine:#x}, expected {ELF_MACHINE[arch]:#x} ({arch})")
                else:
                    print(f"parrot-bin ELF machine {machine:#x} = {arch}")
    return problems


def main():
    if len(sys.argv) != 4 or sys.argv[2] not in ("windows", "linux") or sys.argv[3] not in PE_MACHINE:
        raise SystemExit(__doc__)
    path, target, arch = sys.argv[1:]
    problems = check_windows(path, arch) if target == "windows" else check_linux(path, arch)
    if problems:
        for p in problems:
            print(f"::error::{p}")
        raise SystemExit(1)
    print(f"{path}: OK ({target}, {arch})")


if __name__ == "__main__":
    main()
