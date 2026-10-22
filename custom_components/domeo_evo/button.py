"""Buttons for the S&P DOMEO EVO integration."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import override

from .domeo_evo_modbus import DomeoEvo

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DomeoEvoConfigEntry
from .entity import DomeoEvoEntity, DomeoEvoEntityDescription

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class DomeoEvoButtonEntityDescription(
    ButtonEntityDescription, DomeoEvoEntityDescription
):
    """Describe a DOMEO EVO button."""

    press_fn: Callable[[DomeoEvo], Awaitable[None]]


BUTTONS: tuple[DomeoEvoButtonEntityDescription, ...] = (
    DomeoEvoButtonEntityDescription(
        key="start_boost",
        translation_key="start_boost",
        component="readings",
        press_fn=lambda device: device.settings.async_start_boost(),
    ),
    DomeoEvoButtonEntityDescription(
        key="stop_boost",
        translation_key="stop_boost",
        component="readings",
        press_fn=lambda device: device.settings.async_stop_boost(),
    ),
    DomeoEvoButtonEntityDescription(
        key="reset_filter_alarm",
        translation_key="reset_filter_alarm",
        component="status",
        press_fn=lambda device: device.controls.async_reset_filter_alarm(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DomeoEvoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the DOMEO EVO buttons."""
    runtime_data = entry.runtime_data
    async_add_entities(
        DomeoEvoButton(runtime_data, description) for description in BUTTONS
    )


class DomeoEvoButton(DomeoEvoEntity, ButtonEntity):
    """A DOMEO EVO button."""

    entity_description: DomeoEvoButtonEntityDescription

    @override
    async def async_press(self) -> None:
        """Press the button."""
        await self._async_write(
            self.entity_description.press_fn(self.coordinator.device)
        )
