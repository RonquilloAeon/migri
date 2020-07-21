# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.4.0] - 20 July 2020
### Added
- SQLite support with [aiosqlite](https://github.com/omnilib/aiosqlite)
- Additional testing for empty migration cases

### Fixed
- deprecated() function always uses DeprecationWarning

## [0.3.0] - 6 July 2020
### Added
- Friendly output that replaces log output for info/success messages
- Info output message when migrations directory is empty
- Info output message when migrations are up to date
- New `ConnectionBackend`, `TransactionBackend`, and `Task` base classes
- New `apply_migrations()` function to replace original `run_migrations()` function which
  is now pending deprecation in v1.1.0
- New PostgreSQLConnection class (child of `ConnectionBackend`) to use with `apply_migrations()`
- New Query class to build cross-dialect queries to pass into `ConnectionBackend` methods
- Deprecation warning utility function
- Echo utility to abstract output details such as font style and colors
- Additional testing

### Changed
- Merge `init` and `migrate` commands so `migration` now handles initiation
- Refactor application to support additional dialects in future releases (MySQL/SQLite)

### Removed
- Remove `aiofiles` dependency, file reading synchronous now (to reduce number of dependencies)

## [0.2.1] - 6 June 2020
### Fixed
- Logger name (was `"__name__"` instead of `__name__`)
- Log level not being uppercase (e.g. `info`) in env var or argument causing an error

## [0.2.0] - 6 June 2020
### Added
- Dry run mode
