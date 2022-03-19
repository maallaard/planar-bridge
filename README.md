<p align='center'>
  <img
    width=256px
    src=https://user-images.githubusercontent.com/64651989/159095590-39a9c3ce-4a44-46b1-a597-515a3b282015.png
  />
</p>

<p align='center'>
  <a href="#planar-bridge"><b>Planar Bridge</b></a>
  <b>|</b>
  <a href="#installation">Installation</a>
  <b>|</b>
  <a href="#usage">Usage</a>
  <b>|</b>
  <a href="#configuration">Configuration</a>
  <b>|</b>
  <a href="#credits">Credits</a>
  <b>|</b>
  <a href="#license">License</a>
</p>

---

# Planar Bridge

Planar Bridge is a webscraping tool that builds and maintains locally stored
image databases containing high-quality cards scans from Magic the Gathering.

All scans are obtained from [Scryfall](https://scryfall.com/) via their online
card database. Bulk datasets used to build the image databases locally are
from [MTGJSON](https://mtgjson.com/).

One greatly advantageous feature of Planar Bridge is that it upgrades the
resolution on cards when a higher resolution is available. If a low-resolution
scan exists locally, it will replace it with higher resolution scans if
available on Scryfall. This is especially helpful in handling cards that are
part of a spoiled set and have not been scanned at a crisp high resolution yet.

Planar Bridge is currently in pre-alpha, so everything you see now is subject
to change at any point.

This README file is incomplete at this point, and will be improved upon as more
commits are made.

Please save and share this project if you want to contribute or see how Planar
Bridge progresses!

## Installation

As of now, Planar Bridge is only supported on Linux and MacOS, and is only
confirmed to work with Python 3.10.

To install Planar Bridge, start by installing the
[requests](https://pypi.org/project/requests/) package using pip, and then
clone this repository. This can be done in two commands:

```sh
python3 -m pip install requests
git clone https://github.com/maallaard/planar-bridge.git
```

## Usage

To run Planar Bridge, execute `planar_bridge.py`.

```sh
cd planar-bridge
./planar-bridge.py
```

Planar Bridge will then begin the download process. Keep in mind that with over
600 catagorized sets, downloading all card scans will take several hours even
with the fastest internet connection. However, you can kill the program and
start it later, and it will resume where it left off.

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
sets, set types, and promo types to exclude from the download process. For more
information on set and promo types, visit [MTGJSON](https://mtgjson.com/).

## Credits

Logo based on design made by [Lorc](https://lorcblog.blogspot.com/).

## License

This project is developed under an MIT License. For more information,
see [LICENSE](https://github.com/maallaard/planar-bridge/blob/main/LICENSE).
