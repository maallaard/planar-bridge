from pathlib import Path
from typing import Any
import json
import time

import requests
#from colorama import Fore, Back, Style

from config import CONFIG, MTG_LANG
from static import timestamp
import constants
import fetch
import paths


class PaperObject:
    def __init__(self, paper_dict: dict[str, Any], set_dir: Path) -> None:

        uuid: str = paper_dict["uuid"]
        layout: str = paper_dict["layout"]
        set_code: str = paper_dict["setCode"]

        self.message: str = set_code +  " | " + uuid
        self.scry_id: str = paper_dict["identifiers"]["scryfallId"]

        promo_types: list[str] | None = paper_dict.get("promoTypes")
        related: list[str] | None = paper_dict.get("otherFaceIds")

        if promo_types is None:
            promo_types = []

        promo_intrxn = set(CONFIG["exempt_promos"]) & set(promo_types)
        no_reprints = all((
            paper_dict.get("isReprint"),
            not CONFIG["pull_reprints"],
        ))

        bad_name = False
        substitute_names = ["Checklist", "Double-Faced"]

        for sub_name in substitute_names:
            if sub_name in str(paper_dict["name"]):
                bad_name = True

        self.bad_card: bool = any((
            paper_dict["language"] not in [MTG_LANG, "Phyrexian"],
            bool(paper_dict.get("isOnlineOnly")),
            bool(paper_dict.get("isFunny")),
            layout in constants.LAYOUT_BAD,
            len(promo_intrxn) > 0,
            no_reprints,
            bad_name,
        ))

        # if self.bad_card and set_code in CONFIG["pardoned_sets"]:
            # self.bad_card = False

        if layout in constants.LAYOUT_TWOSIDED:
            self.face = "back" if paper_dict.get("side") == "b" else "front"
        else:
            self.face = None

        if layout in constants.LAYOUT_COMBINED and related is not None:
            img_name = related
            img_name.append(uuid)
            img_name = list(dict.fromkeys(img_name))
            img_name.sort()
            img_name = ("_").join(map(str, img_name))
        else:
            img_name = uuid

        self.img_name: str = img_name

        if layout in constants.LAYOUT_TOKEN:
            set_dir = set_dir / "tokens"

        self.img_path: Path = set_dir / (self.img_name + ".jpg")

    def resolve(self) -> bool | None:

        time.sleep(0.1)

        uri = f"https://api.scryfall.com/cards/{self.scry_id}?format=json"

        img = requests.get(uri, timeout=30)
        img.raise_for_status()

        img_status = str(img.json()["image_status"])

        if img_status in ["placeholder", "missing"]:
            return None

        return bool(img_status == "highres_scan")

    def download(self) -> None:

        self.img_path.parent.mkdir(exist_ok=True, parents=True)

        time.sleep(0.1)

        uri = f"https://api.scryfall.com/cards/{self.scry_id}?format=image"

        if self.face is not None:
            uri = uri + "&face=" + self.face

        img = requests.get(uri, timeout=30)
        img.raise_for_status()

        self.img_path.write_bytes(img.content)
        print(timestamp(), self.message)


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

    def pull_objs(self) -> None:

        states_dict = self.load_states()

        skip_over: bool = all((
            *states_dict.values(),
            self.set_code not in CONFIG["continuous_sets"],
            not self.is_partial,
            bool(states_dict),
        ))

        action_msg =  "(skipped)" if skip_over else "(loading)"

        print(timestamp(), "INFO:", self.set_code, action_msg)

        if skip_over:
            return

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

            if img_res is None or (img_res == paper_state and path_exists):
                continue

            status_msg = "ENHANCE: " if path_exists else "NEWCARD: "

            paper_obj.message = status_msg + paper_obj.message

            paper_obj.download()
            states_dict[paper_obj.img_name] = img_res

        if states_dict != self.load_states():
            self.states_path.write_text(
                json.dumps(states_dict, sort_keys=True),
                encoding="UTF-8",
            )


def planar_bridge() -> None:

    print(timestamp(), "INFO: comparing local & source files...")

    fetcher = fetch.Fetcher()

    is_outdated: bool | None = fetcher.outdated()

    if is_outdated is None:
        return

    if is_outdated:
        fetcher.pull_bulk()

    print(timestamp(), f"INFO: loading bulk data ({fetcher.meta_date})...")

    bulk: dict[str, Any] = json.loads(paths.BULK_PATH.read_bytes())

    if CONFIG["pull_cardbacks"]:
        fetch.get_cardbacks()

    for set_obj in bulk["data"].values():

        set_obj = SetObject(set_obj)

        if set_obj.to_skip:
            continue

        set_obj.pull_objs()

    print(timestamp(), "INFO: Finished successfully.")


if __name__ == "__main__":
    planar_bridge()
