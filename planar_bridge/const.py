from typing import Any


MTGJSON_VERS: str = "5.2.1"

TIMEOUT: float = 0.2

CARDBACK_URLS: tuple[str, ...] = (
    "https://i.imgur.com/xiYusFq.jpg",
    "https://i.imgur.com/m8SkBeQ.jpg",
    "https://i.imgur.com/FLa7Gth.jpg",
)

LAYOUT_COMBINED: list[str] = [
    "adventure",
    "aftermath",
    "flip",
    "split",
]

LAYOUT_TWOSIDED: list[str] = [
    "modal_dfc",
    "reversible_card",
    "transform",
]

LAYOUT_TOKEN: list[str] = [
    "token",
    "double_faced_token",
]

LAYOUT_BAD: list[str] = [
    "art_series",
    "augment",
    "host",
]

LANGUAGE_MAP: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese (Brazil)",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "zhs": "Chinese Simplified",
    "zht": "Chinese Traditional",
    "he": "Hebrew",
    "la": "Latin",
    "grc": "Ancient Greek",
    "ar": "Arabic",
    "sa": "Sanskrit",
    "ph": "Phyrexian",
    "px": "Phyrexian",
}

DEFAULT_CONFIG: dict[str, Any] = {
    "always_pull": True,
    "pull_reprints": False,
    "pull_cardbacks": False,
    "card_lang": "en",
    "pardoned_sets": [
        "30A",
    ],
    "continuous_sets": [
        "SLD",
        "SLU",
        "SLX",
    ],
    "exempt_sets": [
        "MB1",
        "PDRC",
        "PLIST",
        "PURL",
        "UPLIST",
    ],
    "exempt_promos": [
        "datestamped",
        "draftweekend",
        "gameday",
        "intropack",
        "jpwalker",
        "mediainsert",
        "planeswalkerstamped",
        "playerrewards",
        "premiereshop",
        "prerelease",
        "promopack",
        "release",
        "setpromo",
        "stamped",
        "themepack",
        "thick",
        "tourney",
        "wizardsplaynetwork",
    ],
    "exempt_types": [
        "alchemy",
        "funny",
        "memorabilia",
        "token",
    ],
}

VERS_WARNING: str = '\n'.join((
    "Planar Bridge is only expected to work with v" + MTGJSON_VERS,
    "Make sure there are no conflicts before proceeding!",
    "MTGJSON changelog: https://mtgjson.com/changelogs/mtgjson-v5/",
))
