"""Snapshot tests of every DOMEO EVO entity."""

from typing import Any

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from . import MOCK_SERENITE_DATA, MOCK_TCP_DATA, serenite_image
from .register_images import FACTORY_225_FL

UNITS = pytest.mark.parametrize(
    ("register_image", "entry_data"),
    [
        pytest.param(FACTORY_225_FL, MOCK_TCP_DATA, id="fl"),
        pytest.param(serenite_image(), MOCK_SERENITE_DATA, id="serenite"),
    ],
    indirect=True,
)


@UNITS
@pytest.mark.parametrize(
    "platforms",
    [
        pytest.param([platform], id=platform.value)
        for platform in (
            Platform.BINARY_SENSOR,
            Platform.BUTTON,
            Platform.NUMBER,
            Platform.SELECT,
            Platform.SENSOR,
            Platform.SWITCH,
        )
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    register_image: dict[str, dict[int, Any]],
) -> None:
    """Test the entities a unit gets, and their states."""
    await snapshot_platform(hass, entity_registry, snapshot, init_integration.entry_id)
