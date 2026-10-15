"""Platform stub for Roborock Cloud Only."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntityPlatform

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntityPlatform,
) -> None:
    """Set up platform entities."""
    async_add_entities([])