"""Sensors for the S&P DOMEO EVO integration."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import IntEnum
from typing import override

from .domeo_evo_modbus import (
    AirSensType,
    ControlPanel,
    DomeoEvo,
    LimitSwitchState,
    OperatingMode,
    PreheaterState,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfRatio,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import DomeoEvoConfigEntry
from .entity import DomeoEvoEntity, DomeoEvoEntityDescription

PARALLEL_UPDATES = 0


def _options(enum_type: type[IntEnum]) -> list[str]:
    """The sensor options a device enum maps to."""
    return [member.name.lower() for member in enum_type]


def _option(value: IntEnum | None) -> str | None:
    """The sensor state of a device enum value."""
    return None if value is None else value.name.lower()


@dataclass(frozen=True, kw_only=True)
class DomeoEvoSensorEntityDescription(
    SensorEntityDescription, DomeoEvoEntityDescription
):
    """Describe a DOMEO EVO sensor."""

    value_fn: Callable[[DomeoEvo], float | str | None]
    exists_fn: Callable[[DomeoEvo], bool] = lambda device: True


def _temperature(
    key: str,
    value_fn: Callable[[DomeoEvo], float | None],
    *,
    enabled_default: bool = True,
) -> DomeoEvoSensorEntityDescription:
    """Describe one of the unit's five temperature probes."""
    return DomeoEvoSensorEntityDescription(
        key=key,
        translation_key=key,
        component="readings",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=enabled_default,
        value_fn=value_fn,
    )


SENSORS: tuple[DomeoEvoSensorEntityDescription, ...] = (
    DomeoEvoSensorEntityDescription(
        key="airflow",
        translation_key="airflow",
        component="readings",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        value_fn=lambda device: device.readings.airflow,
    ),
    DomeoEvoSensorEntityDescription(
        key="humidity",
        component="readings",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.readings.humidity,
        # Units without the integrated sensor report a constant 54 %.
        exists_fn=lambda device: device.regulates_humidity,
    ),
    DomeoEvoSensorEntityDescription(
        key="operating_mode",
        translation_key="operating_mode",
        component="readings",
        device_class=SensorDeviceClass.ENUM,
        options=_options(OperatingMode),
        value_fn=lambda device: _option(device.readings.operating_mode),
    ),
    _temperature("extract_temperature", lambda d: d.readings.extract_temperature),
    _temperature("exhaust_temperature", lambda d: d.readings.exhaust_temperature),
    _temperature("outdoor_temperature", lambda d: d.readings.outdoor_temperature),
    _temperature("supply_temperature", lambda d: d.readings.supply_temperature),
    _temperature(
        "pre_exchanger_temperature",
        lambda d: d.readings.pre_exchanger_temperature,
        # Not every unit has this probe; those without it report a fault.
        enabled_default=False,
    ),
    DomeoEvoSensorEntityDescription(
        key="voltage_input",
        translation_key="voltage_input",
        component="readings",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.readings.voltage_input,
    ),
    DomeoEvoSensorEntityDescription(
        key="bypass_limit_switch",
        translation_key="bypass_limit_switch",
        component="readings",
        device_class=SensorDeviceClass.ENUM,
        options=_options(LimitSwitchState),
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: _option(device.readings.bypass_limit_switch),
    ),
    DomeoEvoSensorEntityDescription(
        key="preheater_state",
        translation_key="preheater_state",
        component="readings",
        device_class=SensorDeviceClass.ENUM,
        options=_options(PreheaterState),
        value_fn=lambda device: _option(device.readings.preheater_state),
        exists_fn=lambda device: bool(device.status.preheater_connected),
    ),
    DomeoEvoSensorEntityDescription(
        key="control_panel",
        translation_key="control_panel",
        component="readings",
        device_class=SensorDeviceClass.ENUM,
        options=_options(ControlPanel),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: _option(device.readings.control_panel),
    ),
)

_PROBE_DEVICE_CLASSES: dict[AirSensType, tuple[SensorDeviceClass, str]] = {
    AirSensType.HUMIDITY: (SensorDeviceClass.HUMIDITY, PERCENTAGE),
    AirSensType.CO2: (SensorDeviceClass.CO2, UnitOfRatio.PARTS_PER_MILLION),
    AirSensType.VOC: (
        SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        UnitOfRatio.PARTS_PER_MILLION,
    ),
}


def _probe_value(probe: int) -> Callable[[DomeoEvo], int | None]:
    """Read the value of one AIRSENS probe."""

    def _value(device: DomeoEvo) -> int | None:
        return None if device.probes is None else device.probes.probe_value(probe)

    return _value


def _probe_sensors(device: DomeoEvo) -> Iterable[DomeoEvoSensorEntityDescription]:
    """Describe a sensor for each connected AIRSENS probe of a known type."""
    if device.probes is None:
        return
    for probe in device.connected_probes:
        probe_type = device.probes.probe_type(probe)
        if probe_type not in _PROBE_DEVICE_CLASSES:
            continue
        device_class, unit = _PROBE_DEVICE_CLASSES[probe_type]
        yield DomeoEvoSensorEntityDescription(
            key=f"probe_{probe}",
            translation_key=f"probe_{probe_type.name.lower()}",
            translation_placeholders={"probe": str(probe)},
            component="probes",
            device_class=device_class,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=unit,
            value_fn=_probe_value(probe),
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DomeoEvoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the DOMEO EVO sensors."""
    runtime_data = entry.runtime_data
    device = runtime_data.device
    async_add_entities(
        DomeoEvoSensor(runtime_data, description)
        for description in (*SENSORS, *_probe_sensors(device))
        if description.exists_fn(device)
    )


class DomeoEvoSensor(DomeoEvoEntity, SensorEntity):
    """A DOMEO EVO sensor."""

    entity_description: DomeoEvoSensorEntityDescription

    @property
    @override
    def native_value(self) -> float | str | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.device)
