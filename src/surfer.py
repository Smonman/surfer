import argparse
import logging
import logging.config
import pathlib

logging.config.fileConfig("src/logging.conf")
LOGGER = logging.getLogger()


def setup_logger(args: dict) -> None:
    if args.verbose:
        LOGGER.setLevel(logging.INFO)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)


def main(args: dict) -> None:
    LOGGER.debug(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send images to a waveshare e-ink display.")
    parser.add_argument("image", type=pathlib.Path, nargs="?", help="Image to display")
    parser.add_argument("-w", "--watch-directory", type=pathlib.Path, help="watch directory and display lates changes")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show more log output")
    parser.add_argument("-e", "--debug", action="store_true", default=False, help="show debug log messages")
    args = parser.parse_args()
    setup_logger(args)
    main(args)