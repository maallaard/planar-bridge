<p align='center'>
  <img
    width=256px
    src=https://user-images.githubusercontent.com/64651989/159095590-39a9c3ce-4a44-46b1-a597-515a3b282015.png
  />
</p>

<p align='center'>
  <a href="#planar-bridge"><b>Planar Bridge</b></a>
  <b>|</b>
  <a href="#terms-of-use">Terms of Use</a>
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

Planar Bridge is supported on Linux, MacOS, and Windows. However, it is only
confirmed to work with at least Python 3.10.0, so check your installed Python
version if you are unsure:

```sh
$ python3 -V
Python 3.10.0
```

(note that lines in code blocks beginning with `$` means this line is used as
a user-executed command)

To install Planar Bridge, start by installing the
[requests](https://pypi.org/project/requests/) and
[tomli](https://pypi.org/project/tomli/) packages using pip, and then clone
this repository. This can be done in two commands:

```sh
$ python3 -m pip install requests tomli
$ git clone https://github.com/maallaard/planar-bridge.git
```

## Usage

To run Planar Bridge, execute `planar_bridge.py`.

```sh
$ ./planar-bridge/planar-bridge.py
```

Planar Bridge will then begin the download process. Keep in mind that with over
600 catagorized sets, downloading all card scans will take several hours even
with the fastest internet connection. However, you can kill the program and
start it later, and it will resume where it left off.

If you are on Linux/MacOS, Planar Bridge will store files in $XDG_DATA_HOME
(`~/.local/share/planar-bridge`). If you are on Windows, it will be in
%LOCALAPPDATA% (`C:\Users\<username>\AppData\Local\planar-bridge`).

Here is an example file tree layout of Planar Bridge's local folder inside
your local data directory with fake UUIDs:

```
planar-bridge/
├─ imgs/
│  ├─ LEA/
│  │  ├─ tokens/
│  │  │  ├─ 01234567-89ab-cdef-0123-456789abcdef.jpg
│  │  │  ├─ fedcba98-7654-3210-fedc-ba9876543210.jpg
│  │  │  └─ ...
│  │  ├─ 01234567-89ab-cdef-fedc-ba9876543210.jpg
│  │  ├─ fedcba98-7654-3210-0123-456789abcdef.jpg
│  │  ├─ .states.json
│  │  └─ ...
│  ├─ LEB/
│  │  ├─ 1f2e3d4c-5b6a-7089-9807-a6b5-c4d3e2f1.jpg
│  │  ├─ 9807a6b5-c4d3-e2f1-1f2e-3d4c-5b6a7089.jpg
│  │  ├─ .states.json
│  │  └─ ...
│  ├─ 2ED/
│  │  └─ ...
│  ├─ ...
│  └─ .states.json
├─ json/
│  ├─ AllPrintings.json
│  └─ Meta.json
└─ config.toml
```

Planar Bridge stores all card scans in `imgs/`, which you can symlink to a
different directory if you want. Each card is catagorized by set code, with
tokens being stored in the `tokens/` subfolder of the set it belongs to.

Planar Bridge names card images files according to that card's UUID from
MTGJSON's database upon creation. At this time, there is no way to name a card
file according to that card's name.

In every set code folder, there will be a file named `.states.json`. This JSON
file contains the resolutions of all the card scans in that set according to
their UUIDs. This file is also found in `imgs/`, which states for each set code
whether or not every card in that set is at the highest resolution available.
**DO NOT** delete these files. If you do, you will have to redownload images you
already have.

## Configuration

If you want to configure Planar Bridge, copy the default config file and place
it in `~/.local/share/planar-bridge/`.

Currently, the only configurations you can make to Planar Bridge are which
sets, set types, and promo types to exclude from the download process. For more
information on set and promo types, visit [MTGJSON](https://mtgjson.com/).

## Terms of Use

By downloading and running this program, you agree to Wizards of the Coast's
[Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy) as
well as Scryfall's [Terms of Service](https://scryfall.com/docs/terms).
If you have any questions about what you can/cannot do regarding these
policies, carefully read each article and FAQs on the links to WotC's and
Scryfall's terms and conditions.

This program has been made with the intent of respecting the 50 - 100
millisecond request rate limit that Scryfall enforces on their website:

> We kindly ask that you insert 50 – 100 milliseconds of delay between the
> requests you send to the server at api.scryfall.com. (i.e., 10 requests per
> second on average).

(from [Scryfall's API homepage](https://scryfall.com/docs/api))

**DO NOT** modify or remove this program's built-in timer that regulates the
request rate of itself. If you remove it, your IP address will likely get
blocked, either temporarily or permanently. Again, **DO NOT** modify the
request rate of this program.

With that being said, Planar Bridge and its developers accept absolutely zero
responsibility regarding incidents that breach WotC's, Scryfall's, and Planar
Bridge's terms and conditions. **USE AT YOUR OWN RISK!!!**

## Credits

Logo based on design made by [Lorc](https://lorcblog.blogspot.com/).

## License

This project is developed under an MIT License. For more information,
see [LICENSE](https://github.com/maallaard/planar-bridge/blob/main/LICENSE).
