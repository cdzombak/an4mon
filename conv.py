import math


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def mbar_to_inhg(mbar: float) -> float:
    return mbar * 0.02952998751


def absolute_humidity_g_m3(temp_celsius: float, relative_humidity_pct: float) -> float:
    svp = 6.112 * math.exp((17.67 * temp_celsius) / (temp_celsius + 243.5))
    return (svp * relative_humidity_pct * 2.1674) / (273.15 + temp_celsius)
