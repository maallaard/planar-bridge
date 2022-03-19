#!/usr/bin/env python3.10

from pathlib import Path
from typing import Any
import gzip
import json
import time

from yaspin import yaspin
import requests
import tomli


SOURCE_DIR = Path(__file__).parent.resolve()

LOCAL_DIR = (Path.home() / '.local' / 'share' / 'planar-bridge').resolve()
IMG_DIR = LOCAL_DIR / 'imgs'
JSON_DIR = LOCAL_DIR / 'json'

LOCAL_DIR.mkdir(exist_ok=True, parents=True)
IMG_DIR.mkdir(exist_ok=True)
JSON_DIR.mkdir(exist_ok=True)

BULK_PATH = JSON_DIR / 'AllPrintings.json'
META_PATH = JSON_DIR / 'Meta.json'


def get_toml() -> dict[str, Any]:

    config_local = LOCAL_DIR / 'config.toml'
    config_source = SOURCE_DIR / 'config.toml'

    if config_local.exists():
        config = config_local.read_text('UTF-8')
    else:
        config = config_source.read_text('UTF-8')

    return tomli.loads(config)


CONFIG = get_toml()


class PaperObject:  # pylint: disable=too-many-instance-attributes

    def __init__(self, paper_dict: dict[str, Any], set_dir: Path) -> None:

        promo_types: list[str] | None = paper_dict.get('promoTypes')

        if promo_types is None:
            promo_types = []

        promo_intrxn = set(CONFIG['exclude']['promos']) & set(promo_types)

        self.bad_promo: bool = len(promo_intrxn) > 0

        self.uuid: str = paper_dict['uuid']
        self.scry_id: str = paper_dict['identifiers']['scryfallId']
        self.related: list[str] | None = paper_dict.get('otherFaceIds')

        self.layout: str = paper_dict['layout']
        self.is_token: bool = self.layout == 'token'

        self.set_code: str = paper_dict['setCode']

        is_back = all((
            self.layout in ['modal_dfc', 'transform'],
            paper_dict.get('side') == 'b'
        ))

        self.face: str = 'back' if is_back else 'front'

        if self.is_token:
            self.set_dir = set_dir / 'tokens'
            self.set_dir.mkdir(exist_ok=True)
        else:
            self.set_dir = set_dir

        split_types = ['adventure', 'aftermath', 'flip', 'split']

        if self.layout in split_types and self.related:
            self.img_name = self.combined_ids()
        else:
            self.img_name = self.uuid

        self.img_path = self.set_dir / (self.img_name + '.jpg')

    def img_res(self) -> bool | None:

        time.sleep(0.1)

        uri = f'https://api.scryfall.com/cards/{self.scry_id}?format=json'
        img = requests.get(uri)

        if img.status_code != 200:
            raise Exception(f"HTTP request gave {img.status_code} for {uri}")

        img_json: dict[str, Any] = img.json()

        if str(img_json['lang']) != 'en':
            if bool(img_json['reprint']):
                return None

        return str(img_json['image_status']) == 'highres_scan'

    def combined_ids(self) -> str:

        if self.related is None:
            return ''

        combined_ids = self.related
        combined_ids.append(self.uuid)
        combined_ids.sort()
        combined_ids = '_'.join(map(str, combined_ids))

        return combined_ids

    def download(self) -> None:

        time.sleep(0.1)

        uri = f'https://api.scryfall.com/cards/{self.scry_id}?format=image'

        if not self.is_token:
            uri = uri + '&face=' + self.face

        img = requests.get(uri)

        if img.status_code != 200:
            raise Exception(f"HTTP request gave {img.status_code} for {uri}")

        self.img_path.write_bytes(img.content)
        print(self.set_code, self.uuid)


