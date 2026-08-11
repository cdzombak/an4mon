import datetime
import logging
import multiprocessing
from multiprocessing.managers import Namespace

import waitress
from flask import Flask, jsonify, request
from flask_cors import CORS

import lib_mpex
from config import Config
from log import LOG_DEFAULT_FMT
from ntfy import MuteEvent


class WebServer(lib_mpex.ChildProcess):
    def __init__(
        self,
        config: Config,
        mute_ns: Namespace,
        ntfy_queue: multiprocessing.Queue,  # of ReadingEvent | MuteEvent
        log_level: int,
    ):
        self._config = config
        self._mute_ns = mute_ns
        self._ntfy_queue = ntfy_queue
        self._log_level = log_level

    def _run(self):
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=self._log_level, format=LOG_DEFAULT_FMT)
        logging.getLogger("waitress").setLevel(self._log_level + 10)
        logger.info("starting web server")

        app = Flask("an4mon")
        CORS(app)

        @app.route("/mute", methods=["POST"])
        def mute():
            body = request.get_json(silent=True)
            if body is None or not isinstance(body.get("s"), int):
                return jsonify({"error": "body must be JSON with int key 's'"}), 400
            secs: int = body["s"]

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
