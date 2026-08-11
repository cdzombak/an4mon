import datetime
import unittest

from co2 import Co2WarningLevel
from config import Config
from ntfy import should_notify


def _cfg() -> Config:
    return Config.from_dict(
        {
            "aranet_device_address": "test-addr",
            "device_name": "test",
            "notify_yellow_every": 30,
            "notify_red_every": 5,
        }
    )


class TestShouldNotify(unittest.TestCase):
    def setUp(self):
        self.cfg = _cfg()
        self.now = datetime.datetime(2026, 1, 1, 12, 0, tzinfo=datetime.UTC)

    def test_green_never_notifies(self):
        for last_level in Co2WarningLevel:
            self.assertFalse(
                should_notify(
                    self.cfg,
                    last_level,
                    self.now - datetime.timedelta(hours=1),
                    Co2WarningLevel.GREEN,
                    self.now,
                )
            )

    def test_red_notifies_on_level_change(self):
        for last_level in (Co2WarningLevel.GREEN, Co2WarningLevel.YELLOW):
            self.assertTrue(
                should_notify(
                    self.cfg, last_level, self.now, Co2WarningLevel.RED, self.now
                )
            )

    def test_red_renotifies_after_interval(self):
        self.assertTrue(
            should_notify(
                self.cfg,
                Co2WarningLevel.RED,
                self.now - datetime.timedelta(minutes=6),
                Co2WarningLevel.RED,
                self.now,
            )
        )
        self.assertFalse(
            should_notify(
                self.cfg,
                Co2WarningLevel.RED,
                self.now - datetime.timedelta(minutes=4),
                Co2WarningLevel.RED,
                self.now,
            )
        )

    def test_yellow_notifies_after_green(self):
        self.assertTrue(
            should_notify(
                self.cfg,
                Co2WarningLevel.GREEN,
                self.now,
                Co2WarningLevel.YELLOW,
                self.now,
            )
        )

    def test_yellow_renotifies_after_interval(self):
        self.assertTrue(
            should_notify(
                self.cfg,
                Co2WarningLevel.YELLOW,
                self.now - datetime.timedelta(minutes=31),
                Co2WarningLevel.YELLOW,
                self.now,
            )
        )
        self.assertFalse(
            should_notify(
                self.cfg,
                Co2WarningLevel.YELLOW,
                self.now - datetime.timedelta(minutes=29),
                Co2WarningLevel.YELLOW,
                self.now,
            )
        )

    def test_yellow_after_red_respects_interval(self):
        self.assertFalse(
            should_notify(
                self.cfg,
                Co2WarningLevel.RED,
                self.now - datetime.timedelta(minutes=10),
                Co2WarningLevel.YELLOW,
                self.now,
            )
        )


if __name__ == "__main__":
    unittest.main()