class SetObject:

    def __init__(self, set_dict: dict[str, Any]) -> None:

        self.set_type: str = set_dict['type']
        self.set_code: str = set_dict['code']

        self.to_skip: bool = any((
            'isForeignOnly' in set_dict,
            bool(set_dict['isOnlineOnly']),
            self.set_type in CONFIG['exclude']['types'],
            self.set_code in CONFIG['exclude']['sets']
        ))

        self.obj_list: list[dict[str, Any]] = [
            *list(set_dict['cards']),
            *list(set_dict['tokens'])
        ]

        self.set_dir = IMG_DIR / self.set_code
        self.states_path = self.set_dir / '.states.json'

    def load_states(self) -> dict[str, bool]:

        states_dict: dict[str, bool]

        if self.states_path.exists():
            states_dict = json.loads(self.states_path.read_bytes())
        else:
            states_dict = {}

        return states_dict

    def all_highres(self) -> bool:

        return all(self.load_states().values())

    def pull_objs(self) -> None:

        self.set_dir.mkdir(exist_ok=True)

        states_dict = self.load_states()

        print(self.set_code, '------------------------------------')

        for paper_obj in self.obj_list:

            paper_obj = PaperObject(paper_obj, self.set_dir)

            if paper_obj.bad_promo:
                break

            paper_state: bool | None = states_dict.get(paper_obj.img_name)

            if paper_state and paper_obj.img_path.exists():
                break

            img_res = paper_obj.img_res()

            if img_res is None:
                break

            if img_res or not paper_obj.img_path.exists():
                paper_obj.download()
                states_dict[paper_obj.img_name] = img_res

        if states_dict != self.load_states():
            self.states_path.write_text(
                json.dumps(states_dict, sort_keys=True), 'UTF-8'
            )


@yaspin(text='downloading & extracting bulk files...')
def pull_bulk() -> None:

    for target in ['AllPrintings', 'Meta']:

        fob = JSON_DIR / f'{target}.json'
        zip_data = f'https://mtgjson.com/api/v5/{target}.json.gz'

        zip_data = requests.get(zip_data).content
        fob.write_bytes(gzip.decompress(zip_data))


@yaspin(text='comparing local and source builds...')
def check_meta() -> bool:

    if not BULK_PATH.exists() or not META_PATH.exists():
        return True

    uri = requests.get('https://mtgjson.com/api/v5/Meta.json')
    if uri.status_code != 200:
        raise Exception(f"HTTP request gave {uri.status_code} for {uri.url}")

    meta_source = str(uri.json()['meta']['version'])

    meta_local = json.loads(META_PATH.read_bytes())
    meta_local = str(meta_local['meta']['version'])

    meta_source_vers, meta_source_date = meta_source.split('+')
    meta_local_vers, meta_local_date = meta_local.split('+')

    if meta_local_vers != meta_source_vers:
        raise Exception("MTGJSON version has changed")

    return int(meta_local_date) < int(meta_source_date)


def fetch_cardback(art: str = ...) -> None:

    if art == 'original' or art is ...:
        uri = 'https://i.imgur.com/xiYusFq.jpg'

    elif art == 'custom':
        uri = 'https://i.imgur.com/m8SkBeQ.jpg'

    elif art == 'custom_minimal':
        uri = 'https://i.imgur.com/FLa7Gth.jpg'

    else:
        raise Exception(f"Invalid cardback option: '{art}'")

    back_path = IMG_DIR / 'cardback.jpg'

    if back_path.exists():
        return

    back_path.write_bytes(requests.get(uri).content)


def load_states(states_path: Path) -> dict[str, bool]:

    if not states_path.exists():
        states_path.write_text(r'{}', 'UTF-8')

    set_states: dict[str, bool] = json.loads(states_path.read_bytes())

    return set_states


def planar_bridge() -> None:

    with yaspin(text='loading bulk data...'):
        bulk: dict[str, dict] = json.loads(BULK_PATH.read_bytes())['data']

    states_path: Path = IMG_DIR / '.states.json'

    states_dict = load_states(states_path)

    for set_obj in bulk.values():

        set_obj = SetObject(set_obj)

        if not set_obj.to_skip and not states_dict.get(set_obj.set_code):

            set_obj.pull_objs()
            states_dict.update({set_obj.set_code: set_obj.all_highres()})

            if states_dict != load_states(states_path):
                states_path.write_text(
                    json.dumps(states_dict, sort_keys=True), 'UTF-8'
                )


if __name__ == '__main__':

    if check_meta():
        pull_bulk()

    planar_bridge()
