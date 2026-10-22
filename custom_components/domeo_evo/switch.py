"""Switches for the S&P DOMEO EVO integration."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, override

from .domeo_evo_modbus import DomeoEvo

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DomeoEvoConfigEntry
from .entity import DomeoEvoEntity, DomeoEvoEntityDescription

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class DomeoEvoSwitchEntityDescription(
    SwitchEntityDescription, DomeoEvoEntityDescription
):
    """Describe a DOMEO EVO switch."""

    value_fn: Callable[[DomeoEvo], bool | None]
    write_fn: Callable[[DomeoEvo, bool], Awaitable[None]]


SWITCHES: tuple[DomeoEvoSwitchEntityDescription, ...] = (
    DomeoEvoSwitchEntityDescription(
        key="holiday_mode",
        translation_key="holiday_mode",
        component="controls",
        value_fn=lambda device: device.controls.holiday_mode,
        write_fn=lambda device, on: device.controls.async_set_holiday_mode(on),
    ),
    DomeoEvoSwitchEntityDescription(
        key="manual_bypass",
        translation_key="manual_bypass",
        component="controls",
        value_fn=lambda device: device.controls.manual_bypass,
        write_fn=lambda device, on: device.controls.async_set_manual_bypass(on),
    ),
    DomeoEvoSwitchEntityDescription(
        key="auto_bypass",
        translation_key="auto_bypass",
        component="controls",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda device: device.controls.auto_bypass,
        write_fn=lambda device, on: device.controls.async_set_auto_bypass(on),
    ),
    DomeoEvoSwitchEntityDescription(
        key="defrost_allowed",
        translation_key="defrost_allowed",
        component="controls",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.controls.defrost_allowed,
        write_fn=lambda device, on: device.controls.async_set_defrost_allowed(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DomeoEvoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the DOMEO EVO switches."""
    runtime_data = entry.runtime_data
    async_add_entities(
        DomeoEvoSwitch(runtime_data, description) for description in SWITCHES
    )


class DomeoEvoSwitch(DomeoEvoEntity, SwitchEntity):
    """A DOMEO EVO switch."""

    entity_description: DomeoEvoSwitchEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the switch."""
        return self.entity_description.value_fn(self.coordinator.device)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_write(
            self.entity_description.write_fn(self.coordinator.device, True)
        )

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_write(
            self.entity_description.write_fn(self.coordinator.device, False)
        )
