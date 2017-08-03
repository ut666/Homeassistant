"""
Demo platform that offers a fake climate device.
For more details about this platform, please refer to the documentation
https://home-assistant.io/components/demo/
"""

import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import (ClimateDevice, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW)
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE, EVENT_HOMEASSISTANT_START)

from lennox_api import Lennox_iComfort_API

_LOGGER = logging.getLogger(__name__)

CONF_SYSTEM = 'system'
CONF_ZONE = 'zone'

DEFAULT_SYSTEM = 0
DEFAULT_ZONE = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_SYSTEM, default=DEFAULT_SYSTEM): vol.Coerce(int),
    vol.Optional(CONF_ZONE, default=DEFAULT_ZONE): vol.Coerce(int),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
        """Setup the platform."""
        username = config.get(CONF_USERNAME)
        password = config.get(CONF_PASSWORD)
        system = config.get(CONF_SYSTEM)
        zone = config.get(CONF_ZONE)

        """Setup the api"""
        api = Lennox_iComfort_API(username, password, system, zone)
        climate = [LennoxClimate("lennox", api)]
        add_devices(climate)

class LennoxClimate(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, name, api):
        """Initialize the climate device."""
        self._name = name
        self._api = api
        self._unit_of_measurement = TEMP_CELSIUS;

        self._current_state = "Unknown"
        self._current_temperature = self._api._temperature
        self._current_humidity = self._api._humidity
        self._current_program = "Unknown"
        self._current_fan_mode = "Uknown"
        self._current_operation_mode = "Unkown"
       
        self._target_temperature_high = self._api._coolto
        self._target_temperature_low = self._api._heatto

        self._program_list = self._api._program_list
        self._fan_list = self._api._fanmode_list      
        self._operation_list = self._api._opmode_list

        self._away = self._api._awaymode
        

    def update(self):
        """Get the latest data for the states."""
        if self._api is not None:
            """Fetch the latest data"""
            self._api.get()
            
            """set our sensor values"""
            self._current_temperature = self._api._temperature
            self._current_humidity = self._api._humidity
            self._target_temperature_high = self._api._coolto
            self._target_temperature_low = self._api._heatto
            self._away = self._api._awaymode
            
            """Create a textual representations"""
            self._current_operation_mode = "Unknown"
            if self._api._opmode == 0:
                self._current_operation_mode = 'Off';
            elif self._api._opmode == 1:
                self._current_operation_mode = 'Heat only';
            elif self._api._opmode == 2:
                self._current_operation_mode = 'Cool only';
            elif self._api._opmode == 3:
                self._current_operation_mode = 'Heat & Cool';                
            self._current_fan_mode = "Unknown"
            """Create a textual representations"""
            if self._api._fanmode == 0:
                self._current_fan_mode = 'Auto';
            elif self._api._fanmode == 1:
                self._current_fan_mode = 'On';
            elif self._api._fanmode == 2:
                self._current_fan_mode = 'Circulate';
            """Create a textual representation"""
            if self._api._state == 0:
                self._current_state = 'Idle';
            elif self._api._state == 1:
                self._current_state = 'Heating';
            elif self._api._state == 2:
                self._current_state = 'Cooling';
            
    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        # Move these to Thermostat Device and make them global
        return {
        "current_humidity": self._current_humidity,
        "status": self._current_state,
        "program": self._current_program,
        "away_mode": self._away
        }
        
    @property
    def state(self):
        return self._current_state
            
    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement
        
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.current_operation == 'Heat & Cool':
            return None
        if self.current_operation == 'Heat only':
            return int(self._api._heatto)
        elif self.current_operation == 'Cool only':
            return int(self._api._coolto)
        return None
    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self._target_temperature_low

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity

    @property
    def current_operation(self):
        self._current_operation_mode = "Unknown"
        """Create a textual representation"""
        if self._api._opmode == 0:
            self._current_operation_mode = 'Off';
        elif self._api._opmode == 1:
            self._current_operation_mode = 'Heat only';
        elif self._api._opmode == 2:
            self._current_operation_mode = 'Cool only';
        elif self._api._opmode == 3:
            self._current_operation_mode = 'Heat & Cool';   
        """Return the state of the sensor."""
        return self._current_operation_mode
        
    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._away

    @property
    def current_fan_mode(self):
        self._current_fan_mode = "Unknown"
        """Create a textual representation"""
        if self._api._fanmode == 0:
            self._current_fan_mode = 'Auto';
        elif self._api._fanmode == 1:
            self._current_fan_mode = 'On';
        elif self._api._fanmode == 2:
            self._current_fan_mode = 'Circulate';
        """Return the state of the sensor."""
        return self._current_fan_mode
        
    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._fan_list
        
    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        self._target_temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        self._target_temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temp = kwargs.get(ATTR_TEMPERATURE)
        if self.current_operation == 'Heat & Cool' and self._target_temperature_low is not None \
           and self._target_temperature_high is not None:
            self._api._heatto = self._target_temperature_low
            self._api._coolto = self._target_temperature_high
        elif temp is not None:
            if self.current_operation == 'Heat only':
                self._api._heatto = temp
                self._api._coolto = temp + 10
            elif self.current_operation == 'Cool only':
                self._api._heatto = temp - 10
                self._api._coolto = temp           
        self._api.set()
        self.schedule_update_ha_state()

    def set_fan_mode(self, fan):
        """Set new the new fan mode."""
        self._fan = fan
        """Retrieve from textual representation"""
        if self._fan == 'Auto':
            self._api._fanmode = 0;
        elif self._fan == 'On':
            self._api._fanmode = 1;
        elif self._fan == 'Circulate':
            self._api._fanmode = 2;
        self._api.set()
        self.schedule_update_ha_state()

    def set_current_operation_mode(self, operation_mode):
        """Set new target temperature."""
        self._current_operation_mode = operation_mode
        """Retrieve from textual representation"""
        if self._current_operation_mode == 'Off':
            self._api._opmode = 0;
        elif self._current_operation_mode == 'Heat only':
            self._api._opmode = 1;
        elif self._current_operation_mode == 'Cool only':
            self._api._opmode = 2;
        elif self._current_operation_mode == 'Heat & Cool':
            self._api._opmode = 3;            
        self._api.set()
        self.schedule_update_ha_state()
                    
    def turn_away_mode_on(self):
        """Turn away mode on."""
        self._away = 1
        self._api._awaymode = self.away
        self._api.set()
        self.schedule_update_ha_state()

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self._away = 0
        self._api._awaymode = self.away
        self._api.set()
        self.schedule_update_ha_state()

