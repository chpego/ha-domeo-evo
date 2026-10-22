"""The unit's alarms and status flags, from its discrete inputs (FC02).

The S&P table numbers discrete inputs from 10001, so table input
``10000 + n`` is address ``n - 1``.
"""

from __future__ import annotations

from modbus_connection.model import Component, discrete_input

from .readings import PROBES, _check_probe


class Status(Component):
    """Alarms, probe faults and connection flags."""

    discrete_ranges = ((0, 16),)

    defrost_active = discrete_input(0)  # 10001
    """Whether the unit is defrosting."""

    motor_1_fault = discrete_input(1)  # 10002
    """Whether motor 1 reports an error."""

    motor_2_fault = discrete_input(2)  # 10003
    """Whether motor 2 reports an error."""

    extract_probe_fault = discrete_input(3)  # 10004
    exhaust_probe_fault = discrete_input(4)  # 10005
    outdoor_probe_fault = discrete_input(5)  # 10006
    supply_probe_fault = discrete_input(6)  # 10007
    # Defaults to 1 (error) in the table: units without this probe report it.
    pre_exchanger_probe_fault = discrete_input(7)  # 10008

    clp_active = discrete_input(8)  # 10009
    """Whether the external CLP contact is active."""

    modbus_control = discrete_input(9)  # 10010
    """Whether the unit takes orders over Modbus (jumper JP1 closed)."""

    filter_alarm = discrete_input(10)  # 10011
    """Whether the filters are due for replacement."""

    # 1 means "not connected" for the five probes and the preheat battery.
    _probe_1_missing = discrete_input(11)  # 10012
    _probe_2_missing = discrete_input(12)  # 10013
    _probe_3_missing = discrete_input(13)  # 10014
    _probe_4_missing = discrete_input(14)  # 10015
    _probe_5_missing = discrete_input(15)  # 10016
    _preheater_missing = discrete_input(16)  # 10017

    def probe_connected(self, probe: int) -> bool | None:
        """Whether AIRSENS probe ``probe`` (1 to 5) is connected."""
        _check_probe(probe)
        missing: bool | None = getattr(self, f"_probe_{probe}_missing")
        return None if missing is None else not missing

    @property
    def connected_probes(self) -> tuple[int, ...]:
        """The AIRSENS probes the unit reports as connected."""
        return tuple(probe for probe in PROBES if self.probe_connected(probe))

    @property
    def preheater_connected(self) -> bool | None:
        """Whether a defrost (preheat) battery is connected."""
        missing = self._preheater_missing
        return None if missing is None else not missing
