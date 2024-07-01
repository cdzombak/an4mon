import datetime
import json
from dataclasses import dataclass

import requests
from claranet4.lib import Reading

from co2 import Co2WarningLevel
from config import Config


@dataclass
class NtfyState:
    last_notification_level: Co2WarningLevel
    last_time: datetime.datetime

    @staticmethod
    def from_file(file_path: str) -> "NtfyState":
        with open(file_path, "r") as f:
            return NtfyState.from_dict(json.load(f))

    @staticmethod
    def from_dict(data: dict) -> "NtfyState":
        return NtfyState(
            last_notification_level=Co2WarningLevel.from_str(
                data.get("last_notification_level", Co2WarningLevel.GREEN.value)
            ),
            last_time=datetime.datetime.fromisoformat(
                data.get("last_time", "1970-01-01T00:00:00")
            ),
        )

    def to_dict(self) -> dict:
        return {
            "last_notification_level": self.last_notification_level.value,
            "last_time": self.last_time.isoformat(),
        }

    def to_file(self, file_path: str):
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f)


def do_notification(cfg: Config, reading: Reading, now: datetime.datetime):
    try:
        state = NtfyState.from_file(cfg.state_file)
    except FileNotFoundError:
        state = NtfyState(
            last_notification_level=Co2WarningLevel.GREEN,
            last_time=datetime.datetime.min,
        )
    warning_level = Co2WarningLevel.from_ppm(cfg, reading.co2)
    send_notification = False

    if warning_level == Co2WarningLevel.RED:
        if state.last_notification_level != Co2WarningLevel.RED:
            send_notification = True
        elif state.last_time + datetime.timedelta(minutes=cfg.notify_red_every) < now:
            send_notification = True
    elif warning_level == Co2WarningLevel.YELLOW:
        if state.last_notification_level == Co2WarningLevel.GREEN:
            send_notification = True
        elif (
            state.last_time + datetime.timedelta(minutes=cfg.notify_yellow_every) < now
        ):
            send_notification = True

    if not send_notification:
        return

    headers = {
        "Tags": warning_level.ntfy_tag(),
    }
    if cfg.ntfy_token:
        headers["Authorization"] = "Bearer " + cfg.ntfy_token

    requests.post(
        f"{cfg.ntfy_server}/{cfg.ntfy_topic}",
        data=f"{cfg.notify_room_name}: CO2 {reading.co2} ppm".encode("utf-8"),
        headers=headers,
    )

    state.last_notification_level = warning_level
    state.last_time = now
    state.to_file(cfg.state_file)
