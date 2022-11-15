import time


def timestamp() -> str:
    return "[" + time.strftime("%H:%M:%S") + "]"


def boolify_input(bool_str: str, default: bool = ...) -> bool:

    if not bool_str and default is not ...:
        return default

    bool_str = bool_str.strip().lower()[:1]

    if bool_str in ["y", "t", "1"]:
        return True
    if bool_str in ["n", "f", "0"]:
        return False

    raise ValueError(
        "Invalid string, must resemble a boolean value (i.e. y/n, t/f, 1/0)."
    )
