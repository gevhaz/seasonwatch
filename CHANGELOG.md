# Changelog

## Unreleased

### Fixed

- Handle all exceptions that can happen when making GET requests, so that the
  user gets some information about the issue before terminating the application.

## [0.3.0] - 2024-01-28

### Added

- It is now possible to interactively convert previously added TV shows from the
  IMDb format to the TMDB format (they have different IDs at each provider).
- Allow specifying TMDB token.

### Changed

- Use TMDB instead of IMDb as source of latest release data.
- Use user-specified XDG base directories for configuration and data.

### Fixed

- Create data directory before trying to add a database to it.
- Specify `requests` as dependency.
- Removed references to musical releases from the command-line interface since
  it is no longer supported.

### Breaking

- Changed database location from a hardcoded `.seasonwatch/database.sqlite` to
  `.local/share/seasonwatch/database.sqlite` or wherever your `XDG_DATA_HOME`
  points to. Also changed configuration location from
  `.config/seasonwatch/config` to `.config/seasonwatchrc` or wherever your
  `XDG_CONFIG_HOME` points to. This is to align with XDG base directory
  specification and respect user settings.

## [0.2.0] - 2023-05-31

### Added

- Ability to list the shows stored in the database.
- Ability to step up the "last watched" season numbers for TV shows.
- Ability to remove TV shows.

### Fixed

- Fix bug where Cinemagoer (dependency) could no longer get the release dates
  from the IMDb API by instead using "original air date".
- Store IMDb ID as TEXT in the SQLite database to prevent losing initial zeroes.

### Removed

- All music-related functionality.

## [0.1.0] - 2022-08-07

### Added

- Added ability to check for new seasons of TV shows
- Added database and logic to interact with it for storing all data about
  earlier checks etc.
- Added ability to check for new music.
- Added ability to configure Discogs token, adding new TV shows and new artists
  through the command line with the `configure` verb.
