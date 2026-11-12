"""The coded values the DOMEO EVO reports and accepts.

Every member value is the raw code from the S&P register table
("TABLE DES REGISTRES MODBUS RTU DOMEO EVO", Rev. 240806).
"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class Model(StrEnum):
    """The unit size, which sets the airflow ranges the unit accepts."""

    DOMEO_EVO_225 = "225"
    DOMEO_EVO_315 = "315"
    DOMEO_EVO_450 = "450"


class Variant(StrEnum):
    """The control variant of the unit.

    Only the DHU and SERENITE variants regulate on humidity or air quality, so
    only they serve the humidity regulation registers (40011 to 40034).
    """

    FL = "fl"
    DHU = "dhu"
    SERENITE = "serenite"


class OperatingMode(IntEnum):
    """Input register 30003: what the unit is doing now."""

    CONSTANT_SPEED = 0
    PROPORTIONAL = 1
    AGILE = 2
    CLP = 3
    BYPASS = 4
    DEFROST = 5


class AutoMode(IntEnum):
    """Coil 2: how the unit regulates in automatic mode."""

    PROPORTIONAL = 0
    AGILE = 1


class ClpContact(IntEnum):
    """Coil 3: the wiring of the external CLP contact."""

    NORMALLY_OPEN = 0
    NORMALLY_CLOSED = 1


class EquipmentVersion(IntEnum):
    """Coil 1: the factory equipment configuration."""

    VERSION_A = 0
    VERSION_B = 1


class LimitSwitchState(IntEnum):
    """Input register 30017: the bypass limit switch."""

    NO_SIGNAL = 0
    OPEN = 1
    CLOSED = 2


class PreheaterState(IntEnum):
    """Input register 30018: the defrost (preheat) battery."""

    STOPPED = 0
    WAITING = 1
    ACTIVE = 2
    ALARM = 3


class ControlPanel(IntEnum):
    """Input register 30022: which control panel is connected.

    When both are connected, the wired panel wins and the radio panel is
    disabled.
    """

    NONE = 0
    WIRED = 1
    RADIO = 2


class AirSensType(IntEnum):
    """Input registers 30023 to 30027: the type of an AIRSENS probe."""

    NONE = 0
    HUMIDITY = 1
    VOC = 2
    CO2 = 3


class PreheatMode(IntEnum):
    """Holding register 40050: how the defrost (preheat) battery runs."""

    OFF = 0
    ON = 1
    MANUAL = 2
