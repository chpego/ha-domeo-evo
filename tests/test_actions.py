"""Tests for the entities that send commands to the S&P DOMEO EVO."""

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from modbus_connection import IllegalDataValueError, IllegalFunctionError
from modbus_connection.mock import MockModbusUnit, WriteEvent
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.domeo_evo.const import READINGS_INTERVAL

from . import MOCK_SERENITE_DATA, serenite_image

COIL = 0x05
FC06 = 0x06
FC16 = 0x10


@pytest.fixture
def writes(mock_unit: MockModbusUnit) -> list[WriteEvent]:
    """The writes the mock unit receives."""
    events: list[WriteEvent] = []
    mock_unit.on_write(events.append)
    return events


@pytest.mark.parametrize(
    ("domain", "service", "entity_id", "data", "write"),
    [
        pytest.param(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            "switch.domeo_evo_225_fl_holiday_mode",
            {},
            WriteEvent("coil", 3, [False], COIL),
            id="holiday_mode_on_writes_0",
        ),
        pytest.param(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            "switch.domeo_evo_225_fl_holiday_mode",
            {},
            WriteEvent("coil", 3, [True], COIL),
            id="holiday_mode_off_writes_1",
        ),
        pytest.param(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            "switch.domeo_evo_225_fl_manual_bypass",
            {},
            WriteEvent("coil", 5, [True], COIL),
            id="manual_bypass",
        ),
        pytest.param(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            "select.domeo_evo_225_fl_automatic_mode",
            {ATTR_OPTION: "agile"},
            WriteEvent("coil", 1, [True], COIL),
            id="auto_mode",
        ),
        pytest.param(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            "button.domeo_evo_225_fl_start_boost",
            {},
            WriteEvent("holding", 9, [1], FC06),
            id="start_boost",
        ),
        pytest.param(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            "button.domeo_evo_225_fl_stop_boost",
            {},
            WriteEvent("holding", 9, [0], FC16),
            id="stop_boost",
        ),
        pytest.param(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            "button.domeo_evo_225_fl_reset_filter_alarm",
            {},
            WriteEvent("coil", 7, [True], COIL),
            id="reset_filter_alarm_is_coil_8",
        ),
        pytest.param(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            "number.domeo_evo_225_fl_high_airflow",
            {ATTR_VALUE: 180},
            WriteEvent("holding", 7, [180], FC06),
            id="high_airflow",
        ),
        pytest.param(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            "number.domeo_evo_225_fl_filter_replacement_interval",
            {ATTR_VALUE: 12},
            WriteEvent("holding", 44, [12], FC06),
            id="filter_interval",
        ),
    ],
)
@pytest.mark.usefixtures("init_integration")
async def test_command(
    hass: HomeAssistant,
    writes: list[WriteEvent],
    domain: str,
    service: str,
    entity_id: str,
    data: dict[str, Any],
    write: WriteEvent,
) -> None:
    """Test each command sends exactly the expected Modbus write."""
    await hass.services.async_call(
        domain, service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
    )
    assert writes == [write]


@pytest.mark.usefixtures("init_integration")
async def test_holiday_mode_state_follows_the_unit(
    hass: HomeAssistant,
) -> None:
    """Test turning holiday mode on shows it on after the refresh."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.domeo_evo_225_fl_holiday_mode"},
        blocking=True,
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get("switch.domeo_evo_225_fl_holiday_mode").state == "on"


@pytest.mark.usefixtures("init_integration")
async def test_rejected_write(hass: HomeAssistant, mock_unit: MockModbusUnit) -> None:
    """Test a write the unit refuses raises a translated error."""
    mock_unit.fail_write(5, IllegalDataValueError(), register_type="coil")
    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.domeo_evo_225_fl_manual_bypass"},
            blocking=True,
        )
    assert exc_info.value.translation_key == "write_failed"


@pytest.mark.usefixtures("init_integration")
async def test_write_refused_while_jp1_is_open(
    hass: HomeAssistant, mock_unit: MockModbusUnit
) -> None:
    """Test the error points at jumper JP1 when the unit refuses a command.

    A real 225 FL with JP1 open answered exception 0x01 to every write.
    """
    mock_unit.fail_write(3, IllegalFunctionError(), register_type="coil")
    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.domeo_evo_225_fl_holiday_mode"},
            blocking=True,
        )
    assert exc_info.value.translation_key == "write_refused"


@pytest.mark.parametrize(
    ("register_image", "entry_data"),
    [(serenite_image(), MOCK_SERENITE_DATA)],
    indirect=True,
)
@pytest.mark.usefixtures("init_integration")
async def test_regulation_level_follows_the_probe_type(
    hass: HomeAssistant, writes: list[WriteEvent]
) -> None:
    """Test a probe threshold is written in the probe's own unit."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: "number.domeo_evo_225_fl_probe_1_upper_threshold",
            ATTR_VALUE: 1200,
        },
        blocking=True,
    )
    assert writes == [WriteEvent("holding", 29, [1200], FC06)]


@pytest.mark.parametrize(
    ("register_image", "entry_data"),
    [(serenite_image(), MOCK_SERENITE_DATA)],
    indirect=True,
)
@pytest.mark.usefixtures("init_integration")
async def test_value_the_library_refuses(
    hass: HomeAssistant,
    mock_unit: MockModbusUnit,
    writes: list[WriteEvent],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test a value the library refuses is reported as invalid, not sent."""
    # The probe changed type since setup, so the entity's range is stale.
    mock_unit.input[22] = 0
    freezer.tick(READINGS_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: "number.domeo_evo_225_fl_probe_1_upper_threshold",
                ATTR_VALUE: 1200,
            },
            blocking=True,
        )
    assert exc_info.value.translation_key == "invalid_value"
    assert writes == []
