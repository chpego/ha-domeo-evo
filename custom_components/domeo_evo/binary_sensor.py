"""Binary sensors for the S&P DOMEO EVO integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from .domeo_evo_modbus import DomeoEvo

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DomeoEvoConfigEntry
from .entity import DomeoEvoEntity, DomeoEvoEntityDescription

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class DomeoEvoBinarySensorEntityDescription(
    BinarySensorEntityDescription, DomeoEvoEntityDescription
):
    """Describe a DOMEO EVO binary sensor."""

    value_fn: Callable[[DomeoEvo], bool | None]


def _probe_fault(
    key: str, value_fn: Callable[[DomeoEvo], bool | None]
) -> DomeoEvoBinarySensorEntityDescription:
    """Describe the fault flag of one temperature probe."""
    return DomeoEvoBinarySensorEntityDescription(
        key=key,
        translation_key=key,
        component="status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=value_fn,
    )


BINARY_SENSORS: tuple[DomeoEvoBinarySensorEntityDescription, ...] = (
    DomeoEvoBinarySensorEntityDescription(
        key="filter_alarm",
        translation_key="filter_alarm",
        component="status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda device: device.status.filter_alarm,
    ),
    DomeoEvoBinarySensorEntityDescription(
        key="defrost",
        translation_key="defrost",
        component="status",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda device: device.status.defrost_active,
    ),
    DomeoEvoBinarySensorEntityDescription(
        key="motor_1_fault",
        translation_key="motor_1_fault",
        component="status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.status.motor_1_fault,
    ),
    DomeoEvoBinarySensorEntityDescription(
        key="motor_2_fault",
        translation_key="motor_2_fault",
        component="status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.status.motor_2_fault,
    ),
    DomeoEvoBinarySensorEntityDescription(
        key="clp",
        translation_key="clp",
        component="status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.status.clp_active,
    ),
    _probe_fault("extract_probe_fault", lambda d: d.status.extract_probe_fault),
    _probe_fault("exhaust_probe_fault", lambda d: d.status.exhaust_probe_fault),
    _probe_fault("outdoor_probe_fault", lambda d: d.status.outdoor_probe_fault),
    _probe_fault("supply_probe_fault", lambda d: d.status.supply_probe_fault),
    _probe_fault(
        "pre_exchanger_probe_fault", lambda d: d.status.pre_exchanger_probe_fault
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DomeoEvoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the DOMEO EVO binary sensors."""
    runtime_data = entry.runtime_data
    async_add_entities(
        DomeoEvoBinarySensor(runtime_data, description)
        for description in BINARY_SENSORS
    )


class DomeoEvoBinarySensor(DomeoEvoEntity, BinarySensorEntity):
    """A DOMEO EVO binary sensor."""

    entity_description: DomeoEvoBinarySensorEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the state of the flag."""
        return self.entity_description.value_fn(self.coordinator.device)
