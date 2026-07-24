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
- Throttled follow-up requests are deferred until the throttle interval expires instead of being dropped, so state changes are observed even when an appliance stops pushing status events.

### Fixed

- Simulator authentication works again: the OAuth grant request now sends the `Origin` header the simulator requires.
- An unexpected error while reading the event stream now triggers a reconnect instead of stalling the watcher.
- A missing view name in a SQL view definition now raises a descriptive `ValueError`.
