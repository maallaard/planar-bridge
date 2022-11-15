from os import getenv
from pathlib import Path
from sys import platform


def _default_path() -> Path:

    path_env: str | None = getenv("PLANAR_BRIDGE_DIR")

    fallback_env = "XDG_DATA_HOME"
    fallback_dir = "~/.local/share"

    if platform.startswith(("win32", "cygwin")):
        fallback_env = "%AppData%"
        fallback_dir = "%UserProfile%/AppData"

    if path_env is None:
        path_env = getenv(fallback_env, fallback_dir)
        path_env += ("/" if not path_env.endswith("/") else "") + "planar-bridge"

    path_obj: Path = Path(path_env)

    if not path_obj.exists():
        raise FileNotFoundError(path_obj)

    return path_obj


REPO_DIR: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = _default_path().resolve()

JSON_DIR: Path = DATA_DIR / ".json"
JSON_DIR.mkdir(exist_ok=True)

BULK_PATH: Path = JSON_DIR / "AllPrintings.json"
META_PATH: Path = JSON_DIR / "Meta.json"
