from enum import Enum

from config import Config


class Co2WarningLevel(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    @staticmethod
    def from_ppm(cfg: Config, ppm: float) -> "Co2WarningLevel":
        if ppm < cfg.co2_yellow:
            return Co2WarningLevel.GREEN
        elif ppm < cfg.co2_red:
            return Co2WarningLevel.YELLOW
        else:
            return Co2WarningLevel.RED

    @staticmethod
    def from_str(level: str) -> "Co2WarningLevel":
        return {
            Co2WarningLevel.GREEN.value.lower(): Co2WarningLevel.GREEN,
            Co2WarningLevel.YELLOW.value.lower(): Co2WarningLevel.YELLOW,
            Co2WarningLevel.RED.value.lower(): Co2WarningLevel.RED,
        }[level.lower()]

    def emoji(self) -> str:
        return {
            Co2WarningLevel.GREEN: "🟢",
            Co2WarningLevel.YELLOW: "🟡",
            Co2WarningLevel.RED: "🔴",
        }[self]

    def ntfy_tag(self) -> str:
        return {
            Co2WarningLevel.GREEN: "yellow_circle",
            Co2WarningLevel.YELLOW: "yellow_circle",
            Co2WarningLevel.RED: "red_circle",
        }[self]
