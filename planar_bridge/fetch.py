import gzip
import json
import requests

from config import CONFIG
import constants
import static
import paths


WARNING_MSG: str = f"""\
WARN: Planar Bridge is only expected to work with v{constants.MTGJSON_VERS}
WARN: Make sure there are no conflicts before proceeding!
WARN: MTGJSON changelog: https://mtgjson.com/changelog/mtgjson-v5/\
"""


class Fetcher:

    def fix_vers(self, to_fix: dict[str, str]) -> dict[str, str]:
        to_fix.update({"version":to_fix["version"].split("+")[0]})
        return to_fix

    def __init__(self) -> None:

        self.src_info: dict[str, str] = {}
        self.loc_info: dict[str, str] = {}

        self.exists: bool = all((
            paths.BULK_PATH.exists(),
            paths.META_PATH.exists(),
        ))

        uri = "https://mtgjson.com/api/v5/Meta.json"
        dat = requests.get(uri, timeout=30)
        dat.raise_for_status()

        self.src_info = self.fix_vers(dat.json()["meta"])

        if self.exists:
            self.loc_info = json.loads(paths.META_PATH.read_bytes())
            self.loc_info = self.fix_vers(self.loc_info["meta"])

        self.meta_date: str = (self.src_info | self.loc_info)["date"]

    def pull_bulk(self) -> None:

        print(static.timestamp(), "INFO: downloading bulk files...")

        for target in ("AllPrintings", "Meta"):

            uri = f"https://mtgjson.com/api/v5/{target}.json.gz"
            dat = requests.get(uri, timeout=30)
            dat.raise_for_status()

            fob = paths.JSON_DIR / (target + ".json")
            fob.write_bytes(gzip.decompress(dat.content))

    def outdated(self) -> bool | None:

        if not self.exists and not self.loc_info:
            return True

        same_date: bool = self.loc_info["date"] == self.src_info["date"]

        if same_date and not CONFIG["always_pull"]:
            return None

        if self.loc_info["version"] != constants.MTGJSON_VERS:

            print("WARN: MTGJSON has been updated to v" + self.src_info["version"])
            print(WARNING_MSG)

            proceed = input("WARN: Do you want to proceed? [y/N]: ")
            return static.boolify_input(proceed, False)

        return not same_date


def get_cardbacks() -> None:

    cardback_dir = paths.DATA_DIR / ".cardbacks"
    cardback_dir.mkdir(exist_ok=True)

    for i, uri in enumerate(constants.CARDBACK_URIS):

        img_path = cardback_dir / f"cardback-{i+1}.jpg"

        if img_path.exists():
            continue

        img = requests.get(uri, timeout=30)
        img.raise_for_status()

        img_path.write_bytes(img.content)
