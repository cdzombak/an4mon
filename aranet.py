import logging

from claranet4.lib import discover_ara4s, read, Reading

import co2
import conv
from config import Config


def ara_scan():
    # work around https://github.com/bede/claranet4/issues/2 :
    logging.captureWarnings(True)
    # suppress default INFO-level messages from claranet4:
    logging.getLogger().setLevel(logging.ERROR)

    for ara4 in discover_ara4s():
        print(f"{ara4.name} ({ara4.rssi} dBm)")
        print(f"\t{ara4.address}")
        print("")


def ara_read(addr: str) -> Reading:
    # work around https://github.com/bede/claranet4/issues/2 :
    logging.captureWarnings(True)
    # suppress default INFO-level messages from claranet4:
    logging.getLogger().setLevel(logging.ERROR)

    return read(addr)


def ara_print(cfg: Config, r: Reading):
    print(f"{r.name} ({r.rssi} dBm)")
    print(f"co2: {r.co2} ppm {co2.Co2WarningLevel.from_ppm(cfg, r.co2).emoji()}")
    print(
        f"temperature: {r.temperature:.1f} °C ({conv.celsius_to_fahrenheit(r.temperature):.1f} °F)"
    )
    print(f"pressure: {r.pressure} mbar ({conv.mbar_to_inhg(r.pressure):.2f} inHg)")
    print(f"humidity: {r.humidity} %")
