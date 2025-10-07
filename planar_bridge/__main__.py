from typing import Any
import json
import signal
import sys

from objects import CardObject, MetaObject, SetObject
import paths
import utils


if sys.version_info.major != 3 or sys.version_info.minor < 13:
    raise SystemExit("Python version must be at least 3.13")


def remaining_sets(set_entries: dict[str, dict[str, Any]]) -> None:

    set_list: list[str] = []

    for set_entry in set_entries.values():

        set_obj = SetObject(set_entry)

        if (
            not set_obj.states_obj.is_all_highres()
            and set_obj.states_path.exists()
        ):
            set_list.append(set_obj.set_code)

    sets_str = ", ".join(map(str, set_list))
    utils.status("Remaining sets with low res scans: " + sets_str, 0)


def pull_meta() -> None:

    utils.status("Comparing local & source files...", 0)

    meta_obj: MetaObject = MetaObject()
    is_outdated = meta_obj.is_outdated()

    if is_outdated:
        utils.status("Downloading bulk files...", 0)
        meta_obj.pull_bulk()

    utils.status(f"Loading bulk data ({meta_obj.date})...", 0)


def pull_card(card_obj: CardObject) -> tuple[str, bool]:

    if card_obj.bad_card:
        return "", True

    if card_obj.is_highres_local and card_obj.path_exists:
        return "", True

    source_ctrl, source_res = card_obj.parse_source_res()

    if not source_ctrl:

        if not source_res:
            return "", False

        return "", True

    if not card_obj.download():
        return "", False

    return card_obj.img_name, source_res


def pull_set(set_obj: SetObject, total_progress: str) -> None:

    card_obj: CardObject

    message = total_progress + " " + set_obj.set_code.ljust(6)
    message += " AllHighRes: " + str(set_obj.states_obj.is_all_highres())
    utils.status(message, 2)

    signal.signal(signal.SIGINT, set_obj.handle_sigint)

    for card_entry in set_obj.card_entries:

        set_obj.card_count += 1

        card_obj = CardObject(
            card_entry,
            set_obj.states_obj,
            set_obj.set_dir,
        )

        img_name, source_res = pull_card(card_obj)

        if not img_name:

            if not source_res:
                set_obj.states_obj.write_states()
                raise RuntimeError

            continue

        set_obj.states_obj.take_state(img_name, source_res)

        card_obj.message(total_progress, set_obj.set_progress())

    set_obj.states_obj.write_states()


def pull_all() -> None:

    set_obj: SetObject
    set_entries: dict[str, dict[str, Any]]

    pull_meta()

    set_entries = json.loads(paths.BULK_PATH.read_bytes())["data"]

    set_count: int = 0
    set_total: int = len(set_entries)

    for set_entry in set_entries.values():

        set_count += 1
        set_obj = SetObject(set_entry)

        if set_obj.to_omit:
            continue

        total_progress: str = utils.progress_str(set_count, set_total, False)

        pull_set(set_obj, total_progress)

    utils.status("Finished successfully.", 0)

    remaining_sets(set_entries)


def main() -> None:

    pull_all()


if __name__ == "__main__":
    main()
