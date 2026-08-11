import datetime
import unittest

from co2 import Co2WarningLevel
from config import Config
from ntfy import fmt_duration, mute_action, should_notify


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


class TestShouldNotifyMuted(unittest.TestCase):
    def setUp(self):
        self.cfg = _cfg()
        self.now = datetime.datetime(2026, 1, 1, 12, 0, tzinfo=datetime.UTC)
        self.mute_until = self.now + datetime.timedelta(hours=1)
        self.long_ago = self.now - datetime.timedelta(hours=1)

    def test_mute_suppresses_yellow_after_green(self):
        self.assertFalse(
            should_notify(
                self.cfg,
                Co2WarningLevel.GREEN,
                self.long_ago,
                Co2WarningLevel.YELLOW,
                self.now,
                self.mute_until,
            )
        )

    def test_mute_suppresses_yellow_renotify(self):
        self.assertFalse(
            should_notify(
                self.cfg,
                Co2WarningLevel.YELLOW,
                self.long_ago,
                Co2WarningLevel.YELLOW,
                self.now,
                self.mute_until,
            )
        )

    def test_mute_suppresses_red_renotify(self):
        self.assertFalse(
            should_notify(
                self.cfg,
                Co2WarningLevel.RED,
                self.long_ago,
                Co2WarningLevel.RED,
                self.now,
                self.mute_until,
            )
        )

    def test_escalation_to_red_breaks_through_mute(self):
        for last_level in (Co2WarningLevel.GREEN, Co2WarningLevel.YELLOW):
            self.assertTrue(
                should_notify(
                    self.cfg,
                    last_level,
                    self.now,
                    Co2WarningLevel.RED,
                    self.now,
                    self.mute_until,
                )
            )

    def test_expired_mute_has_no_effect(self):
        self.assertTrue(
            should_notify(
                self.cfg,
                Co2WarningLevel.YELLOW,
                self.long_ago,
                Co2WarningLevel.YELLOW,
                self.now,
                self.now - datetime.timedelta(minutes=1),
            )
        )

    def test_no_mute_behaves_as_before(self):
        self.assertTrue(
            should_notify(
                self.cfg,
                Co2WarningLevel.YELLOW,
                self.long_ago,
                Co2WarningLevel.YELLOW,
                self.now,
                None,
            )
        )


class TestMuteAction(unittest.TestCase):
    def test_mute_blob(self):
        self.assertEqual(
            mute_action("Mute 2h", 7200, "https://example.com:5560"),
            "http, Mute 2h, https://example.com:5560/mute, "
            "body='{\"s\": 7200}', "
            "headers.content-type=application/json, clear=true",
        )

    def test_unmute_blob(self):
        self.assertEqual(
            mute_action("Unmute", 0, "https://example.com"),
            "http, Unmute, https://example.com/mute, "
            "body='{\"s\": 0}', "
            "headers.content-type=application/json, clear=true",
        )


class TestFmtDuration(unittest.TestCase):
    def test_whole_hours(self):
        self.assertEqual(fmt_duration(7200), "2h")
        self.assertEqual(fmt_duration(21600), "6h")

    def test_minutes_only(self):
        self.assertEqual(fmt_duration(600), "10m")
        self.assertEqual(fmt_duration(60), "1m")

    def test_hours_and_minutes(self):
        self.assertEqual(fmt_duration(5400), "1h 30m")


if __name__ == "__main__":
    unittest.main()
