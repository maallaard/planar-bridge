from typing import Any
import json
import signal
import sys

import objects
import paths
import utils


if sys.version_info.major != 3 or sys.version_info.minor < 11:
    raise SystemExit("Python version must be at least 3.11")


# pylint: disable=unused-argument
def handler(signal_recieved, frame):

    print("\nSIGINT recieved (Ctrl-C), exiting...")
    sys.exit(1)


def main() -> None:

    signal.signal(signal.SIGINT, handler)

    utils.status("comparing local & source files...", 0)

    fetcher = objects.FetcherObject()
    is_outdated: bool | None = fetcher.outdated()

    if is_outdated is None:
        return

    if is_outdated:
        utils.status("downloading bulk files...", 0)
        fetcher.pull_bulk()

    utils.status(f"loading bulk data ({fetcher.date})...", 0)
    bulk: dict[str, Any] = json.loads(paths.BULK_PATH.read_bytes())

    for set_obj in bulk["data"].values():
        set_obj = objects.SetObject(set_obj)

        if set_obj.to_omit:
            continue

        set_obj.pull()

    utils.status("finished successfully.", 0)


if __name__ == "__main__":
    main()
