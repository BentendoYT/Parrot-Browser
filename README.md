 <p align="center">
  <img src="./patches/pref-pane/ParrotLogo.png" width="60%" alt="Parrot Browser">
</p>

<h3 align="center">Finally, a privacy-focused browser that does the job.</h3>

<p align="center">
  <a href="https://parrot.bentendo.dev/download"><img src="https://img.shields.io/badge/Download-ffffff.svg?style=for-the-badge&labelColor=ffffff" alt="Download" border="0"></a>
  <a href="https://github.com/BentendoYT/Parrot-Browser/releases"><img src="https://img.shields.io/badge/Releases-2b2a33.svg?style=for-the-badge&logo=github&logoColor=white" alt="Releases" border="0"></a>
  <a href="https://bentendo.dev"><img src="https://img.shields.io/badge/Website-2b2a33.svg?style=for-the-badge&logo=htmx&logoColor=white" alt="Website" border="0"></a>
</p>

## About

Parrot is a privacy-focused browser based on LibreWolf and Firefox. It combines strong privacy defaults with a clean interface and a few practical improvements.

The goal is simple: make private browsing feel like the normal browsing experience.

## Features

- **Privacy-focused defaults:** Telemetry, sponsored suggestions and unnecessary background services are disabled.
- **Fingerprinting protection:** Privacy protections are enabled by default.
- **HTTPS-only mode:** Prefer secure connections whenever possible.
- **Monochrome design:** Purple and blue accents are replaced with neutral white and gray tones in both the Nova and classic interfaces.
- **Polished interface:** Small UI improvements and fixes throughout the browser.

## Download

Available builds can be found on the [Releases page](https://github.com/BentendoYT/Parrot-Browser/releases).

| Platform | Architecture | Package |
| --- | --- | --- |
| Windows | x64 | Installer, MSI and ZIP |
| Windows | ARM64 | Installer and ZIP |
| Linux | x64 | TAR.XZ |
| Linux | ARM64 | TAR.XZ |

For installation instructions, see the [FAQ](https://github.com/BentendoYT/Parrot-Browser/wiki/FAQ).

## Installation

### Windows

Run the installer and follow the setup instructions. The standard installer supports system-wide installation and requires administrator privileges.

For silent installation:

```powershell
Parrot-Setup.exe /S
```

For MSI packages:

```powershell
msiexec /i Parrot.msi /qn
```

### Linux

Extract the downloaded archive and follow the included instructions.

## Updates

Parrot receives updates through new releases.

Windows users can also use [Parrot WinUpdater](https://github.com/BentendoYT/Parrot-winupdater) to check for and install updates.

## Building

Windows builds are produced automatically through GitHub Actions.

The repository also contains the patches and scripts used to customize the browser:

| Path | Description |
| --- | --- |
| `assets/patches.txt` | Browser patch list |
| `scripts/librewolf-patches.py` | Applies browser patches |
| `scripts/parrot-nova-colors.py` | Customizes Nova colors |
| `scripts/parrot-ui-polish.py` | Applies UI improvements |
| `scripts/parrot-settings-fixes.py` | Applies settings fixes |
| `settings/parrot.cfg` | Parrot configuration |
| `settings/distribution/policies.json` | Browser policies |

For local Linux builds, refer to the [FAQ](https://github.com/BentendoYT/Parrot-Browser/wiki/FAQ).

## Contributing

Contributions, bug reports and suggestions are welcome.

- [Report a bug](https://github.com/BentendoYT/Parrot-Browser/issues)
- [Request a feature](https://github.com/BentendoYT/Parrot-Browser/issues)
- [View the FAQ](https://github.com/BentendoYT/Parrot-Browser/wiki/FAQ)

## Credits

Parrot builds on the work of:

- [LibreWolf](https://librewolf.net/)
- [Mozilla Firefox](https://www.mozilla.org/firefox/)

## License

Parrot is distributed under the [Mozilla Public License 2.0](./LICENSE).

Copyright © 2026 Bentendo.
