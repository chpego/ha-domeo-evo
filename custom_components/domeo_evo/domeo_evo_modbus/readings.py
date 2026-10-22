"""What the unit measures and reports, from its input registers (FC04).

Field addresses are protocol (PDU) addresses. The S&P table numbers input
registers from 30001, so table register ``30000 + n`` is address ``n - 1``.
"""

from __future__ import annotations

from modbus_connection.model import Component, enum, gauge, integer

from .enums import (
    AirSensType,
    ControlPanel,
    LimitSwitchState,
    OperatingMode,
    PreheaterState,
)

# The integrated humidity sensor reads this when it is not fitted.
HUMIDITY_SENSOR_ABSENT = 54


def _version(raw: int | None) -> str | None:
    """Format a firmware version, sent as ``xx.x`` times ten."""
    if raw is None:
        return None
    return f"{raw // 10}.{raw % 10}"


class Identity(Component):
    """The firmware versions, read once at setup."""

    register_space = "input"
    register_ranges = ((0, 1),)

    _unit_firmware = integer(0, signed=False)  # 30001
    _panel_firmware = integer(1, signed=False)  # 30002

    @property
    def unit_firmware(self) -> str | None:
        """The firmware version of the unit's main board."""
        return _version(self._unit_firmware)

    @property
    def panel_firmware(self) -> str | None:
        """The firmware version of the control panel."""
        return _version(self._panel_firmware)


class Readings(Component):
    """The unit's operating state and sensor readings."""

    register_space = "input"
    # The table documents only these addresses. Reads never cross the holes.
    register_ranges = ((2, 5), (10, 14), (16, 17), (21, 21))

    operating_mode = enum(2, OperatingMode)  # 30003
    """What the unit is doing now."""

    airflow = integer(3, signed=False, unit="m³/h")  # 30004
    """The current airflow."""

    humidity = integer(4, signed=False, unit="%")  # 30005
    """The integrated humidity sensor. Reads 54 when no sensor is fitted."""

    voltage_input = gauge(5, 0.1, signed=False, unit="V")  # 30006, in dV
    """The 0-10 V control input."""

    extract_temperature = gauge(10, 0.1, unit="°C")  # 30011
    """The air extracted from the dwelling."""

    exhaust_temperature = gauge(11, 0.1, unit="°C")  # 30012
    """The air rejected outside."""

    outdoor_temperature = gauge(12, 0.1, unit="°C")  # 30013
    """The fresh air taken in from outside."""

    supply_temperature = gauge(13, 0.1, unit="°C")  # 30014
    """The air blown into the dwelling."""

    pre_exchanger_temperature = gauge(14, 0.1, unit="°C")  # 30015
    """The air before the heat exchanger."""

    bypass_limit_switch = enum(16, LimitSwitchState)  # 30017
    """The bypass limit switch."""

    preheater_state = enum(17, PreheaterState)  # 30018
    """The defrost (preheat) battery."""

    control_panel = enum(21, ControlPanel)  # 30022
    """Which control panel is connected."""


class AirSensProbes(Component):
    """The five AIRSENS probe slots: their type and their reading."""

    register_space = "input"
    register_ranges = ((22, 31),)

    probe_1_type = enum(22, AirSensType)  # 30023
    probe_2_type = enum(23, AirSensType)  # 30024
    probe_3_type = enum(24, AirSensType)  # 30025
    probe_4_type = enum(25, AirSensType)  # 30026
    probe_5_type = enum(26, AirSensType)  # 30027

    probe_1_value = integer(27, signed=False)  # 30028, %RH or ppm
    probe_2_value = integer(28, signed=False)  # 30029
    probe_3_value = integer(29, signed=False)  # 30030
    probe_4_value = integer(30, signed=False)  # 30031
    probe_5_value = integer(31, signed=False)  # 30032

    def probe_type(self, probe: int) -> AirSensType | None:
        """The type of probe ``probe`` (1 to 5)."""
        _check_probe(probe)
        value: AirSensType | None = getattr(self, f"probe_{probe}_type")
        return value

    def probe_value(self, probe: int) -> int | None:
        """The reading of probe ``probe`` (1 to 5): %RH or ppm, by its type."""
        _check_probe(probe)
        value: int | None = getattr(self, f"probe_{probe}_value")
        return value


PROBES = (1, 2, 3, 4, 5)


def _check_probe(probe: int) -> None:
    """Raise ``ValueError`` for a probe number outside 1 to 5."""
    if probe not in PROBES:
        raise ValueError(f"probe must be 1 to 5, got {probe}")
