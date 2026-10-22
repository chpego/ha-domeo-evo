"""Helpers for the S&P DOMEO EVO integration."""

from collections.abc import Mapping
from typing import Any

from .domeo_evo_modbus import DEFAULT_STOPBITS
from modbus_connection import ModbusSerialParams, ModbusTcpParams

from homeassistant.const import CONF_DEVICE, CONF_HOST, CONF_PORT, CONF_TYPE

from .const import CONF_BAUDRATE, CONF_PARITY, PARITIES, TYPE_SERIAL


def create_modbus_params(
    data: Mapping[str, Any],
) -> ModbusSerialParams | ModbusTcpParams:
    """Build the Modbus link parameters from config entry data."""
    if data[CONF_TYPE] == TYPE_SERIAL:
        return ModbusSerialParams(
            device=data[CONF_DEVICE],
            baudrate=data[CONF_BAUDRATE],
            parity=PARITIES[data[CONF_PARITY]],
            stopbits=DEFAULT_STOPBITS,
        )
    return ModbusTcpParams(host=data[CONF_HOST], port=data[CONF_PORT])
