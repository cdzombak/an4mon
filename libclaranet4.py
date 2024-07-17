import asyncio
from dataclasses import dataclass
from bleak import BleakScanner, BleakClient

#
# This file taken from https://github.com/bede/claranet4 at commit
# https://github.com/bede/claranet4/commit/11143c3c457bceebae399e0ba067dcd34ec79341
# Under MIT license (Copyright 2022 Bede Constantinides)
#


class BTIOError(RuntimeError):
    pass


@dataclass
class Device:
    address: str
    name: str
    rssi: int


class Reading:
    def __init__(self, device: Device, response: bytearray):
        self.name: str = device.name
        self.address: str = device.address
        self.rssi: int = device.rssi
        self.co2: int = _le16(response)  # ppm
        self.temperature: float = round(_le16(response, 2) / 20, 1)  # degrees C
        self.pressure: float = round(_le16(response, 4) / 10, 1)  # millibar
        # relative humidity in percent (range 0-100)
        self.humidity: float = round(_le16(response, 5) / 255, 1)


def _le16(data: bytearray, start: int = 0) -> int:
    """Read long integer from specified offset of bytearray"""
    raw = bytearray(data)
    return raw[start] + (raw[start + 1] << 8)


async def _discover() -> list[Device]:
    """Return list of Devices sorted by descending RSSI dBm"""
    devices = [
        Device(address=d.address, name=str(d.name), rssi=d.rssi)
        for d in await BleakScanner.discover()
    ]
    return sorted(devices, key=lambda d: d.rssi, reverse=True)


async def _request_measurements(address: str) -> bytearray:
    """Request measurements bytearray for target address"""
    UUID_CURRENT_MEASUREMENTS_SIMPLE = "f0cd1503-95da-4f4b-9ac8-aa55d312af0c"
    async with BleakClient(address) as client:
        return await client.read_gatt_char(UUID_CURRENT_MEASUREMENTS_SIMPLE)


def scan(runner: asyncio.Runner) -> list[Device]:
    """Find Bluetooth devices in the vicinity, sorted by descending RSSI dBm"""
    return runner.run(_discover())


def scan_ara4s(runner: asyncio.Runner) -> list[Device]:
    """Find Aranet4 devices in the vicinity, sorted by descending RSSI dBm"""
    return [d for d in scan(runner) if "Aranet4" in d.name]


def find_device(runner: asyncio.Runner, address) -> Device:
    """Find Device by address"""
    ble_device = runner.run(BleakScanner.find_device_by_address(address))
    if ble_device:
        return Device(
            address=ble_device.address,
            name=str(ble_device.name),
            rssi=ble_device.rssi,
        )
    else:
        raise BTIOError(f"could not find device {address}")


def read_ara4(runner: asyncio.Runner, address: str = "") -> Reading:
    if address:
        device = find_device(runner, address)
    else:
        ara4_devices = scan_ara4s(runner)
        if not ara4_devices:
            raise BTIOError("no Aranet4 devices discovered")
        else:
            device = ara4_devices[0]
    measurements = runner.run(_request_measurements(device.address))
    return Reading(device, measurements)
