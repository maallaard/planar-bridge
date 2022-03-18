<p align='center'><img width=256px src=https://user-images.githubusercontent.com/64651989/159095590-39a9c3ce-4a44-46b1-a597-515a3b282015.png /><p>
z
# Planar Bridge

Planar Bridge is a webscraping tool that builds and maintains locally stored
image databases containing high-quality cards scans from Magic the Gathering.

All scans are obtained from [Scryfall](https://scryfall.com/) via their online
card database. Bulk datasets used to build the image databases locally are
from [MTGJSON](https://mtgjson.com/).

Planar Bridge is currently in pre-alpha, so everything you see now is subject
to change at any point.

This README file is incomplete at this point, and will be improved upon as more
commits are made.

Please save and share this project if you want to contribute or see how Planar
Bridge progresses!

## Requirements

As of now, Planar Bridge is only supported on Linux and MacOS, and is only
confirmed to work with Python 3.10.

It is recommended to use [pipenv](https://pipenv.pypa.io/) to install and
update the packages that Planar Bridge requires in order to run.

The required packages are:

- [requests](https://pypi.org/project/requests/)
- [tomli](https://pypi.org/project/tomli/)
- [yaspin](https://pypi.org/project/yaspin/)

## Usage

Planar Bridge stores all card scans in `~/.local/share/planar-bridge/imgs/`,
which you can symlink to a different directory if you want. Each card is
catagorized by set code, with tokens being stored in the `tokens/` subfolder of
the set it belongs to.

Planar Bridge names card images files according to that card\'s UUID from
MTGJSON's database upon creation. At this time, there is no way to name a card
file according to that card's name.

## Configuration

If you want to configure Planar Bridge, copy the default config file and place
it in `~/.local/share/planar-bridge/`.

Currently, the only configurations you can make to Planar Bridge are which
sets, set types, and promo types to exclude from the download process.

## Credits

Logo based on design made by [Lorc](https://lorcblog.blogspot.com/).

## License

This project is developed under an MIT License. For more information,
see [LICENSE](https://github.com/maallaard/planar-bridge/blob/main/LICENSE).
