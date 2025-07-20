import datetime
import json

import paho.mqtt.publish as publish

from claranet4.lib import Reading
from co2 import Co2WarningLevel
from config import Config
import conv
from eprint import eprint


def write_mqtt(cfg: Config, reading: Reading, now: datetime.datetime) -> bool:
    try:
        auth = None
        if cfg.mqtt_username:
            auth = {
                "username": cfg.mqtt_username,
                "password": cfg.mqtt_password,
            }

        publish.single(
            cfg.mqtt_topic,
            payload=json.dumps(
                {
                    "tags": {
                        "aranet_name": cfg.device_name,
                        "aranet_addr": cfg.aranet_device_address,
                    },
                    "time": now.isoformat(),
                    "fields": {
                        "rssi": int(reading.rssi),
                        "temp_c": float(reading.temperature),
                        "temp_f": float(
                            conv.celsius_to_fahrenheit(reading.temperature)
                        ),
                        "humidity_pct": float(reading.humidity),
                        "humidity_abs": float(
                            conv.absolute_humidity_g_m3(
                                reading.temperature, reading.humidity
                            )
                        ),
                        "pressure_mbar": float(reading.pressure),
                        "pressure_inHg": float(conv.mbar_to_inhg(reading.pressure)),
                        "co2_ppm": int(reading.co2),
                        "co2_warning_level": Co2WarningLevel.from_ppm(
                            cfg, reading.co2
                        ).value,
                    },
                }
            ),
            hostname=cfg.mqtt_broker,
            port=cfg.mqtt_port,
            auth=auth,
        )
        return True
    except Exception as e:
        eprint(
            f"{datetime.datetime.now()}: failed publishing to MQTT '{cfg.mqtt_broker}'"
            f": {e}"
        )
        return False
