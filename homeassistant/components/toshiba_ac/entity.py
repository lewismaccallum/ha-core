"""Toshiba AC base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ToshibaAcDevice
from .const import DOMAIN
from .coordinator import ToshibaAcCoordinator


class ToshibaAcEntity(CoordinatorEntity[ToshibaAcCoordinator]):
    """Base entity for Toshiba AC devices."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ToshibaAcCoordinator,
        device: ToshibaAcDevice,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, context=device.ac_id)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_unique_id)},
            name=device.name,
            manufacturer="Toshiba",
            model=device.model,
            sw_version=device.firmware_version,
        )
        self._device = device

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator_context in self.coordinator.data
        )
