from pathlib import Path
from time import sleep
from typing import Any
import gzip
import json

from config import CONFIG
import const
import paths
import utils

from requests import Session
sesh = Session()


class PaperObject:
    def __init__(self, paper_dict: dict[str, Any], set_dir: Path) -> None:

        self.uuid: str = paper_dict["uuid"]
        self.set_code: str = paper_dict["setCode"]
        self.scry_id: str = paper_dict["identifiers"]["scryfallId"]

        layout: str = paper_dict["layout"]
        related: list[str] | None = paper_dict.get("otherFaceIds")
        promo_types: list[str] | None = paper_dict.get("promoTypes")

        if promo_types is None:
            promo_types = []

        promo_intrxn = set(CONFIG["exempt_promos"]) & set(promo_types)

        self.bad_card: bool = any((
            paper_dict.get("isReprint") and not CONFIG["pull_reprints"],
            paper_dict["language"] not in [CONFIG["card_lang"], "Phyrexian"],
            paper_dict["name"] in ["Checklist", "Double-Faced"],
            bool(paper_dict.get("isOnlineOnly")),
            bool(paper_dict.get("isFunny")),
            layout in const.LAYOUT_BAD,
            len(promo_intrxn) > 0,
        ))

        if layout in const.LAYOUT_TWOSIDED:
            self.face = "back" if paper_dict.get("side") == "b" else "front"
        else:
            self.face = None

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

    def resolve(self) -> bool | None:

        sleep(0.1)

        url = f"https://api.scryfall.com/cards/{self.scry_id}?format=json"

        img = sesh.get(url, timeout=30)
        img.raise_for_status()

        img_status = str(img.json()["image_status"])

        if img_status in ["placeholder", "missing"]:
            return None

        return bool(img_status == "highres_scan")

    def download(self) -> None:

        self.img_path.parent.mkdir(exist_ok=True, parents=True)

        sleep(0.1)

        url = f"https://api.scryfall.com/cards/{self.scry_id}?format=image"

        if self.face is not None:
            url += "&face=" + self.face

        img = sesh.get(url, timeout=30)
        img.raise_for_status()

        self.img_path.write_bytes(img.content)


class SetObject:
    def __init__(self, set_dict: dict[str, Any]) -> None:

        self.set_code: str = set_dict["code"]
        self.set_dir: Path = paths.DATA_DIR / self.set_code
        self.states_path: Path = self.set_dir / ".states.json"
        self.is_partial: bool = bool(set_dict.get("isPartialPreview"))

        self.to_skip: bool = any((
            bool(str(set_dict["type"]) in CONFIG["exempt_types"]),
            bool(self.set_code in CONFIG["exempt_sets"]),
            bool(set_dict.get("isForeignOnly")),
            bool(set_dict.get("isOnlineOnly")),
        ))

        if self.set_code in CONFIG["pardoned_sets"]:
            self.to_skip = False

        self.obj_list: list[dict[str, Any]] = [
            *list(set_dict["cards"]),
            *list(set_dict["tokens"]),
        ]

    def load_states(self) -> dict[str, bool]:

        states_dict: dict[str, bool]

        if self.states_path.exists():
            states_dict = json.loads(self.states_path.read_bytes())
        else:
            states_dict = {}

        return states_dict

    def pull(self) -> None:

        states_dict = self.load_states()

        skip_over: bool = all((
            *states_dict.values(),
            self.set_code not in CONFIG["continuous_sets"],
            not self.is_partial,
            bool(states_dict),
        ))

        if skip_over:

            if not CONFIG["hide_skipped"]:
                utils.status(self.set_code, 3)

            return

        utils.status(self.set_code, 2)

        for paper_obj in self.obj_list:

            paper_obj = PaperObject(paper_obj, self.set_dir)

            if paper_obj.bad_card:
                continue

            path_exists: bool = paper_obj.img_path.exists()
            paper_state: bool | None = states_dict.get(paper_obj.img_name)

            if paper_state is None:
                paper_state = False

            if paper_state and path_exists:
                continue

            img_res = paper_obj.resolve()

            if (img_res == paper_state and path_exists) or img_res is None:
                continue

            paper_obj.download()
            states_dict[paper_obj.img_name] = img_res

            message = paper_obj.set_code + " > " + paper_obj.uuid
            utils.status(message, 5 if path_exists else 4)

        if states_dict != self.load_states():
            self.states_path.write_text(
                json.dumps(states_dict, sort_keys=True),
                encoding="UTF-8",
            )


class FetcherObject:
    def __init__(self) -> None:
        self.source: dict[str, str]
        self.local: dict[str, str]

        self.bulks_exist: bool = all((
            paths.BULK_PATH.exists(),
            paths.META_PATH.exists(),
        ))

        url = "https://mtgjson.com/api/v5/Meta.json"
        dat = sesh.get(url, timeout=30)
        dat.raise_for_status()

        self.source = self.fix_vers(dat.json()["meta"])

        if self.bulks_exist:
            self.local = json.loads(paths.META_PATH.read_bytes())
            self.local = self.fix_vers(self.local["meta"])

        self.date: str = self.source["date"]

    def fix_vers(self, to_fix: dict[str, str]) -> dict[str, str]:
        to_fix.update({"version":to_fix["version"].split("+")[0]})
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

    def outdated(self) -> bool | None:

        if not (self.bulks_exist or self.local):
            return True

        same_date: bool = self.local["date"] == self.source["date"]

        if same_date and not CONFIG["always_pull"]:
            return None

        if self.local["version"] != const.MTGJSON_VERS:

            message = "MTGJSON has been updated to v"
            message += self.source["version"]
            message += '\n' + const.VERS_WARNING

            utils.status(message, 1)

            proceed = input("Do you want to proceed? [y/N]: ")
            return utils.boolify_str(proceed, False)

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
