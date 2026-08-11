import datetime
import logging
import multiprocessing
from multiprocessing.managers import Namespace
from typing import Final

import waitress
from flask import Flask, jsonify, request
from flask_cors import CORS

import lib_mpex
from config import Config
from log import LOG_DEFAULT_FMT
from ntfy import MuteEvent

HEALTH_UNHEALTHY_POLLS: Final = 2  # unhealthy after this many missed poll intervals
MAX_MUTE_S: Final = 30 * 24 * 60 * 60  # longest accepted mute request


class WebServer(lib_mpex.ChildProcess):
    def __init__(
        self,
        config: Config,
        mute_ns: Namespace,
        health_ns: Namespace,
        ntfy_queue: multiprocessing.Queue,  # of ReadingEvent | MuteEvent
        log_level: int,
    ):
        self._config = config
        self._mute_ns = mute_ns
        self._health_ns = health_ns
        self._ntfy_queue = ntfy_queue
        self._log_level = log_level

    def _run(self):
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=self._log_level, format=LOG_DEFAULT_FMT)
        logging.getLogger("waitress").setLevel(self._log_level + 10)
        logger.info("starting web server")

        unhealthy_t = datetime.timedelta(
            minutes=HEALTH_UNHEALTHY_POLLS * self._config.poll_interval
        )

        app = Flask("an4mon")
        CORS(app)

        @app.route("/health", methods=["GET"])
        def health():
            last_poll_at = self._health_ns.last_poll_at
            if last_poll_at is None:
                return jsonify(
                    {"status": "unhealthy", "error": "no successful poll yet"}
                ), 503
            if datetime.datetime.now(datetime.UTC) - last_poll_at >= unhealthy_t:
                return jsonify(
                    {
                        "status": "unhealthy",
                        "error": f"no successful poll in over {unhealthy_t}",
                    }
                ), 503
            return jsonify({"status": "ok"})

        @app.route("/mute", methods=["POST"])
        def mute():
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                return jsonify({"error": "body must be a JSON object"}), 400
            secs = body.get("s")
            # bool is a subclass of int, but is not a meaningful duration:
            if not isinstance(secs, int) or isinstance(secs, bool):
                return jsonify({"error": "'s' must be an integer"}), 400
            if secs > MAX_MUTE_S:
                return jsonify({"error": f"'s' must be at most {MAX_MUTE_S}"}), 400

            now = datetime.datetime.now(datetime.UTC)
            if secs < 1:
                self._mute_ns.mute_until = now
                logger.info("unmuted")
                self._ntfy_queue.put_nowait(MuteEvent(mute_seconds=0))
            else:
                mute_until = now + datetime.timedelta(seconds=secs)
                self._mute_ns.mute_until = mute_until
                logger.info(f"muted until {mute_until}")
                self._ntfy_queue.put_nowait(MuteEvent(mute_seconds=secs))
            return jsonify({"status": "ok"})

        waitress.serve(
            app, listen=f"{self._config.web_bind_to}:{self._config.web_port}"
        )
