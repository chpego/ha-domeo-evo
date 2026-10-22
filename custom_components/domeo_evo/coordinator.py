"""Data update coordinator for the S&P DOMEO EVO integration."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import override

from .domeo_evo_modbus import READINGS, DomeoEvo, UpdateReport
from modbus_connection import ModbusError, ModbusTimeoutError
from propcache.api import cached_property

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER, TIMEOUTS_BEFORE_RECONNECT

_LOGGER = logging.getLogger(__name__)


class DomeoEvoCoordinator(DataUpdateCoordinator[UpdateReport]):
    """Poll one group of the unit's components."""

    config_entry: DomeoEvoConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: DomeoEvoConfigEntry,
        device: DomeoEvo,
        poll: Callable[[], Awaitable[UpdateReport]],
        interval: timedelta,
        *,
        reconnect_on_timeouts: bool = False,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=interval,
        )
        self.device = device
        self._poll = poll
        self._failing: set[str] = set()
        # Only one coordinator may drop the link, or it could drop it under a
        # poll the other one has in flight.
        self._reconnect_on_timeouts = reconnect_on_timeouts
        self._timeouts = 0

    @cached_property
    def device_info(self) -> DeviceInfo:
        """The unit every entity of this config entry belongs to."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=self.device.name,
            sw_version=self.device.identity.unit_firmware,
        )

    @override
    async def _async_update_data(self) -> UpdateReport:
        try:
            report = await self._poll()
        except ModbusTimeoutError as err:
            await self._async_count_timeout()
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_response",
                translation_placeholders={"error": str(err)},
            ) from err
        except ModbusError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(err)},
            ) from err
        self._timeouts = 0
        if not report.updated:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_component_answered",
            ) from ExceptionGroup(
                "every component failed to refresh", list(report.failed.values())
            )
        self._log_component_changes(report)
        return report

    async def _async_count_timeout(self) -> None:
        """Drop a link that stays open while the unit behind it is silent."""
        if not self._reconnect_on_timeouts:
            return
        self._timeouts += 1
        if self._timeouts >= TIMEOUTS_BEFORE_RECONNECT:
            self._timeouts = 0
            _LOGGER.debug("%s: polls keep timing out, reconnecting", self.name)
            await self.device.modbus_unit.disconnect()

    def _log_component_changes(self, report: UpdateReport) -> None:
        """Log a component's first failure and its recovery, once each."""
        for name, cause in report.failed.items():
            if name not in self._failing:
                self._failing.add(name)
                _LOGGER.warning(
                    "%s: %s failed to refresh, its entities are unavailable: %s",
                    self.name,
                    name,
                    cause,
                )
        for name in report.updated & self._failing:
            self._failing.discard(name)
            _LOGGER.info("%s: %s is available again", self.name, name)


@dataclass
class DomeoEvoRuntimeData:
    """The two coordinators of a config entry."""

    readings: DomeoEvoCoordinator
    settings: DomeoEvoCoordinator

    @property
    def device(self) -> DomeoEvo:
        """The unit both coordinators poll."""
        return self.readings.device

    def coordinator_for(self, component: str) -> DomeoEvoCoordinator:
        """Which coordinator polls a given component."""
        return self.readings if component in READINGS else self.settings


type DomeoEvoConfigEntry = ConfigEntry[DomeoEvoRuntimeData]
