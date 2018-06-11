# -*- coding: utf-8 -*-
import sys
import logging
import time
import pprint

from functools import wraps
import requests

import definitions 

BASE_URL = 'https://que.actronair.com.au'
USER_DEVICES_SUFFIX = '/api/v0/client/user-devices'
TOKEN_SUFFIX = '/api/v0/oauth/token'
ACCOUNT_SUFFIX = '/api/v0/client/account'
AC_SYSTEMS_SUFFIX = '/api/v0/client/ac-systems'
AC_DATA = '/status/latest?serial='
SEND_CMD = '/cmds/send?serial='
CLIENT_TYPE = 'Android' # Client options Ios, Android, WindowsPhone or LoadTest"
MAX_ZONES = 8

logger = logging.getLogger(__name__)

class ActronQueACSystem(object):

    def __init__(self, client, serial, description, ac_id, ac_type):
        self.client = client
        self.serial = serial
        self.description = description
        self.ac_id = ac_id
        self.ac_type = ac_type
        self.attribute_tree = None
        self.zones = [None] * MAX_ZONES
        self.attribute_index = {}

    def _populate_zones(self):
        for i, zone in enumerate(self.attribute_tree['lastKnownState']['RemoteZoneInfo']):
            self.zones[i] = ActronQueZone(i)
            for attribute in definitions.populate_zone(self.attribute_tree['lastKnownState'], i):
                self.attribute_index[attribute.path] = attribute
                self.zones[i].add_attribute(attribute)

    def populate(self, lastKnownStateDump):
        self.attribute_tree = lastKnownStateDump
        print pprint.pprint(lastKnownStateDump)
        self._populate_zones()

    def get_attribute(self, path):
        try:
            return self.attribute_index[path]
        except KeyError:
            return None

class ActronAttribute(object):

    def __init__(self, path, value, mutable=True):
        self.path = path
        self.attribute = self.path.split(".")[-1]
        self.value = value
        self.mutable = mutable
        logger.debug("Creating Attribute: %s", self.__repr__())

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '{0}: {1}'.format(self.path, self.value)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return not self.__eq__(other)

    # @property
    # def value(self):
    #     pass

    def _update_value(self):
        pass

    def update_value(self):
        pass

    def get_value(self):
        return self.value

    def get_path_value(self):
        return (self.path, self.value)

class ActronQueZone(object):

    def __init__(self, index):
        self.index = index
        self.name = ''
        self.attributes = []

    def __repr__(self):
        return '{0} {1} {2}'.format(self.index, self.name, self.attributes)

    def add_attribute(self, attribute):
        self.attributes.append(attribute)

class ActronQueSensor(object):
    pass

class ActronQueCommand(object):

    COMMAND_STRUCT = {'command':{'type': 'set-settings'}}

    def __init__(self, serial, command, value):
        self.serial = serial
        self.command = command
        self.value = value

    def __str__(self):
        return '{0}: {1}'.format(self.command, self.value)

    def get_formatted(self):
        formatted_command = COMMAND_STRUCT
        formatted_command[self.command] = self.value
        return formatted_command

class ActronQueClient(object):

    def __init__(self, username, password, device_id='ActronQuePy', device_name='ActronQuePy'):
        self.username = username
        self.password = password
        self.device_id = device_id
        self.device_name = device_id
        self.request_session = requests.Session()
        self.pairing_token = None
        self.expire_time = time.time()
        self.ac_systems = {}

    def connect(self):
        self._get_oath_token()
        self._populate()

    def _oath_timeout_check(f):
        @wraps(f)
        def wrapper(inst, *args, **kwargs):
            if inst.expire_time <= time.time():
                inst._get_oath_token()
            return f(inst, *args, **kwargs)
        return wrapper

    def _authenticate(self):
        auth_data = {'username': self.username,
                     'password': self.password,
                     'deviceName': self.device_name,
                     'client': CLIENT_TYPE,
                     'deviceUniqueIdentifier': self.device_id}

        response = self.request_session.post(BASE_URL + USER_DEVICES_SUFFIX, data=auth_data)
        auth_response = response.json()
        self.pairing_token = auth_response[u'pairingToken']

    def _get_oath_token(self):
        if not self.pairing_token:
            self._authenticate()
        oauth_data = {'grant_type': 'refresh_token',
                      'refresh_token': self.pairing_token,
                      'client_id': 'app'}

        response = self.request_session.post(BASE_URL + TOKEN_SUFFIX, data=oauth_data)
        oauth_response = response.json()
        self.expire_time = time.time() + oauth_response[u'expires_in']
        self.request_session.headers.update({'authorization': '{0} {1}'.format(oauth_response[u'token_type'],
                                                                               oauth_response[u'access_token'])})

    @_oath_timeout_check
    def _populate(self):

        response = self.request_session.get(BASE_URL + AC_SYSTEMS_SUFFIX)

        for ac in response.json()[u'_embedded'][u'ac-system']:
            self.ac_systems.update({ac[u'serial']: ActronQueACSystem(self,
                                                                     ac[u'serial'],
                                                                     ac[u'description'],
                                                                     ac[u'id'],
                                                                     ac[u'type'])})
        self._update_data()

    @_oath_timeout_check
    def _update_data(self):
        for serial, ac in self.ac_systems.iteritems():
            response = self.request_session.get(BASE_URL + AC_SYSTEMS_SUFFIX + AC_DATA + serial)
            ac.populate(response.json())

    @_oath_timeout_check
    def send_cmd(self, ac_system_object, command_object):
        if not isinstance(command_object, ActronQueCommand):
            raise TypeError("Expecting ActronQueCommand Object")

        self.request_session.post(BASE_URL + AC_SYSTEMS_SUFFIX + SEND_CMD + ac_system_object.serial,
                                  json=command_object.get_formatted())

    def get_ac_systems(self):
        return self.ac_systems

    def refresh_data(self):
        self._update_data()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test = ActronQueClient(sys.argv[1], sys.argv[2])
    test.connect()
    while True:
        time.sleep(10)
        print time.time()
        test.refresh_data()
    print test.get_ac_systems()
