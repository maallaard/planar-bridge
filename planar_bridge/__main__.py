from typing import Any
import json
import signal
import sys

import objects
import paths
import utils


if sys.version_info.major != 3 or sys.version_info.minor < 13:
    raise SystemExit("Python version must be at least 3.13")


def main() -> None:

    meta_obj: objects.MetaObject
    set_obj: objects.SetObject
    card_obj: objects.CardObject

    set_entries: dict[str, Any]

    progress: str

    set_count: int
    set_total: int

    is_outdated: bool | None

    utils.status("Comparing local & source files...", 0)

    meta_obj = objects.MetaObject()
    is_outdated = meta_obj.is_outdated()

    if is_outdated is None:
        return

    if is_outdated:
        utils.status("Downloading bulk files...", 0)
        meta_obj.pull_bulk()

    utils.status(f"Loading bulk data ({meta_obj.date})...", 0)
    set_entries = json.loads(paths.BULK_PATH.read_bytes())

    set_count = 0
    set_total = len(set_entries["data"])

    for set_entry in set_entries["data"].values():

        set_count += 1
        set_obj = objects.SetObject(set_entry)

        signal.signal(signal.SIGINT, set_obj.handle_sigint)

        if set_obj.to_omit:
            continue

        total_progress = utils.progress_str(set_count, set_total, False)
        utils.status(total_progress + " " + set_obj.set_code.ljust(6), 2)

        set_obj.states_dict = set_obj.read_states()

        for card_entry in set_obj.card_entries:

            set_obj.card_count += 1

            card_obj = objects.CardObject(card_entry, set_obj.set_dir)

            if card_obj.bad_card:
                continue

            card_obj.load_local_res(set_obj.states_dict.get(card_obj.img_name))

            if card_obj.is_highres_local and card_obj.path_exists:
                continue

            source_ctrl, source_res = card_obj.parse_source_res()

            if not source_ctrl and not source_res:
                set_obj.handle_httperror()

            if not source_ctrl:
                continue

            if not card_obj.download():
                set_obj.handle_httperror()

            set_obj.states_dict[card_obj.img_name] = source_res

            card_obj.message(total_progress, set_obj.set_progress())

        set_obj.write_states()

    utils.status("Finished successfully.", 0)


if __name__ == "__main__":
    main()
