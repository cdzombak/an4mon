import datetime

from claranet4.lib import Reading
from influxdb import InfluxDBClient

import conv
from co2 import Co2WarningLevel
from config import Config


def write_influx(cfg: Config, reading: Reading, now: datetime.datetime) -> bool:
    if cfg.influx_username:
        client = InfluxDBClient(
            host=cfg.influx_host,
            port=cfg.influx_port,
            username=cfg.influx_username,
            password=cfg.influx_password,
        )
    else:
        client = InfluxDBClient(
            host=cfg.influx_host,
            port=cfg.influx_port,
        )

    ret_pol = None
    parts = cfg.influx_bucket.split("/")
    if len(parts) == 1:
        db = parts[0]
    elif len(parts) == 2:
        db = parts[0]
        ret_pol = parts[1]
    else:
        raise ValueError(f"could not split into db/rp: {cfg.influx_bucket}")

    return client.write_points(
        [
            {
                "measurement": cfg.influx_measurement_name,
                "tags": {
                    "aranet_name": cfg.device_name,
                    "aranet_addr": cfg.aranet_device_address,
                },
                "time": now.isoformat(),
                "fields": {
                    "rssi": int(reading.rssi),
                    "temp_c": float(reading.temperature),
                    "temp_f": float(conv.celsius_to_fahrenheit(reading.temperature)),
                    "humidity_pct": float(reading.humidity),
                    "humidity_abs": float(conv.absolute_humidity_g_m3(reading.temperature, reading.humidity)),
                    "pressure_mbar": float(reading.pressure),
                    "pressure_inHg": float(conv.mbar_to_inhg(reading.pressure)),
                    "co2_ppm": int(reading.co2),
                    "co2_warning_level": Co2WarningLevel.from_ppm(
                        cfg, reading.co2
                    ).value,
                },
            },
        ],
        database=db,
        retention_policy=ret_pol,
    )
