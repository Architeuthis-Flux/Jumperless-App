# CI/CD

The CI/CD system is documented together with the rest of the packaging chain in
[PACKAGING.md](PACKAGING.md).

Quick reference:

- Workflow: [`.github/workflows/build-and-package.yml`](../.github/workflows/build-and-package.yml)
- Jobs: `build` (Linux AppImage + Windows exe), `build-macos` (signed + notarized
  DMG), `build-launcher` (uv backup launcher), `publish-to-jumperlessv5` (mirror
  artifacts onto the JumperlessV5 latest release).
- Triggers: push to `main`, `v*` tags, PRs to `main`, and manual dispatch.
- Required secrets: see the "Required GitHub secrets" table in
  [PACKAGING.md](PACKAGING.md).
- PyPI is **not** published by CI — use `./tools/publish_pypi.sh` (manual).
