# Changelog

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
- Added ability to configure discogs token, adding new TV shows and new artists
  through the command line with the `configure` verb.
