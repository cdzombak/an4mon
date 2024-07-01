import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


class ConfigValidationError(ValueError):
    pass


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
    state_file: Optional[str]
    influx_bucket: Optional[str]
    influx_host: Optional[str]
    influx_port: int
    influx_username: Optional[str]
    influx_password: Optional[str]
    influx_measurement_name: Optional[str]
    influx_nametag: str

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
            notify_room_name=data.get("notify_room_name"),
            state_file=data.get("state_file"),
            influx_bucket=data.get("influx_bucket"),
            influx_host=data.get("influx_host"),
            influx_port=data.get("influx_port", 8086),
            influx_username=data.get("influx_username"),
            influx_password=data.get("influx_password"),
            influx_measurement_name=data.get("influx_measurement_name"),
            influx_nametag=data.get("influx_nametag", ""),
        )
        result.validate()
        if result.ntfy_server.endswith("/"):
            result.ntfy_server = result.ntfy_server[:-1]
        return result

    def validate(self):
        if not self.aranet_device_address or not isinstance(
            self.aranet_device_address, str
        ):
            raise ConfigValidationError("aranet_device_address is required")
        self._validate_ntfy()
        self._validate_influx()

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
        if not self.state_file or not isinstance(self.state_file, str):
            raise ConfigValidationError(
                "state_file is required for notification support"
            )
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

    def _validate_influx(self):
        if not self.influx:
            return
        if not self.influx_bucket or not isinstance(self.influx_bucket, str):
            raise ConfigValidationError("influx_bucket is required")
        if not self.influx_host or not isinstance(self.influx_host, str):
            raise ConfigValidationError("influx_server is required")
        if not isinstance(self.influx_port, int):
            raise ConfigValidationError("influx_port must be an integer")
        if self.influx_username and not isinstance(self.influx_username, str):
            raise ConfigValidationError("influx_username must be a string")
        if self.influx_password and not isinstance(self.influx_password, str):
            raise ConfigValidationError("influx_password must be a string")
        if not self.influx_measurement_name or not isinstance(
            self.influx_measurement_name, str
        ):
            raise ConfigValidationError("influx_measurement_name must be a string")
        if not isinstance(self.influx_nametag, str):
            raise ConfigValidationError("influx_nametag must be a string")
