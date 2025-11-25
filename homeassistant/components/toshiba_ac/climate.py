"""Support for Toshiba AC climate entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    SWING_OFF,
    SWING_ON,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import ToshibaAcDevice, ToshibaAcState
from .const import DOMAIN, MAX_TEMP, MIN_TEMP
from .coordinator import ToshibaAcConfigEntry, ToshibaAcCoordinator
from .entity import ToshibaAcEntity

_LOGGER = logging.getLogger(__name__)

# Map Home Assistant HVAC modes to Toshiba modes
HA_TO_TOSHIBA_MODE = {
    HVACMode.OFF: "off",
    HVACMode.HEAT: "heat",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan_only",
}

TOSHIBA_TO_HA_MODE = {
    "heat": HVACMode.HEAT,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "fan_only": HVACMode.FAN_ONLY,
}

# Map Home Assistant fan modes to Toshiba fan modes
HA_TO_TOSHIBA_FAN = {
    FAN_AUTO: "auto",
    FAN_HIGH: "high",
    FAN_LOW: "low",
}

TOSHIBA_TO_HA_FAN = {
    "auto": FAN_AUTO,
    "high": FAN_HIGH,
    "low": FAN_LOW,
}

# Map swing modes
SWING_AUTO = "auto"
SWING_DOWN = "down"

HA_TO_TOSHIBA_SWING = {
    SWING_OFF: "off",
    SWING_ON: "auto",
    SWING_AUTO: "auto",
    SWING_DOWN: "down",
}

TOSHIBA_TO_HA_SWING = {
    "off": SWING_OFF,
    "auto": SWING_ON,
    "down": SWING_DOWN,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ToshibaAcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Toshiba AC climate entities."""
    coordinator = entry.runtime_data

    async_add_entities(
        ToshibaAcClimate(coordinator, device)
        for device in coordinator.devices.values()
    )


class ToshibaAcClimate(ToshibaAcEntity, ClimateEntity):
    """Represent a Toshiba AC climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_name = None
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_HIGH, FAN_LOW]
    _attr_swing_modes = [SWING_OFF, SWING_ON, SWING_DOWN]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        coordinator: ToshibaAcCoordinator,
        device: ToshibaAcDevice,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, device)
        self._attr_unique_id = device.device_unique_id
        self._set_attr()

    @property
    def _state(self) -> ToshibaAcState | None:
        """Return the current state from coordinator."""
        if (
            self.coordinator.data is None
            or self.coordinator_context not in self.coordinator.data
        ):
            return None
        return self.coordinator.data[self.coordinator_context]

    def _set_attr(self) -> None:
        """Set entity attributes from state."""
        state = self._state
        if state is None:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_current_temperature = None
            self._attr_target_temperature = None
            self._attr_fan_mode = FAN_AUTO
            self._attr_swing_mode = SWING_OFF
            return

        # Set HVAC mode
        if not state.is_on:
            self._attr_hvac_mode = HVACMode.OFF
        else:
            self._attr_hvac_mode = TOSHIBA_TO_HA_MODE.get(state.mode, HVACMode.OFF)

        # Set temperatures
        self._attr_target_temperature = state.temperature

        # Set fan mode
        self._attr_fan_mode = TOSHIBA_TO_HA_FAN.get(state.fan_speed, FAN_AUTO)

        # Set swing mode
        self._attr_swing_mode = TOSHIBA_TO_HA_SWING.get(state.swing, SWING_OFF)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._set_attr()
        super()._handle_coordinator_update()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        state = self._state
        if state is None:
            return

        if hvac_mode == HVACMode.OFF:
            await self.coordinator.client.async_send_command(
                self._device,
                state,
                is_on=False,
            )
        else:
            toshiba_mode = HA_TO_TOSHIBA_MODE.get(hvac_mode)
            if toshiba_mode:
                await self.coordinator.client.async_send_command(
                    self._device,
                    state,
                    is_on=True,
                    mode=toshiba_mode,
                )

        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        state = self._state
        if state is None:
            return

        await self.coordinator.client.async_send_command(
            self._device,
            state,
            temperature=int(temperature),
        )
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        state = self._state
        if state is None:
            return

        toshiba_fan = HA_TO_TOSHIBA_FAN.get(fan_mode)
        if toshiba_fan:
            await self.coordinator.client.async_send_command(
                self._device,
                state,
                fan_speed=toshiba_fan,
            )
            await self.coordinator.async_request_refresh()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set swing mode."""
        state = self._state
        if state is None:
            return

        toshiba_swing = HA_TO_TOSHIBA_SWING.get(swing_mode)
        if toshiba_swing:
            await self.coordinator.client.async_send_command(
                self._device,
                state,
                swing=toshiba_swing,
            )
            await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        state = self._state
        if state is None:
            return

        await self.coordinator.client.async_send_command(
            self._device,
            state,
            is_on=True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        state = self._state
        if state is None:
            return

        await self.coordinator.client.async_send_command(
            self._device,
            state,
            is_on=False,
        )
        await self.coordinator.async_request_refresh()
