#!/usr/bin/env python3
"""Writes the WiX source (for wixl / msitools) of the Parrot Browser MSI.

Usage: gen-msi-wxs.py <package dir containing parrot.exe> <version, e.g. 157.0.1-1> <icon.ico> <out.wxs>

Per-machine install to "Program Files\\Parrot Browser", Start menu shortcut, default-browser
registration (same keys as the NSIS installer) and major upgrades. The UpgradeCode must never change.
"""
import os
import re
import sys
from xml.sax.saxutils import quoteattr

UPGRADE_CODE = "7A3D4E5B-9C1F-4B6A-8E2D-5F0C3B7A91E4"  # never change: it identifies the product family
APP = "Parrot Browser"
EXE = "parrot.exe"
CLIENT = r"Software\Clients\StartMenuInternet\Parrot Browser"
PROGID = "ParrotHTM"


def msi_version(version: str) -> str:
    """157.0.1-1 -> 157.0.1.1 (MSI: a.b.c.d, first field <= 255)."""
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-(\d+))?$", version)
    if not m:
        raise SystemExit(f"error: cannot turn '{version}' into an MSI version")
    major, minor, patch, rel = (int(x) if x else 0 for x in m.groups())
    if major > 255 or minor > 255 or patch > 65535 or rel > 65535:
        raise SystemExit(f"error: version '{version}' is out of range for an MSI")
    return f"{major}.{minor}.{patch}.{rel}"


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    pkg, version, icon, out = sys.argv[1:]
    if not os.path.isfile(os.path.join(pkg, EXE)):
        raise SystemExit(f"error: {EXE} not found in {pkg}")

    lines = []
    counter = {"n": 0}
    components = []

    def nid(prefix):
        counter["n"] += 1
        return f"{prefix}{counter['n']}"

    def walk(path, indent):
        pad = "  " * indent
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.isdir(full):
                did = nid("d")
                lines.append(f"{pad}<Directory Id={quoteattr(did)} Name={quoteattr(name)}>")
                walk(full, indent + 1)
                lines.append(f"{pad}</Directory>")
            else:
                cid, fid = nid("c"), nid("f")
                components.append(cid)
                lines.append(f'{pad}<Component Id="{cid}" Guid="*">')
                lines.append(f'{pad}  <File Id="{fid}" Name={quoteattr(name)} Source={quoteattr(full)} KeyPath="yes"/>')
                lines.append(f"{pad}</Component>")

    walk(pkg, 4)
    files_xml = "\n".join(lines)
    comp_refs = "\n".join(f'      <ComponentRef Id="{c}"/>' for c in components)

    wxs = f'''<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="{APP}" Language="1033" Version="{msi_version(version)}"
           Manufacturer="Parrot" UpgradeCode="{UPGRADE_CODE}">
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine"
             Description="{APP} {version}"/>
    <MajorUpgrade AllowSameVersionUpgrades="yes"
                  DowngradeErrorMessage="A newer version of {APP} is already installed."/>
    <Media Id="1" Cabinet="parrot.cab" EmbedCab="yes"/>
    <Icon Id="parrot.ico" SourceFile={quoteattr(icon)}/>
    <Property Id="ARPPRODUCTICON" Value="parrot.ico"/>
    <Property Id="ARPNOMODIFY" Value="1"/>

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLDIR" Name="{APP}">
{files_xml}
        </Directory>
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="StartMenuDir" Name="{APP}"/>
      </Directory>
    </Directory>

    <DirectoryRef Id="StartMenuDir">
      <Component Id="StartMenuShortcut" Guid="*">
        <Shortcut Id="StartShortcut" Name="{APP}" Target="[INSTALLDIR]{EXE}" WorkingDirectory="INSTALLDIR"/>
        <RemoveFolder Id="RemoveStartMenuDir" On="uninstall"/>
        <RegistryValue Root="HKLM" Key="Software\\Parrot\\Installer" Name="StartMenuShortcut" Type="integer" Value="1" KeyPath="yes"/>
      </Component>
    </DirectoryRef>

    <DirectoryRef Id="INSTALLDIR">
      <Component Id="DefaultBrowserRegistration" Guid="*">
        <RegistryValue Root="HKLM" Key="{CLIENT}" Type="string" Value="{APP}" KeyPath="yes"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities" Name="ApplicationName" Type="string" Value="{APP}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities" Name="ApplicationDescription" Type="string" Value="{APP}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities" Name="ApplicationIcon" Type="string" Value="[INSTALLDIR]{EXE},0"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities\\FileAssociations" Name=".htm" Type="string" Value="{PROGID}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities\\FileAssociations" Name=".html" Type="string" Value="{PROGID}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities\\FileAssociations" Name=".pdf" Type="string" Value="{PROGID}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities\\Startmenu" Name="StartMenuInternet" Type="string" Value="{APP}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities\\URLAssociations" Name="http" Type="string" Value="{PROGID}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\Capabilities\\URLAssociations" Name="https" Type="string" Value="{PROGID}"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\DefaultIcon" Type="string" Value="[INSTALLDIR]{EXE},0"/>
        <RegistryValue Root="HKLM" Key="{CLIENT}\\shell\\open\\command" Type="string" Value="[INSTALLDIR]{EXE}"/>
        <RegistryValue Root="HKLM" Key="Software\\RegisteredApplications" Name="{APP}" Type="string" Value="{CLIENT}\\Capabilities"/>
        <RegistryValue Root="HKLM" Key="Software\\Classes\\{PROGID}" Type="string" Value="{APP} Handler"/>
        <RegistryValue Root="HKLM" Key="Software\\Classes\\{PROGID}\\Application" Name="ApplicationName" Type="string" Value="{APP}"/>
        <RegistryValue Root="HKLM" Key="Software\\Classes\\{PROGID}\\Application" Name="AppUserModelId" Type="string" Value="Parrot"/>
        <RegistryValue Root="HKLM" Key="Software\\Classes\\{PROGID}\\DefaultIcon" Type="string" Value="[INSTALLDIR]{EXE},0"/>
        <RegistryValue Root="HKLM" Key="Software\\Classes\\{PROGID}\\shell\\open\\command" Type="string" Value="&quot;[INSTALLDIR]{EXE}&quot; -osint -url &quot;%1&quot;"/>
      </Component>
    </DirectoryRef>

    <Feature Id="Complete" Title="{APP}" Level="1">
{comp_refs}
      <ComponentRef Id="StartMenuShortcut"/>
      <ComponentRef Id="DefaultBrowserRegistration"/>
    </Feature>
  </Product>
</Wix>
'''
    with open(out, "w", encoding="utf-8") as f:
        f.write(wxs)
    print(f"{len(components)} files, MSI version {msi_version(version)} -> {out}")


if __name__ == "__main__":
    main()
