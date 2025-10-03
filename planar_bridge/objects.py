from time import sleep
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError
import gzip
import json
import sys

from config import CONFIG
import const
import paths
import utils

from requests import Session

sesh = Session()


class CardObject:
    def __init__(self, card_dict: dict[str, Any], set_dir: Path) -> None:

        self.uuid: str = card_dict["uuid"]
        self.set_code: str = card_dict["setCode"]
        self.scry_id: str = card_dict["identifiers"]["scryfallId"]
        self.message_substr: str = self.uuid + " | " + card_dict["name"]
        self.face: Literal["front", "back"] | None = None
        self.is_highres_local: bool

        layout: str = card_dict["layout"]
        related: list[str] | None = card_dict.get("otherFaceIds")
        promo_types: list[str] | None = card_dict.get("promoTypes")

        if promo_types is None:
            promo_types = []

        promo_crosscheck = set(CONFIG["exempt_promos"]) & set(promo_types)

        bad_card_conditions: tuple[bool, ...] = (
            bool(card_dict.get("isReprint")) and not CONFIG["pull_reprints"],
            card_dict["language"] not in [CONFIG["card_lang"], "Phyrexian"],
            card_dict["name"] in ["Checklist", "Double-Faced"],
            bool(card_dict.get("isOnlineOnly")),
            bool(card_dict.get("isFunny")),
            layout in const.LAYOUT_BAD,
            len(promo_crosscheck) > 0,
        )

        self.bad_card: bool = any(bad_card_conditions)

        if layout in const.LAYOUT_TWOSIDED:
            self.face = "front" if card_dict.get("side") == "a" else "back"

        if layout in const.LAYOUT_COMBINED and related is not None:
            img_name = related
            img_name.append(self.uuid)
            img_name = list(dict.fromkeys(img_name))
            img_name.sort()
            img_name = ("_").join(map(str, img_name))
        else:
            img_name = self.uuid

        self.img_name: str = img_name

        if layout in const.LAYOUT_TOKEN:
            set_dir = set_dir / "tokens"

        self.img_path: Path = set_dir / (self.img_name + ".jpg")
        self.path_exists: bool = self.img_path.exists()

    def load_local_res(self, card_state: bool | None) -> None:

        self.is_highres_local = False if card_state is None else card_state

    def parse_source_res(self) -> bool | None:

        sleep(const.TIMEOUT)

        url = f"https://api.scryfall.com/cards/{self.scry_id}?format=json"

        source = sesh.get(url, timeout=30)
        source_res = str(source.json()["image_status"])

        if source_res in ["placeholder", "missing"]:
            return None

        source_state = bool(source_res == "highres_scan")

        if source_state == self.is_highres_local and self.path_exists:
            return None

        return source_state

    def download(self) -> bool:

        self.img_path.parent.mkdir(exist_ok=True, parents=True)

        sleep(const.TIMEOUT)

        url = f"https://api.scryfall.com/cards/{self.scry_id}?format=image"

        if self.face is not None:
            url += "&face=" + self.face

        img = sesh.get(url, timeout=30)

        try:
            img.raise_for_status()
        except HTTPError:
            return False

        self.img_path.write_bytes(img.content)

        return True

    def persist_response(self) -> bool:

        for i in range(1, 6):

            if self.download():
                return True

            sleep(i * 30)

        return False

    def message(self, progress: str) -> None:

        message = self.set_code.ljust(5) + progress + self.message_substr
        utils.status(message, 5 if self.path_exists else 4)


class SetObject:
    def __init__(self, set_dict: dict[str, Any]) -> None:

        self.set_code: str = set_dict["code"]
        self.set_dir: Path = paths.DATA_DIR / self.set_code
        self.states_path: Path = self.set_dir / ".states.json"
        self.is_partial: bool = bool(set_dict.get("isPartialPreview"))
        self.states_dict: dict[str, bool] = {}

        omit_conditions: tuple[bool, ...] = (
            bool(str(set_dict["type"]) in CONFIG["exempt_types"]),
            bool(self.set_code in CONFIG["exempt_sets"]),
            bool(set_dict.get("isForeignOnly")),
            bool(set_dict.get("isOnlineOnly")),
        )

        self.to_omit: bool = any(omit_conditions)

        if self.set_code in CONFIG["pardoned_sets"]:
            self.to_omit = False

        self.card_entries: list[dict[str, Any]] = [
            *list(set_dict["cards"]),
            *list(set_dict["tokens"]),
        ]

        self.card_total: int = len(self.card_entries)
        self.card_count: int = 0

    def load_states(self) -> dict[str, bool]:

        states_dict: dict[str, bool] = {}

        if self.states_path.exists():
            states_dict = json.loads(self.states_path.read_bytes())

        return states_dict

    def save_states(self) -> None:

        if self.states_dict == self.load_states() or not self.states_dict:
            return

        self.states_path.write_text(
            json.dumps(self.states_dict, sort_keys=True),
            encoding="UTF-8",
        )

    def progress(self) -> str:

        return utils.progress_str(self.card_count, self.card_total, True)

    # pylint: disable=unused-argument
    def handle_sigint(self, signum, frame):

        utils.status("SIGINT recieved (Ctrl-C), saving & exiting...", 6)
        self.save_states()
        sys.exit(1)


class MetaObject:
    def __init__(self) -> None:

        self.local: dict = {}
        self.source: dict = {}

        bulks_exist: tuple[bool, bool] = (
            paths.BULK_PATH.exists(),
            paths.META_PATH.exists(),
        )

        self.bulks_exist: bool = all(bulks_exist)

        url = "https://mtgjson.com/api/v5/Meta.json"
        dat = sesh.get(url, timeout=30)
        dat.raise_for_status()

        self.source = self.fix_vers(dat.json()["meta"])

        if self.bulks_exist:
            self.local = json.loads(paths.META_PATH.read_bytes())
            self.local = self.fix_vers(self.local["meta"])

        self.date: str = self.source["date"]

    def fix_vers(self, to_fix: dict[str, str]) -> dict[str, str]:

        to_fix.update({"version": to_fix["version"].split("+")[0]})
        return to_fix

    def pull_bulk(self) -> None:

        for target in ("AllPrintings", "Meta"):

            url = f"https://mtgjson.com/api/v5/{target}.json.gz"
            dat = sesh.get(url, timeout=30)
            dat.raise_for_status()

            fob = paths.JSON_DIR / f"{target}.json"
            fob.write_bytes(gzip.decompress(dat.content))

        if CONFIG["pull_cardbacks"]:
            self.cardbacks()

    def is_outdated(self) -> bool | None:

        if not self.bulks_exist and not self.local:
            return True

        same_date: bool = self.local["date"] == self.source["date"]

        if same_date and not CONFIG["always_pull"]:
            return None

        if self.local["version"] != const.MTGJSON_VERS:

            message = "MTGJSON has been updated to v"
            message += self.source["version"]
            message += "\n" + const.VERS_WARNING

            utils.status(message, 1)
            proceed = input("Do you want to proceed? [y/N]: ")

            if not utils.boolify_str(proceed, False):
                return None

        return not same_date

    def cardbacks(self) -> None:

        paths.CARDBACK_DIR.mkdir(exist_ok=True)

        for i, url in enumerate(const.CARDBACK_URLS):

            img_path = paths.CARDBACK_DIR / f"cardback-{i+1}.jpg"

            if img_path.exists():
                continue

            img = sesh.get(url, timeout=30)
            img.raise_for_status()

            img_path.write_bytes(img.content)
