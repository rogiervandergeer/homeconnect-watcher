# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Earlier releases (0.0.13 and before) are documented only in the git history.

## [Unreleased]

### Added

- CI now tests Python 3.10 through 3.13 and runs the `ty` type checker.
- This changelog.

### Changed

- `load`, `views` and `refresh-view` now require `--db-uri` (and `load` also `--log-path`), reporting a clear error when missing instead of crashing.
- Releases are published to PyPI via Trusted Publishing.

### Fixed

- Simulator authentication works again: the OAuth grant request now sends the `Origin` header the simulator requires.
- A missing view name in a SQL view definition now raises a descriptive `ValueError`.
