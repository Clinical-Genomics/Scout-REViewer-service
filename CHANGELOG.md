# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

About changelog [here](https://keepachangelog.com/en/1.1.0/)

## [unreleased]
### Changed
- Use uv for dependency management, with a locked `uv.lock`; drop conda `environment.yml`
- Docker image built on uv/python 3.14 slim images, running as non-root user, with checksum-pinned trgt (v5.1.0) and REViewer (v0.2.7) release binaries
- Updated GitHub Actions versions; lint and test with uv on pull requests
- REViewer integration tests run in CI with the pinned REViewer binary and a small stub GRCh37 reference; expected SVG regenerated for REViewer v0.2.7
- Settings are read from environment variables, with `.env` values as defaults, so compose `env_file` and `docker run -e` now work
### Fixed
- Documentation for trgt endpoint
- Temporary files left in `tmp_data`: REViewer metrics/phasing outputs, trgt plots, and everything from failed requests. Each request now uses its own scratch directory, removed when the request finishes
- `/trgt` requests without a catalog used the REViewer catalog instead of `TRGT_CATALOG_PATH`

## [0.2]
### Added
- Added trgt endpoint
- Added version endpoint
- Keep a changelog
- Use pyproject.toml for build
### Changed
- Changed build system: use bioconda

## [0.1]
- Initial release