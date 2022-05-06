#!/usr/bin/env python3.10

from pathlib import Path
from typing import Any
import gzip
import json
import time

import requests
import tomli


SOURCE_DIR = Path(__file__).resolve().parent

JSON_DIR = SOURCE_DIR / 'json'
JSON_DIR.mkdir(exist_ok=True)

BULK_PATH = JSON_DIR / 'AllPrintings.json'
META_PATH = JSON_DIR / 'Meta.json'


def get_toml() -> dict[str, Any]:

    config_default: dict[str, Any] = {
        'imgs_dir': '',
        'xmt_types': [
            'funny',
            'memorabilia'
        ],
        'xmt_sets': [
            'MB1',
            'PDRC',
            'PLIST',
            'PURL'
        ],
        'xmt_promos': [
            'datestamped',
            'draftweekend',
            'gameday',
            'intropack',
            'jpwalker',
            'mediainsert',
            'planeswalkerstamped',
            'playerrewards',
            'premiereshop',
            'prerelease',
            'promopack',
            'release',
            'setpromo',
            'stamped',
            'themepack',
            'tourney',
            'wizardsplaynetwork'
        ]
    }

    config_local = SOURCE_DIR / 'config.toml'

    if config_local.exists():
        config = tomli.loads(config_local.read_text(encoding='UTF-8'))
    else:
        config = config_default

    return config


CONFIG = get_toml()


def get_imgs_dir() -> Path:

    imgs_dir_conf: str = CONFIG['imgs_dir']

    if imgs_dir_conf:
        imgs_dir = Path(imgs_dir_conf)
    else:
        imgs_dir = SOURCE_DIR / 'imgs'
        imgs_dir.mkdir(exist_ok=True)

    return imgs_dir


IMGS_DIR = get_imgs_dir()


class PaperObject:  # pylint: disable=too-many-instance-attributes

    def __init__(self, paper_dict: dict[str, Any], set_dir: Path) -> None:

        promo_types: list[str] | None = paper_dict.get('promoTypes')

        if promo_types is None:
            promo_types = []

        promo_intrxn = set(CONFIG['xmt_promos']) & set(promo_types)

        self.bad_card: bool = any((
            len(promo_intrxn) > 0,
            bool(paper_dict.get('isFunny')),
            bool(paper_dict.get('isOnlineOnly')),
            'Checklist' in paper_dict['name'],
            'Double-Faced' in paper_dict['name']
        ))

        self.set_code: str = paper_dict['setCode']

        self.uuid: str = paper_dict['uuid']
        self.scry_id: str = paper_dict['identifiers']['scryfallId']
        self.related: list[str] | None = paper_dict.get('otherFaceIds')

        self.layout: str = paper_dict['layout']

        self.is_token: bool = self.layout in [
            'token',
            'double_faced_token'
        ]

        self.is_dfc: bool = self.layout in [
            'modal_dfc',
            'transform',
            'reversible_card'
        ]

        if self.is_dfc:
            self.face = 'back' if paper_dict.get('side') == 'b' else 'front'
        else:
            self.face = None

        self.set_dir = set_dir / 'tokens' if self.is_token else set_dir

    @property
    def img_name(self) -> str:

        split_types = ['adventure', 'aftermath', 'flip', 'split']

        if self.layout in split_types and self.related is not None:
            img_name = self.related
            img_name.append(self.uuid)
            img_name = list(dict.fromkeys(img_name))
            img_name.sort()
            img_name = ('_').join(map(str, img_name))

        else:
            img_name = self.uuid

        return img_name

    @property
    def img_path(self) -> Path:
        return self.set_dir / (self.img_name + '.jpg')

    def img_res(self) -> bool | None:

        time.sleep(0.1)

        uri = f'https://api.scryfall.com/cards/{self.scry_id}?format=json'
        img = requests.get(uri)

        if img.status_code != 200:
            raise Exception(f"HTTP request gave {img.status_code} for {uri}")

        img_json: dict[str, Any] = img.json()

        if str(img_json['lang']) != 'en' and bool(img_json['reprint']):
            return None

        return bool(img_json['highres_image'])

    def download(self) -> None:

        self.set_dir.mkdir(exist_ok=True)

        time.sleep(0.1)

        uri = f'https://api.scryfall.com/cards/{self.scry_id}?format=image'

        if self.is_dfc and self.face is not None:
            uri = f'{uri}&face={self.face}'

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
            self.set_type in CONFIG['xmt_types'],
            self.set_code in CONFIG['xmt_sets']
        ))

        self.obj_list: list[dict[str, Any]] = [
            *list(set_dict['cards']),
            *list(set_dict['tokens'])
        ]

        self.set_dir = IMGS_DIR / self.set_code
        self.states_path = self.set_dir / '.states.json'

    def load_states(self) -> dict[str, bool]:

        states_dict: dict[str, bool]

        if self.states_path.exists():
            states_dict = json.loads(self.states_path.read_bytes())
        else:
            states_dict = {}

        return states_dict

    def pull_objs(self) -> None:

        states_dict = self.load_states()

        if all((
            states_dict.values(),
            self.set_code not in ['SLD', 'SLU'],
            bool(states_dict)
        )):
            return

        for paper_obj in self.obj_list:

            paper_obj = PaperObject(paper_obj, self.set_dir)

            if paper_obj.bad_card:
                continue

            paper_state: bool | None = states_dict.get(paper_obj.img_name)

            if paper_state is None:
                paper_state = False

            if paper_state and paper_obj.img_path.exists():
                continue

            img_res = paper_obj.img_res()

            if img_res is None:
                continue

            if img_res != paper_state or not paper_obj.img_path.exists():
                paper_obj.download()
                states_dict[paper_obj.img_name] = img_res

        if states_dict != self.load_states():
            self.states_path.write_text(
                json.dumps(states_dict, sort_keys=True),
                encoding='UTF-8'
            )


def pull_bulk() -> None:

    print('downloading & extracting bulk files...')

    for target in ['AllPrintings', 'Meta']:

        fob = JSON_DIR / f'{target}.json'
        zip_data = f'https://mtgjson.com/api/v5/{target}.json.gz'

        zip_data = requests.get(zip_data).content
        fob.write_bytes(gzip.decompress(zip_data))


def check_meta() -> bool:

    print('comparing local and source builds...')

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


def get_cardbacks() -> None:

    count = 0

    for img_hash in ('xiYusFq', 'm8SkBeQ', 'FLa7Gth'):

        count += 1

        img_path: Path = IMGS_DIR / f'cardback-{count}.jpg'

        if img_path.exists():
            continue

        uri = f'https://i.imgur.com/{img_hash}.jpg'

        img_path.write_bytes(requests.get(uri).content)


def load_states(states_path: Path) -> dict[str, bool]:

    if not states_path.exists():
        states_path.write_text(r'{}', encoding='UTF-8')

    set_states: dict[str, bool] = json.loads(states_path.read_bytes())

    return set_states


def planar_bridge() -> None:

    print('loading bulk data...')

    bulk: dict[str, Any] = json.loads(BULK_PATH.read_bytes())

    for set_obj in bulk['data'].values():

        set_obj = SetObject(set_obj)

        if set_obj.to_skip:
            continue

        print(set_obj.set_code, '------------------------------------')

        set_obj.pull_objs()


if __name__ == '__main__':

    if check_meta():
        pull_bulk()

    get_cardbacks()

    planar_bridge()
