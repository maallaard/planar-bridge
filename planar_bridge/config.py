from typing import Any
import tomllib

from const import LANGUAGE_MAP, DEFAULT_CONFIG
from paths import CONFIG_PATH


def _get_toml() -> dict[str, Any]:

    config_defined: dict[str, Any] = {}

    if CONFIG_PATH.exists():
        config_defined = tomllib.loads(CONFIG_PATH.read_text(encoding="UTF-8"))

    config_runtime = DEFAULT_CONFIG | config_defined

    for code, name in LANGUAGE_MAP.items():
        if code == config_runtime["card_lang"]:
            config_runtime.update({"card_lang":name})

    return config_runtime


CONFIG = _get_toml()
