from time import strftime
from colorama import Fore


def status(msg: str, lvl: int) -> None:

    prefix: str

    match lvl:
        case 0: prefix = Fore.CYAN    + "INFO"
        case 1: prefix = Fore.RED     + "WARNING"
        case 2: prefix = Fore.GREEN   + "SET (load)"
        case 3: prefix = Fore.YELLOW  + "SET (skip)"
        case 4: prefix = Fore.MAGENTA + "NEW CARD"
        case 5: prefix = Fore.BLUE    + "ENHANCED"
        case _: raise ValueError(lvl)

    prefix += Fore.RESET + ':'
    timestamp = '[' + Fore.CYAN + strftime("%H:%M:%S") + Fore.RESET + ']'

    for line in msg.splitlines():
        print(timestamp, prefix, line)


def boolify_str(bool_str: str, default: bool | None = None) -> bool:

    if not bool_str and default is not None:
        return default

    bool_str = bool_str.strip().lower()[:1]

    if bool_str in ['y', 't', '1']:
        return True
    if bool_str in ['n', 'f', '0']:
        return False

    raise ValueError(
        f"Input '{bool_str}' does not resemble a boolean value: y/n, t/f, 1/0"
    )
