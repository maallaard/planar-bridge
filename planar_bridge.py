#!/usr/bin/env python3.10

from pathlib import Path
from typing import Any
import gzip
import json
import time
import sys

import requests
import tomli


MTGJSON_VERS: str = '5.2.0'

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

    config_path = SOURCE_DIR / 'config.toml'

    if config_path.exists():
        config_defined = tomli.loads(config_path.read_text(encoding='UTF-8'))
    else:
        config_defined = {}

    return config_default | config_defined


CONFIG = get_toml()


def get_imgs_dir() -> Path:

    imgs_dir_cfg: str = CONFIG['imgs_dir']

    if bool(imgs_dir_cfg):
        imgs_dir = Path(imgs_dir_cfg)
    else:
        imgs_dir = SOURCE_DIR / 'imgs'

    return imgs_dir


IMGS_DIR = get_imgs_dir()


class PaperObject:

    def __init__(self, paper_dict: dict[str, Any], set_dir: Path) -> None:

        uuid: str = paper_dict['uuid']
        set_code: str = paper_dict['setCode']

        self.message: str = f'{set_code} {uuid}'
        self.scry_id: str = paper_dict['identifiers']['scryfallId']

        promo_types: list[str] | None = paper_dict.get('promoTypes')

        if promo_types is None:
            promo_types = []

        promo_intrxn = set(CONFIG['xmt_promos']) & set(promo_types)

        bad_name = False
        for subst_name in ['Checklist', 'Double-Faced']:
            if subst_name in str(paper_dict['name']):
                bad_name = True

        self.bad_card = any((
            bool(paper_dict.get('isOnlineOnly')),
            bool(paper_dict.get('isFunny')),
            len(promo_intrxn) > 0, bad_name
        ))

        layout: str = paper_dict['layout']
        related: list[str] | None = paper_dict.get('otherFaceIds')

        if layout in ['reversible_card', 'modal_dfc', 'transform']:
            self.face = 'back' if paper_dict.get('side') == 'b' else 'front'
        else:
            self.face = None

        to_combine = all((
            layout in ['adventure', 'aftermath', 'split', 'flip'],
            related is not None
        ))

        if to_combine:
            img_name = related
            img_name.append(uuid)
            img_name = list(dict.fromkeys(img_name))
            img_name.sort()
            img_name = ('_').join(map(str, img_name))
        else:
            img_name = uuid

        self.img_name: str = img_name

        if layout in ['token', 'double_faced_token']:
            set_dir = set_dir / 'tokens'

        self.img_path: Path = set_dir / (self.img_name + '.jpg')

    def resolve(self) -> bool | None:

        time.sleep(0.1)

        uri = f'https://api.scryfall.com/cards/{self.scry_id}?format=json'

        img = requests.get(uri)
        img.raise_for_status()

        img_json: dict[str, Any] = img.json()

        img_status = str(img_json['image_status'])

        does_not_exist = any((
            img_status == 'placeholder',
            img_status == 'missing'
        ))

        foreign_reprint = all((
            str(img_json['lang']) != 'en',
            bool(img_json['reprint'])
        ))

        if foreign_reprint or does_not_exist:
            return None

        return bool(img_status == 'highres_scan')

    def download(self) -> None:

        self.img_path.parent.mkdir(exist_ok=True, parents=True)

        time.sleep(0.1)

        uri = f'https://api.scryfall.com/cards/{self.scry_id}?format=image'

        if self.face is not None:
            uri = f'{uri}&face={self.face}'

        img = requests.get(uri)
        img.raise_for_status()

        self.img_path.write_bytes(img.content)
        print(self.message)


class SetObject:

    def __init__(self, set_dict: dict[str, Any]) -> None:

        self.set_code: str = set_dict['code']
        self.set_dir = IMGS_DIR / self.set_code
        self.states_path = self.set_dir / '.states.json'

        self.to_skip = any((
            bool(set_dict.get('isOnlineOnly')),
            bool(set_dict.get('isForeignOnly')),
            bool(self.set_code in CONFIG['xmt_sets']),
            bool(str(set_dict['type']) in CONFIG['xmt_types']),
        ))

        self.obj_list: list[dict[str, Any]] = [
            *list(set_dict['cards']),
            *list(set_dict['tokens'])
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

        skip_over = all((
            *states_dict.values(),
            self.set_code not in ['SLD', 'SLU'],
            bool(states_dict)
        ))

        if skip_over:
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

            img_res = paper_obj.resolve()

            if img_res is None:
                continue

            to_download = any((
                not paper_obj.img_path.exists(),
                img_res != paper_state
            ))

            if to_download:
                paper_obj.download()
                states_dict[paper_obj.img_name] = img_res

        if states_dict != self.load_states():
            self.states_path.write_text(
                json.dumps(states_dict, sort_keys=True),
                encoding='UTF-8'
            )


def yes_no_bool(ans: str) -> bool | None:

    ans = ans.strip().lower()

    if ans in ['y', 'yes', 't', 'true', '1']:
        return True

    if ans in ['n', 'no', 'f', 'false', '0']:
        return False

    return None


def to_proceed(vers: str) -> None:

    print(f'Warning: MTGJSON has been updated to v{vers}')
    print(f'Planar Bridge is only expected to work with v{MTGJSON_VERS}')
    print('Make sure there are no conflicts before proceeding')
    print('MTGJSON changelong: https://mtgjson.com/changelog/mtgjson-v5/')

    proceed = input('Do you want to proceed? [y/N]: ')
    proceed = yes_no_bool(proceed) if proceed != '' else False

    if not proceed:
        sys.exit()


def check_meta() -> bool:

    print('comparing local and source builds...')

    if not BULK_PATH.exists() or not META_PATH.exists():
        return True

    uri = 'https://mtgjson.com/api/v5/Meta.json'

    rqst = requests.get(uri)
    rqst.raise_for_status()

    meta_source = str(rqst.json()['meta']['version'])

    meta_local = json.loads(META_PATH.read_bytes())
    meta_local = str(meta_local['meta']['version'])

    version, source_date = meta_source.split('+')
    local_date = meta_local.split('+')[1]

    if version != MTGJSON_VERS:
        to_proceed(version)

    up_to_date: bool = int(local_date) < int(source_date)

    return up_to_date


def pull_bulk() -> None:

    print('downloading & extracting bulk files...')

    for target in ('AllPrintings', 'Meta'):

        fob = JSON_DIR / f'{target}.json'
        zip_data = f'https://mtgjson.com/api/v5/{target}.json.gz'

        zip_data = requests.get(zip_data)
        zip_data.raise_for_status()

        fob.write_bytes(gzip.decompress(zip_data.content))


def get_cardbacks() -> None:

    cardback_dir = IMGS_DIR / '.cardbacks'
    cardback_dir.mkdir(exist_ok=True)

    count = 0

    for img_hash in ('xiYusFq', 'm8SkBeQ', 'FLa7Gth'):

        count += 1

        img_path: Path = cardback_dir / f'cardback-{count}.jpg'

        if img_path.exists():
            continue

        uri = f'https://i.imgur.com/{img_hash}.jpg'

        img = requests.get(uri)
        img.raise_for_status()

        img_path.write_bytes(img.content)


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
