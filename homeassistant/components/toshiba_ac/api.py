"""API client for Toshiba AC."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from .const import (
    API_AC_MAPPING_ENDPOINT,
    API_AC_STATE_ENDPOINT,
    API_BASE_URL,
    API_LOGIN_ENDPOINT,
    API_TIMEOUT,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    MAX_TEMP,
    MIN_TEMP,
    MODE_COOL,
    MODE_DRY,
    MODE_FAN_ONLY,
    MODE_HEAT,
    PAYLOAD_FAN_POS,
    PAYLOAD_MODE_POS,
    PAYLOAD_POWER_POS,
    PAYLOAD_SELF_CLEAN_POS,
    PAYLOAD_STATE_POS,
    PAYLOAD_SWING_POS,
    PAYLOAD_TEMP_POS,
    POWER_100,
    POWER_50,
    POWER_75,
    POWER_NONE,
    SELF_CLEAN_OFF,
    SELF_CLEAN_ON,
    STATE_OFF,
    STATE_ON,
    SWING_AUTO,
    SWING_DOWN,
    SWING_OFF,
)

_LOGGER = logging.getLogger(__name__)


class ToshibaAcAuthError(Exception):
    """Exception for authentication errors."""


class ToshibaAcConnectionError(Exception):
    """Exception for connection errors."""


class ToshibaAcApiError(Exception):
    """Exception for API errors."""


@dataclass
class ToshibaAcDevice:
    """Represents a Toshiba AC device."""

    ac_id: str
    name: str
    device_unique_id: str
    model: str | None = None
    firmware_version: str | None = None


@dataclass
class ToshibaAcState:
    """Represents the state of a Toshiba AC device."""

    ac_id: str
    is_on: bool
    mode: str  # heat, cool, dry, fan_only
    temperature: int
    fan_speed: str  # auto, high, low
    swing: str  # off, auto, down
    power_level: str  # none, 50, 75, 100
    self_cleaning: bool
    raw_payload: str  # Store raw payload for preserving unknown bytes


class ToshibaAcClient:
    """Client for the Toshiba AC API."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token: str | None = None
        self._consumer_id: str | None = None
        self._consumer_master_id: str | None = None

    @property
    def access_token(self) -> str | None:
        """Return the access token."""
        return self._access_token

    @property
    def consumer_id(self) -> str | None:
        """Return the consumer ID."""
        return self._consumer_id

    @property
    def consumer_master_id(self) -> str | None:
        """Return the consumer master ID."""
        return self._consumer_master_id

    def set_credentials(
        self,
        access_token: str,
        consumer_id: str,
        consumer_master_id: str,
    ) -> None:
        """Set stored credentials."""
        self._access_token = access_token
        self._consumer_id = consumer_id
        self._consumer_master_id = consumer_master_id

    async def async_login(
        self,
        username: str,
        password: str,
        brand_id: str,
    ) -> dict[str, str]:
        """Authenticate with the Toshiba API."""
        url = f"{API_BASE_URL}{API_LOGIN_ENDPOINT}"
        payload = {
            "Username": username,
            "Password": password,
            "BrandId": brand_id,
        }

        timeout = ClientTimeout(total=API_TIMEOUT)
        try:
            async with self._session.post(
                url, json=payload, timeout=timeout
            ) as response:
                if response.status == 401:
                    raise ToshibaAcAuthError("Invalid credentials")
                if response.status != 200:
                    raise ToshibaAcApiError(f"API error: {response.status}")

                data = await response.json()
        except TimeoutError as err:
            raise ToshibaAcConnectionError("Connection timeout") from err
        except ToshibaAcAuthError:
            raise
        except ToshibaAcApiError:
            raise
        except Exception as err:
            raise ToshibaAcConnectionError(f"Connection error: {err}") from err

        if "ResObj" not in data or data["ResObj"] is None:
            if data.get("IsSuccess") is False:
                raise ToshibaAcAuthError(
                    data.get("Message", "Authentication failed")
                )
            raise ToshibaAcApiError("Invalid response from API")

        res_obj = data["ResObj"]
        self._access_token = res_obj.get("accessToken")
        self._consumer_id = res_obj.get("consumerId")
        self._consumer_master_id = res_obj.get("consumerMasterId")

        if not self._access_token:
            raise ToshibaAcAuthError("No access token received")

        return {
            "access_token": self._access_token,
            "consumer_id": self._consumer_id,
            "consumer_master_id": self._consumer_master_id,
        }

    async def async_get_devices(self) -> list[ToshibaAcDevice]:
        """Get all AC devices associated with the account."""
        if not self._access_token or not self._consumer_id:
            raise ToshibaAcAuthError("Not authenticated")

        url = f"{API_BASE_URL}{API_AC_MAPPING_ENDPOINT}"
        params = {"consumerId": self._consumer_id}
        headers = {"Authorization": f"Bearer {self._access_token}"}

        timeout = ClientTimeout(total=API_TIMEOUT)
        try:
            async with self._session.get(
                url, params=params, headers=headers, timeout=timeout
            ) as response:
                if response.status == 401:
                    raise ToshibaAcAuthError("Token expired or invalid")
                if response.status != 200:
                    raise ToshibaAcApiError(f"API error: {response.status}")

                data = await response.json()
        except TimeoutError as err:
            raise ToshibaAcConnectionError("Connection timeout") from err
        except ToshibaAcAuthError:
            raise
        except ToshibaAcApiError:
            raise
        except Exception as err:
            raise ToshibaAcConnectionError(f"Connection error: {err}") from err

        devices: list[ToshibaAcDevice] = []
        res_obj = data.get("ResObj", [])
        if not isinstance(res_obj, list):
            res_obj = [res_obj] if res_obj else []

        for item in res_obj:
            ac_id = item.get("ACId") or item.get("acId")
            name = item.get("ACName") or item.get("acName") or f"AC {ac_id}"
            device_unique_id = item.get("ACDeviceUniqueId") or item.get(
                "acDeviceUniqueId", ac_id
            )
            model = item.get("ModelName") or item.get("modelName")
            firmware = item.get("FirmwareVersion") or item.get("firmwareVersion")

            if ac_id:
                devices.append(
                    ToshibaAcDevice(
                        ac_id=str(ac_id),
                        name=name,
                        device_unique_id=str(device_unique_id),
                        model=model,
                        firmware_version=firmware,
                    )
                )

        return devices

    async def async_get_device_state(self, ac_id: str) -> ToshibaAcState:
        """Get the current state of a specific AC device."""
        if not self._access_token:
            raise ToshibaAcAuthError("Not authenticated")

        url = f"{API_BASE_URL}{API_AC_STATE_ENDPOINT}"
        params = {"ACId": ac_id}
        headers = {"Authorization": f"Bearer {self._access_token}"}

        timeout = ClientTimeout(total=API_TIMEOUT)
        try:
            async with self._session.get(
                url, params=params, headers=headers, timeout=timeout
            ) as response:
                if response.status == 401:
                    raise ToshibaAcAuthError("Token expired or invalid")
                if response.status != 200:
                    raise ToshibaAcApiError(f"API error: {response.status}")

                data = await response.json()
        except TimeoutError as err:
            raise ToshibaAcConnectionError("Connection timeout") from err
        except ToshibaAcAuthError:
            raise
        except ToshibaAcApiError:
            raise
        except Exception as err:
            raise ToshibaAcConnectionError(f"Connection error: {err}") from err

        res_obj = data.get("ResObj", {})
        if not res_obj:
            raise ToshibaAcApiError(f"No state data for device {ac_id}")

        # Get raw payload from response
        raw_payload = res_obj.get("ACStateData") or res_obj.get(
            "acStateData", ""
        )

        return self._parse_state(ac_id, raw_payload)

    def _parse_state(self, ac_id: str, raw_payload: str) -> ToshibaAcState:
        """Parse the hex payload into a state object."""
        # Default state if payload is empty or too short
        if not raw_payload or len(raw_payload) < 12:
            return ToshibaAcState(
                ac_id=ac_id,
                is_on=False,
                mode="cool",
                temperature=22,
                fan_speed="auto",
                swing="off",
                power_level="none",
                self_cleaning=False,
                raw_payload=raw_payload or "",
            )

        # Parse each byte from hex string (2 chars = 1 byte)
        state_hex = raw_payload[PAYLOAD_STATE_POS * 2 : PAYLOAD_STATE_POS * 2 + 2]
        mode_hex = raw_payload[PAYLOAD_MODE_POS * 2 : PAYLOAD_MODE_POS * 2 + 2]
        temp_hex = raw_payload[PAYLOAD_TEMP_POS * 2 : PAYLOAD_TEMP_POS * 2 + 2]
        fan_hex = raw_payload[PAYLOAD_FAN_POS * 2 : PAYLOAD_FAN_POS * 2 + 2]
        swing_hex = raw_payload[PAYLOAD_SWING_POS * 2 : PAYLOAD_SWING_POS * 2 + 2]
        power_hex = raw_payload[PAYLOAD_POWER_POS * 2 : PAYLOAD_POWER_POS * 2 + 2]

        # Self-cleaning is at position 14 (bytes 28-29 in hex string)
        self_clean_hex = ""
        if len(raw_payload) >= (PAYLOAD_SELF_CLEAN_POS + 1) * 2:
            self_clean_hex = raw_payload[
                PAYLOAD_SELF_CLEAN_POS * 2 : PAYLOAD_SELF_CLEAN_POS * 2 + 2
            ]

        # Parse state
        is_on = state_hex.upper() == STATE_ON.upper()

        # Parse mode
        mode_map = {
            MODE_HEAT.upper(): "heat",
            MODE_COOL.upper(): "cool",
            MODE_DRY.upper(): "dry",
            MODE_FAN_ONLY.upper(): "fan_only",
        }
        mode = mode_map.get(mode_hex.upper(), "cool")

        # Parse temperature
        try:
            temperature = int(temp_hex, 16)
            temperature = max(MIN_TEMP, min(MAX_TEMP, temperature))
        except ValueError:
            temperature = 22

        # Parse fan speed
        fan_map = {
            FAN_AUTO.upper(): "auto",
            FAN_HIGH.upper(): "high",
            FAN_LOW.upper(): "low",
        }
        fan_speed = fan_map.get(fan_hex.upper(), "auto")

        # Parse swing
        swing_map = {
            SWING_OFF.upper(): "off",
            SWING_AUTO.upper(): "auto",
            SWING_DOWN.upper(): "down",
        }
        swing = swing_map.get(swing_hex.upper(), "off")

        # Parse power level
        power_map = {
            POWER_NONE.upper(): "none",
            POWER_50.upper(): "50",
            POWER_75.upper(): "75",
            POWER_100.upper(): "100",
        }
        power_level = power_map.get(power_hex.upper(), "none")

        # Parse self-cleaning
        self_cleaning = self_clean_hex.upper() == SELF_CLEAN_ON.upper()

        return ToshibaAcState(
            ac_id=ac_id,
            is_on=is_on,
            mode=mode,
            temperature=temperature,
            fan_speed=fan_speed,
            swing=swing,
            power_level=power_level,
            self_cleaning=self_cleaning,
            raw_payload=raw_payload,
        )

    def _build_payload(
        self,
        current_state: ToshibaAcState,
        is_on: bool | None = None,
        mode: str | None = None,
        temperature: int | None = None,
        fan_speed: str | None = None,
        swing: str | None = None,
        power_level: str | None = None,
        self_cleaning: bool | None = None,
    ) -> str:
        """Build a new payload preserving bytes we don't modify."""
        # Start with current payload or create default
        raw = current_state.raw_payload
        if len(raw) < 30:
            # Create a minimal default payload
            raw = "30" + "42" + "16" + "41" + "31" + "00" + "00" * 10

        # Convert to list for easier manipulation
        payload_bytes = [raw[i : i + 2] for i in range(0, len(raw), 2)]

        # Ensure we have enough bytes
        while len(payload_bytes) < 15:
            payload_bytes.append("00")

        # Update state if provided
        if is_on is not None:
            payload_bytes[PAYLOAD_STATE_POS] = STATE_ON if is_on else STATE_OFF

        # Update mode if provided
        if mode is not None:
            mode_map = {
                "heat": MODE_HEAT,
                "cool": MODE_COOL,
                "dry": MODE_DRY,
                "fan_only": MODE_FAN_ONLY,
            }
            payload_bytes[PAYLOAD_MODE_POS] = mode_map.get(mode, MODE_COOL)

        # Update temperature if provided
        if temperature is not None:
            temp_clamped = max(MIN_TEMP, min(MAX_TEMP, temperature))
            payload_bytes[PAYLOAD_TEMP_POS] = f"{temp_clamped:02X}"

        # Update fan speed if provided
        if fan_speed is not None:
            fan_map = {
                "auto": FAN_AUTO,
                "high": FAN_HIGH,
                "low": FAN_LOW,
            }
            payload_bytes[PAYLOAD_FAN_POS] = fan_map.get(fan_speed, FAN_AUTO)

        # Update swing if provided
        if swing is not None:
            swing_map = {
                "off": SWING_OFF,
                "auto": SWING_AUTO,
                "down": SWING_DOWN,
            }
            payload_bytes[PAYLOAD_SWING_POS] = swing_map.get(swing, SWING_OFF)

        # Update power level if provided
        if power_level is not None:
            power_map = {
                "none": POWER_NONE,
                "50": POWER_50,
                "75": POWER_75,
                "100": POWER_100,
            }
            payload_bytes[PAYLOAD_POWER_POS] = power_map.get(power_level, POWER_NONE)

        # Update self-cleaning if provided
        if self_cleaning is not None and len(payload_bytes) > PAYLOAD_SELF_CLEAN_POS:
            payload_bytes[PAYLOAD_SELF_CLEAN_POS] = (
                SELF_CLEAN_ON if self_cleaning else SELF_CLEAN_OFF
            )

        return "".join(payload_bytes)

    async def async_send_command(
        self,
        device: ToshibaAcDevice,
        current_state: ToshibaAcState,
        is_on: bool | None = None,
        mode: str | None = None,
        temperature: int | None = None,
        fan_speed: str | None = None,
        swing: str | None = None,
        power_level: str | None = None,
        self_cleaning: bool | None = None,
    ) -> None:
        """Send a control command to the AC device.

        Note: This is a placeholder for Azure IoT SDK integration.
        The actual implementation would use Azure IoT Hub to send
        the command to the device.
        """
        payload = self._build_payload(
            current_state,
            is_on=is_on,
            mode=mode,
            temperature=temperature,
            fan_speed=fan_speed,
            swing=swing,
            power_level=power_level,
            self_cleaning=self_cleaning,
        )

        # The message structure for Azure IoT SDK
        _message: dict[str, Any] = {
            "sourceId": "homeassistant",
            "messageId": "0000000",
            "targetId": [device.ac_id],
            "cmd": "CMD_FCU_TO_AC",
            "payload": {"data": payload},
            "timeStamp": "0000000",
        }

        # TODO: Implement Azure IoT SDK integration
        # For now, log the command that would be sent
        _LOGGER.debug(
            "Would send command to device %s: payload=%s",
            device.ac_id,
            payload,
        )

        # In a real implementation, this would:
        # 1. Connect to Azure IoT Hub using credentials from the API
        # 2. Send the message to the device
        # 3. Wait for acknowledgment
        # Since Azure IoT SDK integration requires additional setup,
        # this serves as a foundation for future implementation
