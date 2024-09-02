"""Modbus host for Siemens RDF302 Thermostat."""

import asyncio
import logging

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException, ModbusIOException

_LOGGER = logging.getLogger(__name__)


class ModbusHost:
    """Modbus host for Siemens RDF302."""

    def __init__(self, host, port, max_retries=3, retry_delay=0.5) -> None:
        """Initialize the modbus host."""
        self._host = host
        self._port = port
        self._client = AsyncModbusTcpClient(host=host, port=port)
        self._lock = asyncio.Lock()
        self._subscriber_count = 0
        self._max_retry_count = max_retries
        self._retry_delay = retry_delay

    async def async_connect(self):
        """Connect to the modbus host."""
        if not self._client.connected:
            await self._client.connect()

    async def async_disconnect(self):
        """Disconnect from the modbus host."""
        if self._client.connected:
            await self._client.close()

    def add_subscriber(self):
        """Add a subscriber."""
        self._subscriber_count += 1

    def get_subscriber_count(self):
        """Get the subscriber count."""
        return self._subscriber_count

    def remove_subscriber(self):
        """Remove a subscriber."""
        self._subscriber_count -= 1
        if self._subscriber_count == 0:
            task = asyncio.create_task(self.async_disconnect())
            # TODO: destroy host instance if no subscribers

    # NOTE: This method  will try to read the registers 'self._max_retries' times
    async def async_read_holding_registers(self, unit_id, address, count):
        """Read holding registers."""
        async with self._lock:
            for attempt in range(self._max_retry_count):
                await self.async_connect()
                result = await self._client.read_holding_registers(
                    address, count, unit_id
                )
                if not result.isError() and len(result.registers) == count:
                    return result.registers

                if attempt < self._max_retry_count - 1:
                    _LOGGER.warning(
                        "Modbus error reading holding registers at address %s, retrying",
                        address,
                    )
                    await asyncio.sleep(self._retry_delay)

            _LOGGER.error(
                "Modbus error reading holding registers at address %s, retries exhausted",
                address,
            )
            return None

    async def async_read_input_registers(self, unit_id, address, count):
        """Read input registers."""
        async with self._lock:
            for attempt in range(self._max_retry_count):
                await self.async_connect()
                result = await self._client.read_input_registers(
                    address, count, unit_id
                )
                if not result.isError() and len(result.registers) == count:
                    return result.registers

                if attempt < self._max_retry_count - 1:
                    _LOGGER.warning(
                        "Modbus error reading input registers at address %s, retrying",
                        address,
                    )
                    await asyncio.sleep(self._retry_delay)
            _LOGGER.error(
                "Modbus error reading input registers at address %s, retries exhausted",
                address,
            )

            return None

    async def async_read_coil(self, unit_id, address):
        """Read coils."""
        async with self._lock:
            await self.async_connect()
            result = await self._client.read_coils(address, 1, unit_id)
            if not result.isError():
                return result.bits[0]
            return None

    async def async_read_coils(self, unit_id, address, count):
        """Read coils."""
        async with self._lock:
            for attempts in range(self._max_retry_count):
                await self.async_connect()
                result = await self._client.read_coils(address, count, unit_id)
                if not result.isError() and len(result.bits) == count:
                    return result.bits

                if attempts < self._max_retry_count - 1:
                    _LOGGER.warning(
                        "Modbus error reading coils at address %s, retrying", address
                    )
                    await asyncio.sleep(self._retry_delay)

            _LOGGER.error(
                "Modbus error reading coils at address %s, retries exhausted", address
            )
            return None

    async def async_write_register(self, unit_id, address, value) -> bool:
        """Write a single register."""
        async with self._lock:
            try:
                await self.async_connect()
                result = await self._client.write_register(address, value, unit_id)
                if not result.isError():
                    return True

                _LOGGER.error(
                    "Modbus error writing register at address %s, retries exhausted",
                    address,
                )
            except ModbusIOException as e:
                _LOGGER.error(
                    "Modbus I/O error writing register at address %s: %s",
                    address,
                    str(e),
                )
                return False
            except ModbusException as e:
                _LOGGER.error(
                    "Modbus error writing register at address %s: %s",
                    address,
                    str(e),
                )
                return False
            except Exception as e:
                _LOGGER.error(
                    "Unknown error writing register at address %s: %s",
                    address,
                    str(e),
                )
                return False

    async def async_write_coil(self, unit_id, address, value):
        """Write a single coil."""
        async with self._lock:
            try:
                await self.async_connect()
                result = await self._client.write_coil(address, value, unit_id)

                if not result.isError():
                    return True

                _LOGGER.error(
                    "Modbus error writing coil at address %s",
                    address,
                )

            except ModbusIOException as e:
                _LOGGER.error(
                    "Modbus I/O error writing coil at address %s: %s",
                    address,
                    str(e),
                )
                return False
            except ModbusException as e:
                _LOGGER.error(
                    "Modbus error writing coil at address %s: %s",
                    address,
                    str(e),
                )
                return False
            except Exception as e:
                _LOGGER.error(
                    "Unknown error writing coil at address %s: %s",
                    address,
                    str(e),
                )
                return False
