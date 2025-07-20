import unittest
import conv


class TestAbsoluteHumidity(unittest.TestCase):
    """Test cases for absolute humidity calculation function."""

    def test_typical_room_conditions(self):
        """Test 20°C, 60% RH → 10.37 g/m³ (typical room conditions)"""
        result = conv.absolute_humidity_g_m3(20.0, 60.0)
        self.assertAlmostEqual(result, 10.37, places=2)

    def test_cold_conditions(self):
        """Test 0°C, 50% RH → 2.42 g/m³ (cold conditions)"""
        result = conv.absolute_humidity_g_m3(0.0, 50.0)
        self.assertAlmostEqual(result, 2.42, places=2)

    def test_warm_humid_conditions(self):
        """Test 25°C, 80% RH → 18.42 g/m³ (warm, humid conditions)"""
        result = conv.absolute_humidity_g_m3(25.0, 80.0)
        self.assertAlmostEqual(result, 18.42, places=2)


if __name__ == '__main__':
    unittest.main()
