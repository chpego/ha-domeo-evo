"""Diagnostics for the S&P DOMEO EVO integration."""

from typing import Any

from modbus_connection import ModbusError

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import DomeoEvoConfigEntry

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: DomeoEvoConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    The raw register map loads straight into ``modbus_connection.mock``, which
    reproduces a reported problem without the hardware. The unit stores no
    personal data, so nothing in it needs redacting.
    """
    runtime_data = entry.runtime_data
    device = runtime_data.device
    try:
        raw: dict[str, Any] = dict(await device.async_read_raw())
    except ModbusError as err:
        raw = {"error": str(err)}

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "device": {
            "name": device.name,
            "unit_firmware": device.identity.unit_firmware,
            "panel_firmware": device.identity.panel_firmware,
            "connected_probes": list(device.connected_probes),
            "humidity_regulation": device.humidity_settings is not None,
        },
        "readings": {
            "updated": sorted(runtime_data.readings.data.updated),
            "failed": {
                name: str(err)
                for name, err in runtime_data.readings.data.failed.items()
            },
        },
        "settings": {
            "updated": sorted(runtime_data.settings.data.updated),
            "failed": {
                name: str(err)
                for name, err in runtime_data.settings.data.failed.items()
            },
        },
        "raw": raw,
    }
