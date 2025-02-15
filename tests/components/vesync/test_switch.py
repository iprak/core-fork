"""Tests for the switch module."""

import pytest
import requests_mock
from syrupy import SnapshotAssertion

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .common import (
    ALL_DEVICE_NAMES,
    ENTITY_HUMIDIFIER_300S_AUTOMATIC_OFF_SWITCH,
    mock_devices_response,
)

from tests.common import MockConfigEntry


@pytest.mark.parametrize("device_name", ALL_DEVICE_NAMES)
async def test_switch_state(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    requests_mock: requests_mock.Mocker,
    device_name: str,
) -> None:
    """Test the resulting setup state is as expected for the platform."""

    # Configure the API devices call for device_name
    mock_devices_response(requests_mock, device_name)

    # setup platform - only including the named device
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check device registry
    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    assert devices == snapshot(name="devices")

    # Check entity registry
    entities = [
        entity
        for entity in er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        if entity.domain == SWITCH_DOMAIN
    ]
    assert entities == snapshot(name="entities")

    # Check states
    for entity in entities:
        assert hass.states.get(entity.entity_id) == snapshot(name=entity.entity_id)


@pytest.mark.parametrize(
    ("install_humidifier_device", "service_name", "expected_setter"),
    [
        ("humidifier_300s", SERVICE_TURN_OFF, "automatic_stop_off"),
        ("humidifier_300s", SERVICE_TURN_ON, "automatic_stop_on"),
    ],
    indirect=["install_humidifier_device"],
)
async def test_set_automatic_on_off(
    hass: HomeAssistant,
    manager,
    humidifier_300s,
    install_humidifier_device,
    service_name,
    expected_setter,
) -> None:
    """Test set of automatic on."""

    await hass.services.async_call(
        SWITCH_DOMAIN,
        service_name,
        {
            ATTR_ENTITY_ID: ENTITY_HUMIDIFIER_300S_AUTOMATIC_OFF_SWITCH,
        },
        blocking=True,
    )

    # Assert that setter was invoked
    getattr(humidifier_300s, expected_setter).assert_called_once()
