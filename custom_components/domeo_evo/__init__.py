"""Integrate S&P DOMEO EVO ventilation units into Home Assistant."""

from .domeo_evo_modbus import DomeoEvo, Model, Variant

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_MODEL, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_UNIT_ID, CONF_VARIANT, READINGS_INTERVAL, SETTINGS_INTERVAL
from .coordinator import DomeoEvoConfigEntry, DomeoEvoCoordinator, DomeoEvoRuntimeData
from .helpers import create_modbus_params

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: DomeoEvoConfigEntry) -> bool:
    """Set up a DOMEO EVO from a config entry."""
    unit = async_get_unit(
        hass, entry, create_modbus_params(entry.data), entry.data[CONF_UNIT_ID]
    )
    device = DomeoEvo(
        unit, Model(entry.data[CONF_MODEL]), Variant(entry.data[CONF_VARIANT])
    )

    readings = DomeoEvoCoordinator(
        hass,
        entry,
        device,
        device.async_update_readings,
        READINGS_INTERVAL,
        reconnect_on_timeouts=True,
    )
    settings = DomeoEvoCoordinator(
        hass, entry, device, device.async_update_settings, SETTINGS_INTERVAL
    )
    # Setup runs on the first read and settles which probes exist, which the
    # platforms need to know before they add their entities.
    await readings.async_config_entry_first_refresh()
    await settings.async_config_entry_first_refresh()

    entry.runtime_data = DomeoEvoRuntimeData(readings, settings)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DomeoEvoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
