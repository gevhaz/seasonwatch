# seasonwatch

## Introduction

**seasonwatch** is a script that helps you keep track of when new seasons of
TV shows you are following are released and when new albums of artists you are
interested in drop.

## Installation

You will need Python 3.10.

First install the one dependency that cannot be automatically installed with
pip, which is the library for handling GObject instrospection data. For Ubuntu,
it's done like so:

```shell
# apt install libgirepository1.0-dev
```

It is needed for showing notifications.

Next, download the wheel from the release page here on Github and install it
with:

```shell
$ pip3 install seasonwatch-<the version you want to install>-py3-none-any.whl
```

## Usage

### Initial configuration

In order to use Seasonwatch, you need to have a TMDB API Read Access Token.
Getting one is free, and you get it by registering on
<https://www.themoviedb.org> and then creating an API key according to the
[documentation](https://developer.themoviedb.org/docs). Creating an API key also
gives you an API Read Access Token. Once you have it, manually edit your
configuration file (usually `~/.config/seasonwatchrc`) or running:

```command
$ seasonwatch configure
TMDB API Read Access Token: <your token, then Enter>
Testing token...
Token is valid!
Write new config file, losing all comments? (Y/n): <Y>
Successfully set TMDB token!
```

### Adding new shows or artists

Start by adding a TV show or an artist. For adding a TV show, run:

```shell
$ seasonwatch configure --tv-shows
```

You'll be prompted to fill in the title of the show, the ID, and the last season
you've seen. For example, if you've just watched season 4 of The Expanse and
want to be notified when the next season is released, you'd fill in it like so:

```text
Title of the show: The Expanse
ID of the show (after 'tt' in the url on IMDB): 3230854
Last watched season: 4
```

You can find the ID in the IMDb URL. In this case, the page on IMDb for the show
is: https://www.imdb.com/title/tt3230854/?ref_=fn_al_tt_1

the ID is the number that comes after "tt" in the URL, and before the first '/'
after that, that is '3230854'.

Adding an artist works in a similar way. First, run:

```
$ seasonwatch configure --artist
```

Then, if you want to follow e.g. Abul Mogard, find his page in discogs.com, get
the ID from there, and fill it in:

```text
Name of the artist: Abul Mogard
ID of the artist (number after 'artist' in the Discogs url): 2803639
```

The URL in this case is: https://www.discogs.com/artist/2803639-Abul-Mogard
where the ID should be easy to see.

### Checking for new seasons or albums

Just run seasonwatch like so:

```
$ seasonwatch
```

You will get notifications for the the most urgent finds, but all info will be
printed on the command line. It might be a good idea to automate the running of
the script with e.g. a cron job that runs it regularly.

## Development

seasonwatch currently supports checking for new TV show seasons and new albums
by artists. Version 0.1.0 has been released and it should be good to use by
anyone.

### Bugs

Report bugs under the [issues](https://github.com/gevhaz/seasonwatch/issues) tab here on Github.

### Planned features

- Support checking for when a movie is released
- Put module package on PyPI
