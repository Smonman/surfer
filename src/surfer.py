import argparse
import logging
import logging.config
import pathlib

import epaper
from PIL import Image

logging.config.fileConfig("src/logging.conf")
LOGGER = logging.getLogger()


def setup_logger(args: dict) -> None:
    if args.verbose:
        LOGGER.setLevel(logging.INFO)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)


def display_new_image(epd: any, path: pathlib.Path) -> None:
    LOGGER.debug(f"displaying image {path}")
    try:
        epd.init()
        img = Image.open(path)
        draw_image(img)
    except Exception as e:
        LOGGER.error(f"could not display image {path}", e)
    finally:
        epd.sleep()


def draw_image(epd: any, image: Image) -> None:
    LOGGER.debug("drawing image")
    epd.display(Image)


def get_epaper_module(specifier: str) -> any:
    LOGGER.debug(f"trying to get epaper module for {specifier}")
    try:
        return epaper.epaper("epd7in5").EPD()
    except Exception as e:
        LOGGER.error(f"cannot get epaper module for {specifier}", e)
        raise ValueError(f"module {specifier} not found", e)


def start(epd: any, args: dict) -> None:
    if args.image:
        display_new_image(epd, args.image)
    elif args.watch_directory:
        raise NotImplementedError()


def main(args: dict) -> None:
    LOGGER.debug(args)
    epd = None
    try:
        epd = get_epaper_module("epd7in5")
        start(epd, args)
    except KeyboardInterrupt:
        LOGGER.info("interrupted")
    except Exception as e:
        LOGGER.error(e)
    finally:
        LOGGER.info("quitting")
        if epd:
            epd.Clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send images to a waveshare e-ink display.")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("image", type=pathlib.Path, nargs="?", help="Image to display")
    input_group.add_argument("-w", "--watch-directory", type=pathlib.Path, help="watch directory and display lates changes")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show more log output")
    parser.add_argument("-e", "--debug", action="store_true", default=False, help="show debug log messages")
    args = parser.parse_args()
    setup_logger(args)
    main(args)
