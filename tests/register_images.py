"""Register images of a DOMEO EVO, for tests that need no hardware.

Load one into ``modbus_connection.mock`` with ``load_image``. Addresses are
protocol (PDU) addresses: the S&P table number minus its base, minus one.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _signed(value: int) -> int:
    """A negative value as it appears on the wire."""
    return value & 0xFFFF


# A factory-fresh DOMEO EVO 225 FL.
FACTORY_225_FL: dict[str, dict[int, Any]] = {
    "input": {
        0: 123,  # 30001: firmware 12.3
        1: 105,  # 30002: panel firmware 10.5
        2: 1,  # 30003: proportional mode
        3: 90,  # 30004: 90 m³/h
        4: 54,  # 30005: no humidity sensor fitted
        5: 37,  # 30006: 3.7 V
        10: 215,  # 30011: extract 21.5 °C
        11: 98,  # 30012: exhaust 9.8 °C
        12: _signed(-35),  # 30013: outdoor -3.5 °C
        13: 187,  # 30014: supply 18.7 °C
        14: _signed(-20),  # 30015: pre-exchanger -2.0 °C
        16: 1,  # 30017: limit switch open
        17: 0,  # 30018: preheater stopped
        21: 1,  # 30022: wired panel
    },
    "discrete": {
        7: True,  # 10008: no pre-exchanger probe on this unit
        9: True,  # 10010: Modbus control (JP1 closed)
        11: True,  # 10012-10016: no AIRSENS probes
        12: True,
        13: True,
        14: True,
        15: True,
        16: True,  # 10017: no preheat battery
    },
    "coil": {
        3: False,  # coil 4: holiday mode off
        4: True,  # coil 5: automatic bypass on
    },
    "holding": {
        0: 1,  # 40001: unit id 1
        1: 8,  # 40002: 19200 baud
        2: 2,  # 40003: even parity
        6: 60,  # 40007: low airflow
        7: 120,  # 40008: high airflow
        8: 225,  # 40009: freecooling airflow
        38: 12,  # 40039
        39: 24,  # 40040
        40: 8,  # 40041
        41: 60,  # 40042
        44: 6,  # 40045
        45: 55,  # 40046: 5.5 °C
        46: 12,  # 40047: 1.2 V
        48: 5,  # 40049
        49: 1,  # 40050: preheat on
        52: _signed(-130),  # 40053: -13.0 °C
        53: 30,  # 40054
        # 40011-40034, humidity regulation defaults.
        10: [60, 60, 60, 60, 60, 60],
        16: [225, 225, 225, 225, 225, 225],
        22: [60, 1000, 1000, 1000, 1000, 1000],
        28: [90, 2000, 2000, 2000, 2000, 2000],
    },
}

# A unit of the previous Domeo range (Domeo 210 FL, from the S&P tables of
# 2014 and 2017), read at the DOMEO EVO addresses. It is not a DOMEO EVO. Its
# tables leave input registers 0 to 5 undocumented; this image assumes they
# read 0.
PREVIOUS_DOMEO_210_FL: dict[str, dict[int, Any]] = {
    "input": {
        **dict.fromkeys(range(6), 0),
        6: 123,  # firmware 12.3
        9: 0,  # type of unit: Domeo 210 FL
        10: 1,  # type of control: constant airflow
        13: 60,  # low airflow
        14: 135,  # boost airflow
        16: 60,  # current airflow (30017 on a DOMEO EVO)
        17: 0,  # 0-10 V input
        21: 215,  # extract 21.5 °C (30022 on a DOMEO EVO)
        22: 98,  # exhaust 9.8 °C
        23: _signed(-35),  # outdoor -3.5 °C
        24: 187,  # supply 18.7 °C
    },
    "discrete": dict.fromkeys(range(17), False),
    "coil": dict.fromkeys(range(15), False),
    "holding": {0: 1, 1: 8, 2: 2, 8: 0, 9: 60, 10: 135, 11: 210, 15: 0},
}

# Every address the S&P table documents, by space.
DOCUMENTED: dict[str, set[int]] = {
    "input": {*range(0, 6), *range(10, 15), 16, 17, *range(21, 32)},
    "discrete": set(range(0, 17)),
    "coil": set(range(0, 9)),
    "holding": {*range(0, 3), *range(4, 34), *range(38, 42), *range(44, 54)},
}


def load_image(unit: Any, image: dict[str, dict[int, Any]] = FACTORY_225_FL) -> None:
    """Seed a ``MockModbusUnit`` with a copy of a register image."""
    for space, values in deepcopy(image).items():
        getattr(unit, space).update(values)
