import asyncio
import datetime
import logging
import multiprocessing
import time
from multiprocessing.managers import Namespace
from typing import Final, Optional

import requests

import lib_mpex
from aranet import ara_print, ara_read
from config import Config
from influx import write_influx
from log import LOG_DEFAULT_FMT
from mqtt import write_mqtt
from ntfy import ReadingEvent

HEALTHCHECK_TIMEOUT_S: Final = 10.0


class Poller(lib_mpex.ChildProcess):
    def __init__(
        self,
        config: Config,
        ntfy_queue: Optional[multiprocessing.Queue],  # of ReadingEvent
        log_level: int,
        print_readings: bool,
        health_ns: Optional[Namespace] = None,
    ):
        self._config = config
        self._ntfy_queue = ntfy_queue
        self._log_level = log_level
        self._print_readings = print_readings
        self._health_ns = health_ns

    def _run(self):
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=self._log_level, format=LOG_DEFAULT_FMT)
        logger.info("starting poller")

        interval_s = self._config.poll_interval * 60
        with asyncio.Runner() as runner:
            while True:
                self._poll_once(logger, runner)
                time.sleep(interval_s)

    def _poll_once(self, logger: logging.Logger, runner: asyncio.Runner):
        now = datetime.datetime.now(datetime.UTC)
        try:
            reading = ara_read(runner, self._config.aranet_device_address)
        except Exception as e:
            logger.error(
                f"failed reading from {self._config.aranet_device_address}: {e}"
            )
            return

        logger.info(
            f"read from {reading.name}: CO2 {reading.co2} ppm, "
            f"{reading.temperature:.1f} °C, {reading.humidity:.0f}% RH, "
            f"{reading.pressure} mbar"
        )
        if self._health_ns is not None:
            self._health_ns.last_poll_at = now
        if self._print_readings:
            ara_print(self._config, reading)

        if self._ntfy_queue is not None:
            self._ntfy_queue.put(ReadingEvent(co2=reading.co2, t=now))

        healthy = True
        if self._config.influx:
            try:
                if not write_influx(self._config, reading, now):
                    logger.error("influx write failed")
                    healthy = False
            except Exception as e:
                logger.error(f"influx write failed: {e}")
                healthy = False
        if self._config.mqtt:
            if not write_mqtt(self._config, reading, now):
                healthy = False

        if healthy and self._config.healthcheck_ping_url:
            try:
                requests.get(
                    self._config.healthcheck_ping_url, timeout=HEALTHCHECK_TIMEOUT_S
                )
            except requests.RequestException as e:
                logger.error(f"healthcheck ping failed: {e}")
