"""Config flow for Siemens RDF302 Thermostat integration."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import (
    CONF_HOST,
    CONF_NAME,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_UNIT_ID,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

user_schema = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=502): int,
        vol.Required(CONF_UNIT_ID): int,
        # TODO: unique_id, entity_id, etc.
    }
)

options_schema = vol.Schema(
    {
        vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): int,
    }
)


class SiemensRDF302ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow to add Siemens RDF302 Thermostat integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._hosts = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate input here if needed
            # TODO: check host valid, etc.
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            unit_id = user_input[CONF_UNIT_ID]

            unique_id = f"{host}:{port}:{unit_id}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_UNIT_ID: unit_id,
                },
            )

        return self.async_show_form(
            step_id="user", data_schema=user_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SiemensRDF302OptionsFlow(config_entry)


class SiemensRDF302OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Siemens RDF302 Thermostat."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema, self.config_entry.options
            ),
        )
