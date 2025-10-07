import sys

from pull import pull_all


if sys.version_info.major != 3 or sys.version_info.minor < 13:
    raise SystemExit("Python version must be at least 3.13")


def main() -> None:

    pull_all()


if __name__ == "__main__":
    main()
