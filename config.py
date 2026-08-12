import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


class ConfigValidationError(ValueError):
    pass


def _is_int(value) -> bool:
    # bool is a subclass of int, but is not a meaningful number:
    return isinstance(value, int) and not isinstance(value, bool)


class NtfyPriority(Enum):
    """copied from https://github.com/cdzombak/driveway-monitor/blob/main/ntfy.py ;
    used for config validation only"""

    N_1 = "1"
    MIN = "min"
    N_2 = "2"
    LOW = "low"
    N_3 = "3"
    DEFAULT = "default"
    N_4 = "4"
    HIGH = "high"
    N_5 = "5"
    MAX = "max"
    URGENT = "urgent"

    @staticmethod
    def all_values() -> Set[str]:
        return {e.value for e in NtfyPriority}


@dataclass
class Config:
    aranet_device_address: str
    notify: bool
    influx: bool
    mqtt: bool
    healthcheck_ping_url: Optional[str]
    ntfy_server: str
    ntfy_token: Optional[str]
    ntfy_topic: Optional[str]
    notify_room_name: Optional[str]
    notify_yellow_every: int
    notify_red_every: int
    co2_yellow: int
    co2_red: int
    ntfy_priority_yellow: str
    ntfy_priority_red: str
    mute_short_h: int
    mute_long_h: int
    web_external_base_url: Optional[str]
    web_port: int
    web_bind_to: str
    poll_interval: int
    influx_bucket: Optional[str]
    influx_host: Optional[str]
    influx_port: int
    influx_username: Optional[str]
    influx_password: Optional[str]
    influx_measurement_name: Optional[str]
    device_name: str
    mqtt_broker: Optional[str]
    mqtt_port: int
    mqtt_username: Optional[str]
    mqtt_password: Optional[str]
    mqtt_topic: Optional[str]

    @staticmethod
    def from_file(file_path: str) -> "Config":
        with open(file_path, "r") as f:
            return Config.from_dict(json.load(f))

    @staticmethod
    def from_dict(data: dict) -> "Config":
        result = Config(
            aranet_device_address=data.get("aranet_device_address"),
            notify=data.get("notify", False),
            influx=data.get("influx", False),
            mqtt=data.get("mqtt", False),
            healthcheck_ping_url=data.get("healthcheck_ping_url"),
            ntfy_server=data.get("ntfy_server", "https://ntfy.sh"),
            ntfy_token=data.get("ntfy_token"),
            ntfy_topic=data.get("ntfy_topic"),
            notify_yellow_every=data.get("notify_yellow_every", 30),
            notify_red_every=data.get("notify_red_every", 5),
            co2_yellow=data.get("co2_yellow", 1000),
            co2_red=data.get("co2_red", 1400),
            ntfy_priority_yellow=data.get("ntfy_priority_yellow", "3"),
            ntfy_priority_red=data.get("ntfy_priority_red", "5"),
            mute_short_h=data.get("mute_short_h", 2),
            mute_long_h=data.get("mute_long_h", 6),
            web_external_base_url=data.get("web_external_base_url"),
            web_port=data.get("web_port", 5560),
            web_bind_to=data.get("web_bind_to", "127.0.0.1"),
            notify_room_name=data.get("notify_room_name"),
            poll_interval=data.get("poll_interval", 2),
            influx_bucket=data.get("influx_bucket"),
            influx_host=data.get("influx_host"),
            influx_port=data.get("influx_port", 8086),
            influx_username=data.get("influx_username"),
            influx_password=data.get("influx_password"),
            influx_measurement_name=data.get("influx_measurement_name"),
            device_name=data.get("device_name") or data.get("influx_nametag", ""),
            mqtt_broker=data.get("mqtt_broker"),
            mqtt_port=data.get("mqtt_port", 1883),
            mqtt_username=data.get("mqtt_username"),
            mqtt_password=data.get("mqtt_password"),
            mqtt_topic=data.get("mqtt_topic"),
        )
        result.validate()
        if result.ntfy_server.endswith("/"):
            result.ntfy_server = result.ntfy_server[:-1]
        if result.web_external_base_url and result.web_external_base_url.endswith("/"):
            result.web_external_base_url = result.web_external_base_url[:-1]
        return result

    def validate(self):
        if not self.aranet_device_address or not isinstance(
            self.aranet_device_address, str
        ):
            raise ConfigValidationError("aranet_device_address is required")
        if not self.device_name or not isinstance(self.device_name, str):
            raise ConfigValidationError("device_name is required")
        if not _is_int(self.poll_interval) or self.poll_interval < 1:
            raise ConfigValidationError("poll_interval must be a positive integer")
        self._validate_ntfy()
        self._validate_web()
        self._validate_influx()
        self._validate_mqtt()

    def _validate_ntfy(self):
        if not self.notify:
            return
        if self.ntfy_token and not isinstance(self.ntfy_token, str):
            raise ConfigValidationError("ntfy_token must be a string")
        if not self.ntfy_topic or not isinstance(self.ntfy_topic, str):
            raise ConfigValidationError("ntfy_topic is required")
        if not isinstance(self.ntfy_priority_yellow, str):
            raise ConfigValidationError("ntfy_priority_yellow must be a string")
        if not isinstance(self.ntfy_priority_red, str):
            raise ConfigValidationError("ntfy_priority_red must be a string")
        if self.ntfy_priority_red not in NtfyPriority.all_values():
            raise ConfigValidationError(
                f"ntfy_priority_red must be one of {NtfyPriority.all_values()}"
            )
        if self.ntfy_priority_yellow not in NtfyPriority.all_values():
            raise ConfigValidationError(
                f"ntfy_priority_yellow must be one of {NtfyPriority.all_values()}"
            )
        if not self.notify_room_name or not isinstance(self.notify_room_name, str):
            raise ConfigValidationError("notify_room_name is required")
        if not isinstance(self.ntfy_server, str):
            raise ConfigValidationError("ntfy_server must be a string")
        if not (
            self.ntfy_server.lower().startswith("http://")
            or self.ntfy_server.lower().startswith("https://")
        ):
            raise ConfigValidationError(
                "ntfy_server must start with http:// or https://"
            )

    def _validate_web(self):
        if not self.notify or self.web_external_base_url is None:
            return
        if not isinstance(self.web_external_base_url, str):
            raise ConfigValidationError("web_external_base_url must be a string")
        if not (
            self.web_external_base_url.lower().startswith("http://")
            or self.web_external_base_url.lower().startswith("https://")
        ):
            raise ConfigValidationError(
                "web_external_base_url must start with http:// or https://"
            )
        if self.web_external_base_url.lower().startswith("http://"):
            logging.getLogger(__name__).warning(
                "ntfy actions (e.g. mute buttons) on a non-HTTPS "
                "web_external_base_url will not work with the ntfy web "
                "interface or iOS app; consider using HTTPS"
            )
        if not _is_int(self.mute_short_h) or self.mute_short_h < 1:
            raise ConfigValidationError("mute_short_h must be a positive integer")
        if not _is_int(self.mute_long_h) or self.mute_long_h < 1:
            raise ConfigValidationError("mute_long_h must be a positive integer")
        if not _is_int(self.web_port):
            raise ConfigValidationError("web_port must be an integer")
        if self.web_port <= 0 or self.web_port > 65535:
            raise ConfigValidationError("web_port must be between 1 and 65535")
        if not self.web_bind_to or not isinstance(self.web_bind_to, str):
            raise ConfigValidationError("web_bind_to must be a string")

    def _validate_influx(self):
        if not self.influx:
            return
        if not self.influx_bucket or not isinstance(self.influx_bucket, str):
            raise ConfigValidationError("influx_bucket is required")
        if not self.influx_host or not isinstance(self.influx_host, str):
            raise ConfigValidationError("influx_server is required")
        if not _is_int(self.influx_port):
            raise ConfigValidationError("influx_port must be an integer")
        if self.influx_port <= 0 or self.influx_port > 65535:
            raise ConfigValidationError("influx_port must be between 1 and 65535")
        if (self.influx_username is None) != (self.influx_password is None):
            raise ConfigValidationError(
                "influx_username and influx_password must be both set or both missing"
            )
        if self.influx_username is not None and not isinstance(
            self.influx_username, str
        ):
            raise ConfigValidationError("influx_username must be a string")
        if self.influx_password is not None and not isinstance(
            self.influx_password, str
        ):
            raise ConfigValidationError("influx_password must be a string")
        if not self.influx_measurement_name or not isinstance(
            self.influx_measurement_name, str
        ):
            raise ConfigValidationError("influx_measurement_name must be a string")

    def _validate_mqtt(self):
        if not self.mqtt:
            return
        if not self.mqtt_broker or not isinstance(self.mqtt_broker, str):
            raise ConfigValidationError("mqtt_broker is required")
        if not _is_int(self.mqtt_port):
            raise ConfigValidationError("mqtt_port must be an integer")
        if self.mqtt_port <= 0 or self.mqtt_port > 65535:
            raise ConfigValidationError("mqtt_port must be between 1 and 65535")
        if not self.mqtt_topic or not isinstance(self.mqtt_topic, str):
            raise ConfigValidationError("mqtt_topic is required")
        if (self.mqtt_username is None) != (self.mqtt_password is None):
            raise ConfigValidationError(
                "mqtt_username and mqtt_password must be both set or both missing"
            )
        if self.mqtt_username is not None and not isinstance(self.mqtt_username, str):
            raise ConfigValidationError("mqtt_username must be a string")
        if self.mqtt_password is not None and not isinstance(self.mqtt_password, str):
            raise ConfigValidationError("mqtt_password must be a string")
