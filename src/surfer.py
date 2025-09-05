import argparse
import logging
import logging.config
import pathlib
import time
import datetime

import epaper
from PIL import Image
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logging.config.fileConfig("src/logging.conf")
LOGGER = logging.getLogger()

WATCHDOG_INTERVAL = 5
MAX_PARTIAL_REFRESH = 10

partial_refresh_counter = 0


def setup_logger(args: dict) -> None:
    if args.verbose:
        LOGGER.setLevel(logging.INFO)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)


def may_partial_draw() -> bool:
    return partial_refresh_counter < MAX_PARTIAL_REFRESH


def clear_partial_refresh_counter() -> None:
    LOGGER.debug("clearing partial refresh counter")
    global partial_refresh_counter
    partial_refresh_counter = 0


def increment_partial_refresh_counter() -> None:
    LOGGER.debug("incrementing partial refresh counter")
    global partial_refresh_counter
    partial_refresh_counter += 1


class FileChangeHandler(FileSystemEventHandler):
    
    def __init__(self, epd: any) -> None:
        self.last_modified = datetime.datetime.now()
        self.epd = epd


    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        if not isinstance(event, FileModifiedEvent):
            return
        if datetime.datetime.now() - self.last_modified < datetime.timedelta(seconds=WATCHDOG_INTERVAL):
            return
        LOGGER.info(f"directory {event.src_path} was modified")
        self.last_modified = datetime.datetime.now()
        display_new_image(self.epd, event.src_path, True)


def get_watchdog_path(path: pathlib.Path) -> pathlib.Path:
    if path.is_file():
        LOGGER.warning(f"watchdog path {path} is pointing to a file, using parent directory")
        return path.parents[0]
    return path


def run_watchdog(observer: Observer) -> None:
    LOGGER.debug("watchdog observer is running...")
    try:
        while True:
            time.sleep(WATCHDOG_INTERVAL)
    except KeyboardInterrupt:
        LOGGER.info("interrupted watchdog")
    finally:
        LOGGER.info("terminating watchdog observer")
        observer.stop()
        observer.join()


def start_watchdog(epd: any, path: pathlib.Path) -> None:
    LOGGER.debug(f"starting watchdog on path {path}")
    event_handler = FileChangeHandler(epd)
    observer = Observer()
    observer.schedule(event_handler, path=get_watchdog_path(path), recursive=False)
    observer.start()
    run_watchdog(observer)


def display_new_image(epd: any, path: pathlib.Path, try_partial: bool = False) -> None:
    LOGGER.debug(f"trying to displaying image {path}")
    if not try_partial or not may_partial_draw():
        display_image(epd, path)
    else:
        display_image_partial(epd, path)


def display_image(epd: any, path: pathlib.Path) -> None:
    LOGGER.debug(f"displaying image {path}")
    try:
        epd.init()
        img = Image.open(path)
        draw_image(epd, img)
    except Exception as e:
        LOGGER.exception(f"could not display image {path}")
    finally:
        epd.sleep()


def draw_image(epd: any, image: Image) -> None:
    LOGGER.debug("drawing image")
    buffer = epd.getbuffer(image)
    epd.display(buffer)
    clear_partial_refresh_counter()


def display_image_partial(epd: any, path: pathlib.Path) -> None:
    LOGGER.debug(f"displaying image partial {path}")
    try:
        epd.init_part()
        img = Image.open(path)
        draw_image_partial(epd, img)
    except Exception as e:
        LOGGER.exception(f"could not display image {path}")
    finally:
        epd.sleep()


def draw_image_partial(epd: any, image: Image) -> None:
    LOGGER.debug("drawing image parial")
    buffer = epd.getbuffer(image)
    epd.display_Partial(buffer, 0, 0, epd.width, epd.height)
    increment_partial_refresh_counter()


def get_epaper_module(specifier: str) -> any:
    LOGGER.debug(f"trying to get epaper module for {specifier}")
    try:
        return epaper.epaper(specifier).EPD()
    except Exception as e:
        LOGGER.exception(f"cannot get epaper module for {specifier}")
        raise ValueError(f"module {specifier} not found", e)


def start(epd: any, args: dict) -> None:
    LOGGER.debug(f"start displaying")
    if args.image:
        display_new_image(epd, args.image)
    elif args.watch_directory:
        start_watchdog(epd, args.watch_directory)


def quit(epd: any) -> None:
    try:
        epd.init()
        epd.Clear()
        epd.sleep()
    except KeyboardInterrupt:
        epd.epdconfig.module_exit(cleanup=True)


def main(args: dict) -> None:
    LOGGER.debug(args)
    epd = None
    try:
        epd = get_epaper_module(args.display)
        LOGGER.debug("successfully got epaper module")
        start(epd, args)
    except KeyboardInterrupt:
        LOGGER.info("interrupted")
    except Exception as e:
        LOGGER.error(e)
    finally:
        LOGGER.info("quitting")
        if epd:
            quit(epd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send images to a waveshare e-ink display.")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("image", type=pathlib.Path, nargs="?", help="Image to display")
    input_group.add_argument("-w", "--watch-directory", type=pathlib.Path, help="watch directory and display lates changes")
    parser.add_argument("-d", "--display", type=str, default="epd7in5_V2", help="waveshare display model specifier")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="show more log output")
    parser.add_argument("-e", "--debug", action="store_true", default=False, help="show debug log messages")
    args = parser.parse_args()
    setup_logger(args)
    main(args)
