import urllib3


# Planar Bridge does not work with IPv6 yet.
urllib3.util.connection.HAS_IPV6 = False

MTGJSON_VERS: str = "5.2.0"

CARDBACK_URIS: tuple[str, ...] = (
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
