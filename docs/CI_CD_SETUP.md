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
- PyPI: the `publish-pypi` job uploads on every `v*` tag when the
  `PYPI_API_TOKEN` secret is set (pypi.org API token scoped to `jumperless`);
  without it the job only builds and warns, and `./tools/publish_pypi.sh --prod`
  is the manual fallback. The tag must equal `v<VERSION>`.
