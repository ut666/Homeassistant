import requests
import json

import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, TEMP_CELSIUS, EVENT_HOMEASSISTANT_START)

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
    def run_setup(event):
        """Setup the sensor platform."""
        username = config.get(CONF_USERNAME)
        password = config.get(CONF_PASSWORD)
        system = config.get(CONF_SYSTEM)
        zone = config.get(CONF_ZONE)

        """Setup the api"""
        api = Lennox_iComfort_API(username, password, system, zone)

        """Create our sensors"""
        sensors = [Lennox_Status(api)]
        sensors += [Lennox_Temperature(api)]
        sensors += [Lennox_Humidity(api)]
        sensors += [Lennox_HeatTo(api)]
        sensors += [Lennox_CoolTo(api)]
        add_devices(sensors)
    
    # Wait until start event is sent to load this component.
    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, run_setup)

class Lennox_iComfort_API(Entity):
    """Representation of the Lennox iComfort thermostat sensors."""
    
    def __init__(self, username, password, system, zone):
        """Initialize the sensor."""
        self._name = 'lennox'
        self._username = username
        self._password = password
        self._system = system
        self._zone = zone
        self._state = "Unknown"
        self._temperature = "Unknown"
        self._humidity = "Unknown"
        self._heatto = "Unknown"
        self._coolto = "Unknown"
        self.update()
    
    def update(self):
        #Perform our json query
        validateUser = "ValidateUser";
        getSystemsInfo = "GetSystemsInfo";
        gatewaySN  = "?gatewaysn="
        getTStatInfoList = "GetTStatInfoList";
        userID = "?UserId=";
        serviceURL = "https://" + self._username + ":" + self._password + "@services.myicomfort.com/DBAcessService.svc/";
        session_url = serviceURL + validateUser + "?UserName=" + self._username + "&TempUnit=&Cancel_Away=-1";
        s = requests.session();
        cookies = s.get(session_url)
        url = serviceURL + getSystemsInfo + userID + self._username;
        r = s.get(url)
        
        #fetch the requested system
        system = r.json()["Systems"][self._system]

        #fetch our system serial number
        serailNumber = system["Gateway_SN"];

        #now do a getTStatInfoList request
        url = serviceURL + getTStatInfoList + gatewaySN + serailNumber + "&TempUnit=&Cancel_Away=-1";
        resp = s.get(url);

        #fetch the stats for the requested zone
        statInfo = resp.json()['tStatInfo'][self._zone];

        #get our status
        status = statInfo['System_Status'];

        #Create a textual representation
        if status == 0:
            self._state = 'Idle';
        elif status == 1:
            self._state = 'Heating';
        elif status == 2:
            self._state = 'Cooling';
        else:
            self._state = 'Unknown';

        #get our indoor temperature
        self._temperature = statInfo['Indoor_Temp'];

        #get our indoor humidity
        self._humidity = statInfo['Indoor_Humidity'];

        #get our heat to temperature
        self._heatto = statInfo['Heat_Set_Point'];
        
        #get our cool to temperature
        self._coolto = statInfo['Cool_Set_Point'];

class Lennox_Status(Entity):
    """Representation of the Lennox iComfort thermostat status sensor."""
    
    def __init__(self, api):
        """Initialize the sensor."""
        self._name = 'status'
        self._api = api
   
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
    
    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.lennox_{}'.format(self._name)

    def update(self):
        """Get the latest data for the states."""
        if self._api is not None:
            self._api.update()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._api._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ''

class Lennox_Temperature(Entity):
    """Representation of the Lennox iComfort thermostat indoor temperature sensor."""
    
    def __init__(self, api):
        """Initialize the sensor."""
        self._name = 'temperature'
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.lennox_{}'.format(self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._api._temperature

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

class Lennox_HeatTo(Entity):
    """Representation of the Lennox iComfort thermostat heat to sensor."""
    
    def __init__(self, api):
        """Initialize the sensor."""
        self._name = 'heat_to'
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.lennox_{}'.format(self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._api._heatto

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

class Lennox_CoolTo(Entity):
    """Representation of the Lennox iComfort thermostat cool to sensor."""
    
    def __init__(self, api):
        """Initialize the sensor."""
        self._name = 'cool_to'
        self._api = api
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.lennox_{}'.format(self._name)		

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._api._coolto

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

class Lennox_Humidity(Entity):
    """Representation of the Lennox iComfort thermostat humidity sensor."""
    
    def __init__(self, api):
        """Initialize the sensor."""
        self._name = 'humidity'
        self._api = api
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.lennox_{}'.format(self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._api._humidity

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return '%'