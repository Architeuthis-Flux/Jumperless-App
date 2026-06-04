# Jumperless-App packaging

The only application source is [`JumperlessWokwiBridge.py`](../JumperlessWokwiBridge.py).
Everything below turns that one script into the things people install.

There are four outputs:

| Output | What it is | Built by |
|--------|------------|----------|
| PyPI `jumperless` | `pip install jumperless` / `uv tool install jumperless` | `tools/publish_pypi.sh` (manual) |
| Windows `.exe` | single-file console executable | CI `build` job / `tools/build_local.py` |
| macOS `.dmg` | signed + notarized universal2 `.app` installer | CI `build-macos` job / `tools/build-macos-installer.sh` |
| Linux `.AppImage` | single-file executable (+ `.tar.gz` fallback) | CI `build` job / `tools/build_local.py` |
| Backup launcher | tiny per-OS app that installs/updates `jumperless` via `uv` | CI `build-launcher` job / `tools/build_launcher.py` |

CI publishes all native artifacts to a **Jumperless-App** GitHub release and
mirrors the single-file installers (`.dmg` / `.exe` / `.AppImage`) onto the
**JumperlessV5** "latest" release (next to `firmware.uf2`).

---

## Version

`VERSION` at the repo root is the single source of truth. setuptools reads it
for the PyPI metadata; PyInstaller bundles it next to the binary; the installed
package also reports it via `importlib.metadata`.

CI also derives the GitHub release tag from it: the `version` job reads `VERSION`
and every build publishes to a release tagged **`v<VERSION>`** (e.g. `v1.1.1.19`)
on the Jumperless-App repo. A real tag push (`refs/tags/v*`) uses the pushed tag
instead. Bump `VERSION` to cut a new release; pushes that keep the same `VERSION`
update that version's release in place.

---

## PyPI (manual)

```bash
./tools/publish_pypi.sh           # sync bridge.py, build, twine check (no upload)
./tools/publish_pypi.sh --test    # upload to TestPyPI
./tools/publish_pypi.sh --prod    # upload to PyPI (asks for confirmation)
```

Auth: twine reads `~/.pypirc` or `TWINE_USERNAME`/`TWINE_PASSWORD`
(username `__token__`, password = a `pypi-…` API token). The installable
module is `jumperless_pkg`; `Scripts/prepare_jumperless_pkg.py` copies
`JumperlessWokwiBridge.py` into `jumperless_pkg/bridge.py` at build time, and the
`jumperless` console script runs `jumperless_pkg.cli:main → bridge.main()`.

---

## Local native builds (for testing)

One command builds the current platform plus the launcher into a git-ignored
`local-builds/` folder (never the CI `builds/` dir):

```bash
python tools/build_local.py                 # current OS app + uv launcher
python tools/build_local.py --no-launcher   # just the app
python tools/build_local.py --launcher-only # just the launcher
```

Results:

```
local-builds/
  macos/    Jumperless.app + Jumperless-Installer.dmg   (unsigned)
  windows/  Jumperless.exe
  linux/    Jumperless (+ Jumperless-x86_64.AppImage if appimagetool is installed)
  launcher/ macOS|linux|windows launcher bundles
```

macOS local builds reuse `tools/build-macos-installer.sh`; first run needs the
universal venv (`./Scripts/setup_universal_python.sh`), then later runs are fast.

---

## How CI builds each platform

`.github/workflows/build-and-package.yml`:

- **build** (matrix): Linux x64 → PyInstaller onefile inside a `python:3.11-bullseye`
  container (low glibc) → AppImage + `tar.gz`; Windows x64 → PyInstaller onefile
  `.exe` with embedded version info → `zip`.
- **build-macos**: imports the Developer ID cert into a temp keychain **once**,
  builds the universal2 `.app`, signs it (hardened runtime), notarizes + staples
  it, builds the DMG (signed via `create-dmg --codesign`), notarizes + staples the
  DMG, then deletes the keychain in a final `always()` step. The keychain stays
  alive across **both** the app and DMG signing — this is the fix for the old
  "item could not be found in the keychain" DMG failure.
- **build-launcher** (matrix): builds the uv launcher bundles (macOS host →
  `.app` + Linux bundle; Windows host → `.exe`).
- **publish-to-jumperlessv5**: mirrors only the single-file installers — the macOS
  `.dmg`, the Windows `.exe`, and the Linux `.AppImage` — onto the JumperlessV5
  latest release with `--clobber` (no zip/tar.gz bundles, no launcher zips;
  tag/title/notes/`firmware.uf2` untouched). The Jumperless-App release itself
  still gets every artifact (zips, tar.gz, launchers included).

Code signing and notarization are conditional: when the macOS secrets are absent
(e.g. a fork), the macOS job builds an **unsigned** DMG and stays green.

---

## The uv backup launcher

`launcher/uv_bootstrap.py` runs on every launch and:

1. ensures `uv` is installed (official installer, else `pip install uv`),
2. `uv tool install jumperless` if it isn't installed yet,
3. otherwise asks the app itself — `jumperless --check-update` prints
   `current=… latest=… outdated=true|false` — and only runs
   `uv tool upgrade jumperless` when it is out of date,
4. launches the CLI.

`tools/build_launcher.py` wraps that bootstrap in a clickable, icon-carrying
bundle per OS (macOS `.app`, Linux `.desktop`, Windows `.exe` via
`launcher/JumperlessLauncher.spec`).

---

## Required GitHub secrets

| Secret | Used for | Absent → |
|--------|----------|----------|
| `MACOS_CERTIFICATE` (base64 .p12) | macOS code signing | unsigned DMG, job still passes |
| `MACOS_CERTIFICATE_PASSWORD` | unlock the .p12 | — |
| `APPLE_ID` | notarization | signing only, no notarization |
| `APPLE_ID_PASSWORD` (app-specific) | notarization | — |
| `APPLE_TEAM_ID` (10 chars) | notarization | — |
| `JUMPERLESSV5_TOKEN` (PAT, Contents:write on JumperlessV5) | mirror artifacts | mirror step skipped |
| `GITHUB_TOKEN` (automatic) | Jumperless-App releases | — |

Set `DISABLE_MACOS_NOTARIZATION: "true"` (workflow env) to sign without notarizing.
