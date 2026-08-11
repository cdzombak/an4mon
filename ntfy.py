import datetime
import logging
import multiprocessing
from dataclasses import dataclass
from typing import Final

import requests

import lib_mpex
from co2 import Co2WarningLevel
from config import Config
from log import LOG_DEFAULT_FMT

NTFY_TIMEOUT_S: Final = 10.0


@dataclass(frozen=True)
class ReadingEvent:
    co2: int
    t: datetime.datetime


def should_notify(
    cfg: Config,
    last_level: Co2WarningLevel,
    last_time: datetime.datetime,
    level: Co2WarningLevel,
    now: datetime.datetime,
) -> bool:
    if level == Co2WarningLevel.RED:
        if last_level != Co2WarningLevel.RED:
            return True
        return last_time + datetime.timedelta(minutes=cfg.notify_red_every) < now
    elif level == Co2WarningLevel.YELLOW:
        if last_level == Co2WarningLevel.GREEN:
            return True
        return last_time + datetime.timedelta(minutes=cfg.notify_yellow_every) < now
    return False


class Notifier(lib_mpex.ChildProcess):
    def __init__(
        self,
        config: Config,
        input_queue: multiprocessing.Queue,  # of ReadingEvent
        log_level: int,
    ):
        self._config = config
        self._input_queue = input_queue
        self._log_level = log_level
        self._last_level = Co2WarningLevel.GREEN
        self._last_time = datetime.datetime.min.replace(tzinfo=datetime.UTC)

    def _run(self):
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=self._log_level, format=LOG_DEFAULT_FMT)
        logger.info("starting notifier")

        while True:
            ev: ReadingEvent = self._input_queue.get()
            level = Co2WarningLevel.from_ppm(self._config, ev.co2)
            logger.debug(f"received reading: {ev.co2} ppm ({level.value})")

            if not should_notify(
                self._config, self._last_level, self._last_time, level, ev.t
            ):
                continue

            headers = {
                "Tags": level.ntfy_tag(),
                "Priority": (
                    self._config.ntfy_priority_red
                    if level == Co2WarningLevel.RED
                    else self._config.ntfy_priority_yellow
                ),
            }
            if self._config.ntfy_token:
                headers["Authorization"] = "Bearer " + self._config.ntfy_token

            message = f"{self._config.notify_room_name}: CO2 {ev.co2} ppm"
            try:
                resp = requests.post(
                    f"{self._config.ntfy_server}/{self._config.ntfy_topic}",
                    data=message.encode("utf-8"),
                    headers=headers,
                    timeout=NTFY_TIMEOUT_S,
                )
                resp.raise_for_status()
                logger.info(f"notification '{message}' sent")
            except requests.RequestException as e:
                logger.error(f"error sending notification: {e}")
                continue

            self._last_level = level
            self._last_time = ev.t
