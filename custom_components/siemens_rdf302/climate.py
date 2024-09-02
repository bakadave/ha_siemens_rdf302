"""Support for Siemens RDF302 units."""

import logging

from homeassistant.components.climate import (
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRECISION_TENTHS, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_NAME,
    CONF_UNIT_ID,
    DOMAIN,
    REGISTER_CURRENT_TEMP_RO,
    REGISTER_FAN_SPEED_RO,
    REGISTER_FAN_SPEED_RW,
    REGISTER_HEAT_COOL_RW,
    REGISTER_PRESET_RO,
    REGISTER_PRESET_RW,
    REGISTER_SETPOINT_TEMP_RO,
    REGISTER_SETPOINT_TEMP_RW,
)

_LOGGER = logging.getLogger(__name__)

CALL_TYPE_WRITE_REGISTER = "write_register"
CALL_TYPE_WRITE_COIL = "write_coil"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SiemensRDF302 climate entity from a config entry."""
    modbus_host = hass.data[entry.entry_id]
    unit_id = entry.data[CONF_UNIT_ID]
    name = entry.data[CONF_NAME]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, unit_id)},
        name=name,
        manufacturer="Siemens",
        model="RDF302",
    )

    device = SiemensRDF302(name, modbus_host, unit_id, device_info)
    async_add_entities([device], update_before_add=True)


class SiemensRDF302(ClimateEntity):
    """Representation of a Siemens RDF302 Thermostat climate entity."""

    def __init__(self, name, modbus_host, unit_id, device_info) -> None:
        """Initialize the climate entity."""
        self._name = name
        self._modbus = modbus_host
        self._unit_id = unit_id
        self._unique_id = f"{name}:{unit_id}"

        self._hvac_mode = HVACMode.OFF
        self._target_temperature = None
        self._current_temperature = None
        self._fan_mode = "off"
        self._attr_preset_mode = PRESET_NONE
        self._attr_device_info = device_info
        _LOGGER.debug(
            "Creating ModbusThermostat entity: %s, unit ID: %s", name, unit_id
        )

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [
            HVACMode.COOL,
            HVACMode.HEAT,
        ]

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return self._attr_preset_modes

    @property
    def preset_modes(self):
        """Return the list of available preset modes."""
        return [
            PRESET_COMFORT,
            PRESET_ECO,
            PRESET_AWAY,
        ]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temperature

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return ["low", "medium", "high", "off"]

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        return self._fan_mode

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 5

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 40

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return PRECISION_TENTHS

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
        )

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        mode_value = {
            HVACMode.COOL: 0,
            HVACMode.HEAT: 1,
        }.get(hvac_mode, 0)

        _LOGGER.debug("Setting HVAC mode to %s", hvac_mode)

        if self._hvac_mode != hvac_mode:
            success = await self._modbus.async_write_register(
                self._unit_id, REGISTER_HEAT_COOL_RW, int(mode_value)
            )
            if success:
                self._hvac_mode = hvac_mode
            else:
                _LOGGER.error("Error setting HVAC mode to %s", hvac_mode)

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""
        mode_value = {
            PRESET_COMFORT: 1,
            PRESET_ECO: 3,
            PRESET_AWAY: 4,
        }.get(preset_mode, PRESET_AWAY)

        _LOGGER.debug("Setting preset mode to %s", preset_mode)
        success = await self._modbus.async_write_register(
            self._unit_id, REGISTER_PRESET_RW, mode_value
        )
        if success:
            self._attr_preset_modes = preset_mode
        else:
            _LOGGER.error("Error setting preset mode to %s", preset_mode)

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            _LOGGER.debug("Setting target temperature to %s", temperature)
            temp_value = temperature * 50  # Multiply by 50 as per specification
            success = await self._modbus.async_write_register(
                self._unit_id, REGISTER_SETPOINT_TEMP_RW, int(temp_value)
            )
            if success:
                self._target_temperature = temperature
            else:
                _LOGGER.error("Error setting target temperature to %s", temperature)

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        fan_value = {"auto": 0, "low": 33, "medium": 66, "high": 100}.get(fan_mode, 0)

        _LOGGER.debug("Setting fan mode to %s", fan_mode)
        success = await self._modbus.async_write_register(
            self._unit_id, REGISTER_FAN_SPEED_RW, fan_value
        )
        if success:
            self._fan_mode = fan_mode
        else:
            _LOGGER.error("Error setting fan mode to %s", fan_mode)

    async def async_update(self):
        """Update the state of the climate entity."""
        try:
            # Read current temperature
            current_temp = await self._modbus.async_read_input_registers(
                self._unit_id, REGISTER_CURRENT_TEMP_RO, 1
            )
            if current_temp is not None and len(current_temp) == 1:
                temp_C = current_temp[0] / 50
                self._current_temperature = temp_C
            else:
                _LOGGER.warning("Received invalid data for current temperature")

            # Read target temperature
            target_temp = await self._modbus.async_read_input_registers(
                self._unit_id, REGISTER_SETPOINT_TEMP_RO, 1
            )
            if target_temp is not None and len(target_temp) == 1:
                temp_C = target_temp[0] / 50
                self._target_temperature = temp_C
            else:
                _LOGGER.warning("Received invalid data for target temperature")

            # Read HVAC mode
            mode = await self._modbus.async_read_holding_registers(
                self._unit_id, REGISTER_HEAT_COOL_RW, 1
            )
            if mode is not None and len(mode) == 1:
                self._hvac_mode = self._value_to_hvac_mode(mode[0])
            else:
                _LOGGER.error("No response to reading HVAC mode or power state")

            # Read fan mode
            fan_speed = await self._modbus.async_read_input_registers(
                self._unit_id, REGISTER_FAN_SPEED_RO, 1
            )
            if fan_speed is not None and len(fan_speed) == 1:
                self._fan_mode = self._value_to_fan_mode(fan_speed[0])
            else:
                _LOGGER.error("Received invalid data for fan mode")

            # Read preset mode
            preset = await self._modbus.async_read_input_registers(
                self._unit_id, REGISTER_PRESET_RO, 1
            )
            if preset is not None and len(preset) == 1:
                self._attr_preset_modes = self._value_to_preset_mode(preset[0])
            else:
                _LOGGER.error("Received invalid data for preset mode")

        except Exception as e:
            _LOGGER.error("Error updating Siemens RDF302 Thermostat state: %s", str(e))

        finally:
            # Notify Home Assistant of the updated state
            _LOGGER.debug(
                "Updating Siemens RDF302 state: temp=%s, target=%s, mode=%s, fan=%s, preset: %s",
                self._current_temperature,
                self._target_temperature,
                self._hvac_mode,
                self._fan_mode,
                self._attr_preset_modes,
            )

    def _value_to_hvac_mode(self, mode):
        return {
            0: HVACMode.COOL,
            1: HVACMode.HEAT,
        }.get(mode, HVACMode.HEAT)

    def _value_to_fan_mode(self, value):
        return {0: "off", 33: "low", 66: "medium", 100: "high"}.get(value, "off")

    def _value_to_preset_mode(self, value):
        return {1: PRESET_COMFORT, 3: PRESET_ECO, 4: PRESET_AWAY}.get(
            value, PRESET_AWAY
        )

    def _decode_bcd(self, value):
        return (
            (value & 0xF)
            + ((value >> 4) & 0xF) * 10
            + ((value >> 8) & 0xF) * 100
            + ((value >> 12) & 0xF) * 1000
        )
