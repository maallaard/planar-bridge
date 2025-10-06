from typing import Any
import json
import signal
import sys

import objects
import paths
import utils


if sys.version_info.major != 3 or sys.version_info.minor < 13:
    raise SystemExit("Python version must be at least 3.13")


def remaining_sets(set_entries: dict[str, Any]) -> None:

    sets_list: list[str] = []

    for set_entry in set_entries["data"].values():

        set_obj = objects.SetObject(set_entry)

        if (
            not set_obj.states_obj.is_all_highres()
            and set_obj.states_path.exists()
        ):
            sets_list.append(set_obj.set_code)

    sets_str = ", ".join(map(str, sets_list))
    utils.status("Remaining sets with low res scans: " + sets_str, 0)


def pull_meta() -> None:

    utils.status("Comparing local & source files...", 0)

    meta_obj: objects.MetaObject = objects.MetaObject()
    is_outdated = meta_obj.is_outdated()

    if is_outdated:
        utils.status("Downloading bulk files...", 0)
        meta_obj.pull_bulk()

    utils.status(f"Loading bulk data ({meta_obj.date})...", 0)


def pull_all() -> None:

    set_obj: objects.SetObject
    card_obj: objects.CardObject

    set_entries: dict[str, Any]

    set_count: int
    set_total: int

    pull_meta()

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
        message = total_progress + " " + set_obj.set_code.ljust(6)
        message += " AllHighRes: " + str(set_obj.states_obj.is_all_highres())
        utils.status(message, 2)

        for card_entry in set_obj.card_entries:

            set_obj.card_count += 1

            card_obj = objects.CardObject(card_entry, set_obj.set_dir)

            if card_obj.bad_card:
                continue

            card_obj.init_highres_local(
                set_obj.states_obj.get_state(card_obj.img_name)
            )

            if card_obj.is_highres_local and card_obj.path_exists:
                continue

            source_ctrl, source_res = card_obj.parse_source_res()

            if not source_ctrl and not source_res:
                set_obj.states_obj.write_states()
                raise RuntimeError

            if not source_ctrl:
                continue

            if not card_obj.download():
                set_obj.states_obj.write_states()
                raise RuntimeError

            set_obj.states_obj.take_state(card_obj.img_name, source_res)

            card_obj.message(total_progress, set_obj.set_progress())

        set_obj.states_obj.write_states()

    utils.status("Finished successfully.", 0)

    remaining_sets(set_entries)


def main() -> None:

    pull_all()


if __name__ == "__main__":
    main()
