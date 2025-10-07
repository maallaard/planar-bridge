from time import sleep
from pathlib import Path
from typing import Any, Literal, NoReturn
import gzip
import json

from requests import Session

from config import CONFIG
import const
import paths
import utils


session = Session()


class StatesObject:

    def __init__(self, states_path: Path) -> None:

        self.states_path: Path = states_path
        self.states_dict: dict[str, bool] = self.read_states()

    def read_states(self) -> dict[str, bool]:

        states_dict: dict[str, bool] = {}

        if self.states_path.exists():
            states_dict = json.loads(self.states_path.read_bytes())

        return states_dict

    def write_states(self) -> None:

        if self.states_dict == self.read_states() or not self.states_dict:
            return

        self.states_path.write_text(
            json.dumps(self.states_dict, sort_keys=True),
            encoding="UTF-8",
        )

    def get_state(self, name: str) -> bool | None:

        return self.states_dict.get(name)

    def take_state(self, name: str, res: bool) -> None:

        self.states_dict[name] = res

    def is_all_highres(self) -> bool:

        return all(self.states_dict.values())


class CardObject:
    def __init__(
        self, card_dict: dict[str, Any], states_obj: StatesObject, set_dir: Path
    ) -> None:

        self.uuid: str = card_dict["uuid"]
        self.set_code: str = card_dict["setCode"]
        self.scry_id: str = card_dict["identifiers"]["scryfallId"]
        self.message_substr: str = self.uuid + " | " + card_dict["name"]
        self.face: Literal["front", "back"] | None = None
        self.layout: str = card_dict["layout"]

        self.bad_card: bool = self.__init_bad_card(card_dict)
        self.img_name: str = self.__init_img_name(card_dict)

        self.is_highres_local: bool | None = states_obj.get_state(self.img_name)

        if self.layout in const.LAYOUT_TOKEN:
            set_dir = set_dir / "tokens"

        self.img_path: Path = set_dir / (self.img_name + ".jpg")
        self.path_exists: bool = self.img_path.exists()

    def __init_bad_card(self, card_dict: dict[str, Any]) -> bool:

        promo_types: list[str] | None = card_dict.get("promoTypes")

        if promo_types is None:
            promo_types = []

        promo_crosscheck = set(CONFIG["exempt_promos"]) & set(promo_types)

        bad_card_conditions: tuple[bool, ...] = (
            bool(card_dict.get("isReprint")) and not CONFIG["pull_reprints"],
            card_dict["language"] not in [CONFIG["card_lang"], "Phyrexian"],
            card_dict["name"] in ["Checklist", "Double-Faced"],
            bool(card_dict.get("isOnlineOnly")),
            self.layout in const.LAYOUT_BAD,
            bool(card_dict.get("isFunny")),
            len(promo_crosscheck) > 0,
        )

        return any(bad_card_conditions)

    def __init_img_name(self, card_dict: dict[str, Any]) -> str:

        related: list[str] | None = card_dict.get("otherFaceIds")

        if self.layout in const.LAYOUT_TWOSIDED:
            self.face = "front" if card_dict.get("side") == "a" else "back"

        if self.layout in const.LAYOUT_COMBINED and related is not None:
            img_name = related
            img_name.append(self.uuid)
            img_name = list(dict.fromkeys(img_name))
            img_name.sort()
            img_name = ("_").join(map(str, img_name))
        else:
            img_name = self.uuid

        return img_name

    def parse_source_res(self) -> tuple[bool, bool]:

        sleep(const.TIMEOUT)

        url = f"https://api.scryfall.com/cards/{self.scry_id}?format=json"
        source = utils.handle_response(session, url)

        if source is None:
            return False, False

        source_res = str(source.json()["image_status"])

        if source_res in ["placeholder", "missing"]:
            return False, True

        source_state = bool(source_res == "highres_scan")

        if source_state == self.is_highres_local and self.path_exists:
            return False, True

        return True, source_state

    def download(self) -> bool:

        self.img_path.parent.mkdir(exist_ok=True, parents=True)

        sleep(const.TIMEOUT)

        url = f"https://api.scryfall.com/cards/{self.scry_id}?format=image"

        if self.face is not None:
            url += "&face=" + self.face

        img = utils.handle_response(session, url)

        if img is None:
            return False

        self.img_path.write_bytes(img.content)

        return True

    def message(self, total_progress: str, set_progress: str) -> None:

        message = total_progress + " " + self.set_code.ljust(6)
        message += set_progress + self.message_substr
        utils.status(message, 5 if self.path_exists else 4)


class SetObject:
    def __init__(self, set_dict: dict[str, Any]) -> None:

        self.set_code: str = set_dict["code"]
        self.set_dir: Path = paths.DATA_DIR / self.set_code
        self.states_path: Path = self.set_dir / ".states.json"
        self.is_partial: bool = bool(set_dict.get("isPartialPreview"))
        self.states_obj: StatesObject = StatesObject(self.states_path)

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

    def set_progress(self) -> str:

        return utils.progress_str(self.card_count, self.card_total, True)

    # pylint: disable=unused-argument
    def handle_sigint(self, signum, frame) -> NoReturn:

        utils.status("SIGINT recieved (Ctrl-C), saving & exiting...", 6)
        self.states_obj.write_states()
        raise KeyboardInterrupt


class MetaObject:
    def __init__(self) -> None:

        self.local: dict[str, str] = {}
        self.source: dict[str, str] = {}

        self.jsons_exist: bool = (
            paths.BULK_PATH.exists() and paths.META_PATH.exists()
        )

        if self.jsons_exist:
            self.local = self.__fix_vers(
                json.loads(paths.META_PATH.read_bytes())["meta"]
            )

        self.source = self.__init_source()

        self.date: str = self.source["date"]

    def __fix_vers(self, to_fix: dict[str, str]) -> dict[str, str]:

        to_fix.update({"version": to_fix["version"].split("+")[0]})
        return to_fix

    def __init_source(self) -> dict[str, str] | NoReturn:

        url = "https://mtgjson.com/api/v5/Meta.json"
        meta = utils.handle_response(session, url)

        if meta is None:
            raise RuntimeError

        return self.__fix_vers(meta.json()["meta"])

    def pull_bulk(self) -> None | NoReturn:

        for target in ("AllPrintings", "Meta"):

            url = f"https://mtgjson.com/api/v5/{target}.json.gz"
            all_printings = utils.handle_response(session, url)

            if all_printings is None:
                raise RuntimeError

            fob = paths.JSON_DIR / f"{target}.json"
            fob.write_bytes(gzip.decompress(all_printings.content))

    def is_outdated(self) -> bool | NoReturn:

        if not self.jsons_exist and not self.local:
            return True

        same_date: bool = self.local["date"] == self.source["date"]

        if same_date and not CONFIG["always_pull"]:
            raise SystemExit

        if self.local["version"] != const.MTGJSON_VERS:

            message = "MTGJSON has been updated to v" + self.source["version"]
            message += "\n" + const.VERS_WARNING

            utils.status(message, 1)
            proceed = input("Do you want to proceed? [y/N]: ")

            if not utils.boolify_str(proceed, False):
                raise KeyboardInterrupt

        return not same_date
