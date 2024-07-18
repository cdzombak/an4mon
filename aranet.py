import asyncio
import logging
import math

from libclaranet4 import scan_ara4s, read_ara4, Reading

import co2
import conv
from config import Config


def ara_scan(runner: asyncio.Runner):
    # work around https://github.com/bede/claranet4/issues/2 :
    logging.captureWarnings(True)
    logging.getLogger().setLevel(logging.ERROR)

    for ara4 in scan_ara4s(runner):
        print(f"{ara4.name} ({ara4.rssi} dBm)")
        print(f"\t{ara4.address}")
        print("")


def ara_read(runner: asyncio.Runner, addr: str) -> Reading:
    # work around https://github.com/bede/claranet4/issues/2 :
    logging.captureWarnings(True)
    logging.getLogger().setLevel(logging.ERROR)

    result = read_ara4(runner, addr)
    # I _always_ get humidity readings of X.3%,
    # where Aranet displays X% (with no decimal):
    result.humidity = float(int(result.humidity))

    return result


def ara_print(cfg: Config, r: Reading):
    print(f"{r.name} ({r.rssi} dBm)")
    print(f"co2: {r.co2} ppm {co2.Co2WarningLevel.from_ppm(cfg, r.co2).emoji()}")
    print(
        f"temperature: {r.temperature:.1f} °C ({conv.celsius_to_fahrenheit(r.temperature):.1f} °F)"
    )
    print(f"pressure: {r.pressure} mbar ({conv.mbar_to_inhg(r.pressure):.2f} inHg)")
    print(f"humidity: {r.humidity} %")
