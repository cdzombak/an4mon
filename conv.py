import math


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def mbar_to_inhg(mbar: float) -> float:
    return mbar * 0.02952998751


def absolute_humidity_g_m3(temp_celsius: float, relative_humidity_pct: float) -> float:
    """
    Calculate absolute humidity in g/m³ using Magnus-Tetens approximation.
    
    Args:
        temp_celsius: Temperature in degrees Celsius
        relative_humidity_pct: Relative humidity as percentage (0-100)
    
    Returns:
        Absolute humidity in grams per cubic meter
        
    Test cases for quick sanity check:
        20°C, 60% RH → 10.37 g/m³ (typical room conditions)
        0°C, 50% RH → 2.42 g/m³ (cold conditions)
        25°C, 80% RH → 18.42 g/m³ (warm, humid conditions)
    """
    svp = 6.112 * math.exp((17.67 * temp_celsius) / (temp_celsius + 243.5))
    return (svp * relative_humidity_pct * 2.1674) / (273.15 + temp_celsius)
