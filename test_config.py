import unittest

from config import Config, ConfigValidationError


def _base_dict() -> dict:
    return {
        "aranet_device_address": "test-addr",
        "device_name": "test",
        "notify": True,
        "ntfy_topic": "test-topic",
        "notify_room_name": "Office",
    }


class TestWebConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = Config.from_dict(_base_dict())
        self.assertEqual(cfg.mute_short_h, 2)
        self.assertEqual(cfg.mute_long_h, 6)
        self.assertIsNone(cfg.web_external_base_url)
        self.assertEqual(cfg.web_port, 5560)
        self.assertEqual(cfg.web_bind_to, "127.0.0.1")

    def test_valid_web_config(self):
        cfg = Config.from_dict(
            _base_dict()
            | {
                "web_external_base_url": "https://example.com:5560",
                "mute_short_h": 1,
                "mute_long_h": 12,
                "web_port": 8080,
            }
        )
        self.assertEqual(cfg.web_external_base_url, "https://example.com:5560")
        self.assertEqual(cfg.mute_short_h, 1)
        self.assertEqual(cfg.mute_long_h, 12)
        self.assertEqual(cfg.web_port, 8080)

    def test_base_url_trailing_slash_stripped(self):
        cfg = Config.from_dict(
            _base_dict() | {"web_external_base_url": "https://example.com/"}
        )
        self.assertEqual(cfg.web_external_base_url, "https://example.com")

    def test_base_url_requires_http_scheme(self):
        with self.assertRaises(ConfigValidationError):
            Config.from_dict(
                _base_dict() | {"web_external_base_url": "example.com:5560"}
            )

    def test_mute_hours_must_be_positive_ints(self):
        for bad in (0, -1, "2", 1.5):
            with self.assertRaises(ConfigValidationError):
                Config.from_dict(
                    _base_dict()
                    | {
                        "web_external_base_url": "https://example.com",
                        "mute_short_h": bad,
                    }
                )
            with self.assertRaises(ConfigValidationError):
                Config.from_dict(
                    _base_dict()
                    | {
                        "web_external_base_url": "https://example.com",
                        "mute_long_h": bad,
                    }
                )

    def test_web_port_range(self):
        for bad in (0, -1, 65536, "8080"):
            with self.assertRaises(ConfigValidationError):
                Config.from_dict(
                    _base_dict()
                    | {
                        "web_external_base_url": "https://example.com",
                        "web_port": bad,
                    }
                )

    def test_web_validation_skipped_without_base_url(self):
        cfg = Config.from_dict(_base_dict() | {"mute_short_h": -5})
        self.assertEqual(cfg.mute_short_h, -5)


if __name__ == "__main__":
    unittest.main()
