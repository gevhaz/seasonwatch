# Seasonwatch

## Introduction

**Seasonwatch** is an application that helps you keep track of when new seasons
of TV show you are following are released.

## Dependencies

- Python >= 3.10
- `libgirepository` ([Arch
  Linux](https://archlinux.org/packages/extra/x86_64/libgirepository/),
  [Ubuntu](https://packages.ubuntu.com/jammy/libgirepository1.0-dev)) (for
  showing notifications)

## Installation

Download the wheel from the release page here on GitHub and install it with:

```console
$ pip install seasonwatch-<the version you want to install>-py3-none-any.whl
```

Alternatively, clone the repository and run the following in it:

```console
$ poetry build
$ pip install dist/<your newly built package>
```

You can also run it using poetry directly if you just want to try it:

```console
$ poetry run seasonwatch
```

## Usage

### Initial configuration

In order to use Seasonwatch, you need to have a TMDB API Read Access Token.
Getting one is free, and you get it by registering on
<https://www.themoviedb.org> and then creating an API key according to the
[documentation](https://developer.themoviedb.org/docs). Creating an API key also
gives you an API Read Access Token. Once you have it, manually edit your
configuration file (usually `~/.config/seasonwatchrc`) or run:

```console
$ seasonwatch configure
TMDB API Read Access Token: <your token, then Enter>
Testing token...
Token is valid!
Write new config file, losing all comments? (Y/n): <Y>
Successfully set TMDB token!
```

### Adding new TV show

You can interactively add a new TV show to your database by running the below
command. You'll be prompted to fill in the title of the TV show, the ID, and the
last season you've seen. For example, if you've just watched season 3 of The
Expanse and want to be notified when the next season is released, you'd fill in
it like so:

```console
$ seasonwatch tv --add
What the show should be called: The Expanse
ID of the show (after 'tv/' in the URL on TMDB): 63639
Last watched season: 3
title: The Expanse
TMDB ID: 63639
Last watched season: 3
Does this look ok? (Y/n) Y

Add more shows? (y/N)
```

You can use anything you want as the title. The ID is in the URL of the TV
show on TMDB. In this case, the page on TMDB for the TV show is:
<https://www.themoviedb.org/tv/63639-the-expanse>

The ID is the number that comes after `tv/` in the URL, and before the title of
the TV show. That is, "63639".

You can verify that the TV show is added to the database by running:

```console
$ seasonwatch tv --list
┌────────────────────────────────┬─────────────────────┬──────────────────────────────────────┐
│ Title                          │ Last watched season │ Hyperlink                            │
├────────────────────────────────┼─────────────────────┼──────────────────────────────────────┤
│ The Expanse                    │ 3                   │ https://www.themoviedb.org/tv/63639  │
└────────────────────────────────┴─────────────────────┴──────────────────────────────────────┘
```

### Checking for new seasons

Just run Seasonwatch like so:

```console
$ seasonwatch
Season 4 of The Expanse is out already!
```

You will be shown notifications for shows that are already out or coming out
soon, and the information for all shows in your database will be printed on the
command line. It might be a good idea to automate the running of the script with
a cron job that runs it regularly. Even when run in the background, Seasonwatch
will show you desktop notifications.

## Migration to TMDB

The IMDb API is no longer working, so from version 0.3.0 onward, TMDB is used
instead. If your database was created before then, you will be asked to migrate
when running Seasonwatch for the first time after installing the new version.
There is a helper that will suggest corresponding TMDB IDs for your old shows.

## Development

### Status

Seasonwatch currently supports checking for new TV show seasons only. Version
0.3.0 has been released and is ready to be used for this purpose.

### Bugs

Report bugs under the [issues](https://github.com/gevhaz/seasonwatch/issues) tab
here on GitHub.

### Release process

The release process is automated and happens through the Release workflow. It
just needs to be triggered by pushing a tag. Instructions for creating a release:

1. Create a pull request toward the `dev` branch with a step-up commit that
   bumps the version and updates the changelog if necessary. Merge it.
2. Create a pull request from the `dev` branch toward the `main` branch and
   merge that.
3. Create an annotated tag on the `main` branch:
    `git tag -am "Step up Seasonwatch to version X.Y.Z" vX.Y.Z`.
4. Push the tag: `git push --tags origin vX.Y.Z`.
5. Verify that the Release workflow is triggered and succeeds.
