from typing import Any
import tomli

import paths


MTG_LANG: str = "English"

DEFAULTS: dict[str, Any] = {
    "always_pull": False,
    "pull_reprints": False,
    "pull_cardbacks": False,
    "pardoned_sets": ["30A"],
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


def _get_toml() -> dict[str, Any]:

    config_path = paths.DATA_DIR / "config.toml"

    config_defined: dict[str, Any] = {}

    if config_path.exists():
        config_defined = tomli.loads(config_path.read_text(encoding="UTF-8"))

    return DEFAULTS | config_defined


CONFIG = _get_toml()
