from dataclasses import dataclass
from typing import Any
import tomllib

from const import LANGUAGE_MAP, DEFAULT_CONFIG
from paths import CONFIG_PATH


@dataclass
class Config:

    pull_reprints: bool
    card_lang: str
    pardoned_sets: list[str]
    continuous_sets: list[str]
    exempt_sets: list[str]
    exempt_promos: list[str]
    exempt_types: list[str]

    def __init__(self) -> None:

        config: dict[str, Any] = {}

        if CONFIG_PATH.exists():
            config = tomllib.loads(CONFIG_PATH.read_text(encoding="UTF-8"))

        config = DEFAULT_CONFIG | config

        for code, name in LANGUAGE_MAP.items():
            if code == config["card_lang"]:
                config.update({"card_lang": name})

        self.pull_reprints = config["pull_reprints"]
        self.card_lang = config["card_lang"]
        self.pardoned_sets = config["pardoned_sets"]
        self.continuous_sets = config["continuous_sets"]
        self.exempt_sets = config["exempt_sets"]
        self.exempt_promos = config["exempt_promos"]
        self.exempt_types = config["exempt_types"]


CONFIG: Config = Config()
