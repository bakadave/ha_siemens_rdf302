"""Initialize the module."""

import logging

from homeassistant.config_entries import ConfigEntry  # Used for config flow setup
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PORT, DOMAIN, PLATFORMS
from .modbus_host import ModbusHost

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Siemens RDF302 from config flow."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    host_key = f"{host}:{port}"

    # Create a new ModbusHost instance if it doesn't exist
    if host_key not in hass.data[DOMAIN]:
        hass.data[DOMAIN][host_key] = ModbusHost(host, port)
        _LOGGER.debug("Created ModbusHost instance for %s", host_key)
    else:
        _LOGGER.debug("Using existing ModbusHost instance for %s", host_key)

    # Increase the subscriber count
    hass.data[DOMAIN][host_key].add_subscriber()

    # Store the ModbusHost reference in the entry data for the climate entity to use
    hass.data[entry.entry_id] = hass.data[DOMAIN][host_key]

    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    host_key = f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        modbus_host = hass.data[DOMAIN][host_key]
        modbus_host.remove_subscriber()
        if modbus_host.get_subscriber_count() == 0:
            await modbus_host.async_disconnect()
            del hass.data[DOMAIN][host_key]
        del hass.data[entry.entry_id]

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Siemens RDF302 component."""
    hass.data[DOMAIN] = {}
    return True
