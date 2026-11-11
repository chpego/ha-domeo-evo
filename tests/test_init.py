"""Tests for setting up and polling the S&P DOMEO EVO integration."""

from datetime import timedelta
import json
from pathlib import Path
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.domeo_evo.const import (
    DOMAIN,
    READINGS_INTERVAL,
    SETTINGS_INTERVAL,
    TIMEOUTS_BEFORE_RECONNECT,
)

from . import MOCK_ENTRY_ID, MOCK_SERENITE_DATA, MOCK_TITLE, serenite_image

AIRFLOW = "sensor.domeo_evo_225_fl_airflow"
HOLIDAY_MODE = "switch.domeo_evo_225_fl_holiday_mode"
FILTER_ALARM = "binary_sensor.domeo_evo_225_fl_filter_replacement"


@pytest.fixture
def platforms() -> list[Platform]:
    """Set up the platforms these tests look at."""
    return [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]


async def _poll(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Let the readings coordinator poll once."""
    freezer.tick(READINGS_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test the entry loads, reads the unit, and unloads."""
    assert init_integration.state is ConfigEntryState.LOADED
    assert hass.states.get(AIRFLOW).state == "90"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(ModbusConnectionError(), id="unreachable"),
        pytest.param(ModbusTimeoutError(), id="silent"),
    ],
)
async def test_setup_retries_while_the_unit_is_unreachable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_unit: MockModbusUnit,
    mock_get_unit: object,
    error: Exception,
) -> None:
    """Test setup is retried until the unit answers."""
    mock_unit.fail_requests(error)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_retries_when_nothing_answers(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_unit: MockModbusUnit,
    mock_get_unit: object,
) -> None:
    """Test a unit that refuses every block is not set up."""
    mock_unit.fail_read(2, IllegalDataAddressError(), register_type="input")
    mock_unit.fail_read(0, IllegalDataAddressError(), register_type="discrete")
    mock_unit.fail_read(0, IllegalDataAddressError(), register_type="coil")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_failing_component_only_affects_its_entities(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_unit: MockModbusUnit,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a component that stops answering, then recovers."""
    mock_unit.fail_read(0, IllegalDataAddressError(), register_type="coil")
    await _poll(hass, freezer)
    assert hass.states.get(HOLIDAY_MODE).state == STATE_UNAVAILABLE
    assert hass.states.get(AIRFLOW).state == "90"
    assert "controls failed to refresh" in caplog.text

    mock_unit.fail_read(0, None, register_type="coil")
    await _poll(hass, freezer)
    assert hass.states.get(HOLIDAY_MODE).state == "off"
    assert "controls is available again" in caplog.text


async def test_unit_going_offline(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_unit: MockModbusUnit,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test entities go unavailable while the link is down, then come back."""
    mock_unit.fail_requests(ModbusConnectionError())
    await _poll(hass, freezer)
    assert hass.states.get(AIRFLOW).state == STATE_UNAVAILABLE
    assert hass.states.get(FILTER_ALARM).state == STATE_UNAVAILABLE

    mock_unit.fail_requests(None)
    mock_unit.input[3] = 165
    await _poll(hass, freezer)
    assert hass.states.get(AIRFLOW).state == "165"


async def test_nothing_answering_marks_entities_unavailable(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_unit: MockModbusUnit,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test a poll where every component is refused."""
    mock_unit.fail_read(2, IllegalDataAddressError(), register_type="input")
    mock_unit.fail_read(0, IllegalDataAddressError(), register_type="discrete")
    mock_unit.fail_read(0, IllegalDataAddressError(), register_type="coil")
    await _poll(hass, freezer)
    assert hass.states.get(AIRFLOW).state == STATE_UNAVAILABLE


async def test_reconnects_after_repeated_timeouts(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    mock_unit: MockModbusUnit,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test a link that stays up while the unit is silent is dropped."""
    assert mock_connection.connected
    mock_unit.fail_requests(ModbusTimeoutError())
    for _ in range(TIMEOUTS_BEFORE_RECONNECT - 1):
        await _poll(hass, freezer)
        assert mock_connection.connected

    await _poll(hass, freezer)
    assert not mock_connection.connected
    assert hass.states.get(AIRFLOW).state == STATE_UNAVAILABLE

    mock_unit.fail_requests(None)
    await _poll(hass, freezer)
    assert hass.states.get(AIRFLOW).state == "90"


# The settings coordinator only polls while a number entity listens to it.
@pytest.mark.parametrize("platforms", [[Platform.NUMBER, Platform.SENSOR]])
async def test_settings_timeouts_never_drop_the_link(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    mock_unit: MockModbusUnit,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test only the readings coordinator counts timeouts."""
    coordinator = init_integration.runtime_data.settings
    # Fail only the settings block, so the readings keep the link busy.
    mock_unit.fail_read(0, ModbusTimeoutError())
    for _ in range(TIMEOUTS_BEFORE_RECONNECT):
        freezer.tick(SETTINGS_INTERVAL + timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_connection.connected
    assert not coordinator.last_update_success


def _unpaired_probe_image() -> dict[str, dict[int, Any]]:
    """A SERENITE unit whose probe 2 is connected but reports no type."""
    image = serenite_image()
    image["discrete"][12] = False
    image["input"][23] = 0
    return image


@pytest.mark.parametrize(
    ("register_image", "entry_data"),
    [(_unpaired_probe_image(), MOCK_SERENITE_DATA)],
    indirect=True,
)
@pytest.mark.parametrize("platforms", [[Platform.NUMBER, Platform.SENSOR]])
async def test_probe_without_a_type_gets_no_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test a connected probe that reports no type is left out."""
    entity_ids = {
        entry.entity_id
        for entry in er.async_entries_for_config_entry(
            entity_registry, init_integration.entry_id
        )
    }
    assert "sensor.domeo_evo_225_fl_probe_1_carbon_dioxide" in entity_ids
    assert not any("probe_2" in entity_id for entity_id in entity_ids)


MODBUS_CONTROL = "binary_sensor.domeo_evo_225_fl_modbus_control_jp1"
JP1_ISSUE = f"modbus_control_off_{MOCK_ENTRY_ID}"


async def test_jp1_open_raises_a_repair_until_closed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_unit: Any,
    mock_unit: MockModbusUnit,
    issue_registry: ir.IssueRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test a repair tells the user to close JP1, and goes once it is closed."""
    mock_unit.discrete[9] = False
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert hass.states.get(MODBUS_CONTROL).state == "off"
    issue = issue_registry.async_get_issue(DOMAIN, JP1_ISSUE)
    assert issue is not None
    assert issue.translation_key == "modbus_control_off"
    assert issue.translation_placeholders == {"name": MOCK_TITLE}

    mock_unit.discrete[9] = True
    await _poll(hass, freezer)
    assert hass.states.get(MODBUS_CONTROL).state == "on"
    assert issue_registry.async_get_issue(DOMAIN, JP1_ISSUE) is None


async def test_unloading_clears_the_jp1_repair(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_unit: Any,
    mock_unit: MockModbusUnit,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test the repair does not outlive its config entry."""
    mock_unit.discrete[9] = False
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert issue_registry.async_get_issue(DOMAIN, JP1_ISSUE) is not None

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert issue_registry.async_get_issue(DOMAIN, JP1_ISSUE) is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_pre_exchanger_temperature_needs_its_probe(
    hass: HomeAssistant, mock_unit: MockModbusUnit, freezer: FrozenDateTimeFactory
) -> None:
    """Test the pre-exchanger reading is unknown while its probe flags a fault."""
    entity_id = "sensor.domeo_evo_225_fl_pre_exchanger_temperature"
    assert hass.states.get(entity_id).state == "unknown"

    mock_unit.discrete[7] = False  # 10008: probe fitted and correct
    await _poll(hass, freezer)
    assert hass.states.get(entity_id).state == "-2.0"


async def test_real_225_fl_rd_with_jp1_open(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_unit: Any,
    mock_unit: MockModbusUnit,
    issue_registry: ir.IssueRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the registers of a real unit, taken from a tester's diagnostics."""
    dump = json.loads(
        (Path(__file__).parent / "fixtures" / "field_225_fl_rd.json").read_text()
    )
    dump.pop("_source")
    mock_unit.load_raw(dump)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(AIRFLOW).state == "105"
    assert hass.states.get(MODBUS_CONTROL).state == "off"
    assert issue_registry.async_get_issue(DOMAIN, JP1_ISSUE) is not None
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, MOCK_ENTRY_ID), MOCK_ENTRY_ID
    )
    assert device is not None
    # It reported 0 as its firmware version.
    assert device.sw_version is None
