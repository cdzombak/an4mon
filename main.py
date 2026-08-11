import argparse
import asyncio
import logging
import multiprocessing
import sys
import traceback

import lib_mpex
from aranet import ara_scan
from config import Config
from log import LOG_DEFAULT_FMT
from ntfy import Notifier
from poller import Poller


def main():
    parser = argparse.ArgumentParser(
        prog="an4mon",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Run the given JSON configuration file",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--scan",
        help="Scan for Aranet4 devices",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--print",
        help="Print readings from the configured device to stdout",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--debug",
        help="Print debug-level logs (to stderr)",
        required=False,
        action="store_true",
    )
    args = parser.parse_args()

    logger = logging.getLogger("main")
    ll = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=ll, format=LOG_DEFAULT_FMT)

    if sys.version_info < (3, 12):
        logger.error("Python 3.12 or newer is required.")
        sys.exit(1)

    if args.scan and args.config:
        print("--scan and --config are mutually exclusive")
        sys.exit(1)
    elif not args.scan and not args.config:
        print("either --scan or --config is required")
        sys.exit(1)

    if args.scan:
        with asyncio.Runner() as scan_runner:
            ara_scan(scan_runner)
            sys.exit(0)

    cfg = Config.from_file(args.config)
    if not cfg.influx and not cfg.notify and not cfg.mqtt and not args.print:
        print(
            "config's 'influx', 'notify', and 'mqtt' keys are all False, "
            "and --print was not given; nothing to do!"
        )
        sys.exit(1)

    exit_queue = multiprocessing.Queue()
    procs = []

    ntfy_queue = None
    if cfg.notify:
        ntfy_queue = multiprocessing.Queue()
        notifier = Notifier(cfg, ntfy_queue, log_level=ll)
        procs.append(multiprocessing.Process(target=notifier.run, args=(exit_queue,)))
    poller = Poller(cfg, ntfy_queue, log_level=ll, print_readings=args.print)
    procs.append(multiprocessing.Process(target=poller.run, args=(exit_queue,)))

    def my_exit(error: bool):
        logger.debug(f"exiting ({'success' if not error else 'with error'}) ...")
        for p in procs:
            p.terminate()
        sys.exit(1 if error else 0)

    logger.info("starting child processes ...")
    for p in procs:
        p.start()

    while any(p.is_alive() for p in procs):
        e: lib_mpex.ChildExit = exit_queue.get()
        if e.is_exc():
            logger.error(f"{e.exc_info[0]} {e.exc_info[1]}")
            logger.error(f"Error in {e.class_name} (pid {e.pid}): {e.error}")
            traceback.print_exception(*e.exc_info)
            my_exit(True)
        else:
            logger.info(f"{e.class_name} (pid {e.pid}) exited: {e.error}")
            my_exit(False)

    for p in procs:
        p.join()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
