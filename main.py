import argparse
import datetime
import sys

import requests

from aranet import ara_print, ara_read, ara_scan
from config import Config
from influx import write_influx
from ntfy import do_notification

if __name__ == "__main__":
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
    args = parser.parse_args()

    if args.scan and args.config:
        print("--scan and --config are mutually exclusive")
        sys.exit(1)
    elif not args.scan and not args.config:
        print("either --scan or --config is required")
        sys.exit(1)

    if args.scan:
        ara_scan()
        sys.exit(0)

    cfg = Config.from_file(args.config)
    if not cfg.influx and not cfg.notify and not args.print:
        print(
            "config's 'influx' and 'notify' keys are both False, and --print was not given; nothing to do!"
        )
        sys.exit(1)

    now = datetime.datetime.now(datetime.UTC)
    reading = ara_read(cfg.aranet_device_address)
    healthy = True
    if args.print:
        ara_print(cfg, reading)
    if cfg.notify:
        do_notification(cfg, reading, now)
    if cfg.influx:
        healthy = write_influx(cfg, reading, now)
    if healthy and cfg.healthcheck_ping_url:
        requests.get(cfg.healthcheck_ping_url)
