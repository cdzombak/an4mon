import datetime
import logging
import multiprocessing
from dataclasses import dataclass
from multiprocessing.managers import Namespace
from typing import Final, Optional

import requests

import lib_mpex
from co2 import Co2WarningLevel
from config import Config
from log import LOG_DEFAULT_FMT

NTFY_TIMEOUT_S: Final = 10.0
NTFY_PRIORITY_MUTED: Final = "min"
NTFY_PRIORITY_UNMUTED: Final = "default"


@dataclass(frozen=True)
class ReadingEvent:
    co2: int
    t: datetime.datetime


@dataclass(frozen=True)
class MuteEvent:
    mute_seconds: int  # 0 = unmuted


def fmt_duration(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60}m"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if minutes == 0:
        return f"{hours}h"
    return f"{hours}h {minutes}m"


def mute_action(label: str, seconds: int, base_url: str) -> str:
    return (
        f"http, {label}, {base_url}/mute, "
        f"body='{{\"s\": {seconds}}}', "
        "headers.content-type=application/json, clear=true"
    )


def should_notify(
    cfg: Config,
    last_level: Co2WarningLevel,
    last_time: datetime.datetime,
    level: Co2WarningLevel,
    now: datetime.datetime,
    mute_until: Optional[datetime.datetime] = None,
) -> bool:
    if level == Co2WarningLevel.RED:
        if last_level != Co2WarningLevel.RED:
            # escalation to red always notifies, even while muted:
            return True
        notify = last_time + datetime.timedelta(minutes=cfg.notify_red_every) < now
    elif level == Co2WarningLevel.YELLOW:
        if last_level == Co2WarningLevel.GREEN:
            notify = True
        else:
            notify = (
                last_time + datetime.timedelta(minutes=cfg.notify_yellow_every) < now
            )
    else:
        return False

    if notify and mute_until is not None and now < mute_until:
        return False
    return notify


class Notifier(lib_mpex.ChildProcess):
    def __init__(
        self,
        config: Config,
        input_queue: multiprocessing.Queue,  # of ReadingEvent | MuteEvent
        log_level: int,
        mute_ns: Optional[Namespace] = None,
    ):
        self._config = config
        self._input_queue = input_queue
        self._log_level = log_level
        self._mute_ns = mute_ns
        self._last_level = Co2WarningLevel.GREEN
        self._last_time = datetime.datetime.min.replace(tzinfo=datetime.UTC)

    def _run(self):
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=self._log_level, format=LOG_DEFAULT_FMT)
        logger.info("starting notifier")

        while True:
            ev: ReadingEvent | MuteEvent = self._input_queue.get()
            if isinstance(ev, MuteEvent):
                self._handle_mute(logger, ev)
            else:
                self._handle_reading(logger, ev)

    def _handle_reading(self, logger: logging.Logger, ev: ReadingEvent):
        level = Co2WarningLevel.from_ppm(self._config, ev.co2)
        logger.debug(f"received reading: {ev.co2} ppm ({level.value})")

        mute_until = self._mute_ns.mute_until if self._mute_ns is not None else None
        if not should_notify(
            self._config, self._last_level, self._last_time, level, ev.t, mute_until
        ):
            if (
                mute_until is not None
                and ev.t < mute_until
                and should_notify(
                    self._config, self._last_level, self._last_time, level, ev.t
                )
            ):
                logger.info(
                    f"CO2 {level.value} notification suppressed; "
                    f"muted until {mute_until}"
                )
            return

        headers = {
            "Tags": level.ntfy_tag(),
            "Priority": (
                self._config.ntfy_priority_red
                if level == Co2WarningLevel.RED
                else self._config.ntfy_priority_yellow
            ),
        }
        if self._config.web_external_base_url:
            headers["Actions"] = "; ".join(
                mute_action(
                    f"Mute {hours}h", hours * 3600, self._config.web_external_base_url
                )
                for hours in (self._config.mute_short_h, self._config.mute_long_h)
            )

        message = f"{self._config.notify_room_name}: CO2 {ev.co2} ppm"
        if not self._send(logger, message, headers):
            return

        self._last_level = level
        self._last_time = ev.t

    def _handle_mute(self, logger: logging.Logger, ev: MuteEvent):
        if ev.mute_seconds > 0:
            message = f"Notifications muted for {fmt_duration(ev.mute_seconds)}."
            headers = {"Tags": "mute", "Priority": NTFY_PRIORITY_MUTED}
            if self._config.web_external_base_url:
                headers["Actions"] = mute_action(
                    "Unmute", 0, self._config.web_external_base_url
                )
        else:
            message = "Notifications unmuted."
            headers = {"Tags": "loud_sound", "Priority": NTFY_PRIORITY_UNMUTED}
        self._send(logger, message, headers)

    def _send(
        self, logger: logging.Logger, message: str, headers: dict[str, str]
    ) -> bool:
        if self._config.ntfy_token:
            headers["Authorization"] = "Bearer " + self._config.ntfy_token
        try:
            resp = requests.post(
                f"{self._config.ntfy_server}/{self._config.ntfy_topic}",
                data=message.encode("utf-8"),
                headers=headers,
                timeout=NTFY_TIMEOUT_S,
            )
            resp.raise_for_status()
            logger.info(f"notification '{message}' sent")
            return True
        except requests.RequestException as e:
            logger.error(f"error sending notification: {e}")
            return False
