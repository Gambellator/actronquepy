# -*- coding: utf-8 -*-
import sys
import logging
import time
import pprint

from functools import wraps
import requests

import definitions as definitions
from quedatatypes import ActronAttribute, ActronQueZone, ActronQueSensor, ActronQueCommand

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
        #self.zones = [None] * MAX_ZONES
        self.zones = map(ActronQueZone, range(MAX_ZONES))
        self.system_stats = []
        self.attribute_index = definitions.DottedAttribute()

    def _populate_zones(self):
        for i, zone in enumerate(self.zones):
            zone.title = self.get_attribute('RemoteZoneInfo.[{0}].NV_Title'.format(i))
            zone.zone_position = self.get_attribute('RemoteZoneInfo.[{0}].ZonePosition'.format(i))
            zone.live_temp = self.get_attribute('RemoteZoneInfo.[{0}].LiveTemp_oC'.format(i))
            #self.zones[i] = ActronQueZone(i)
            #for attribute in definitions.populate_zone(self.attribute_tree['lastKnownState'], i):
            #    self.attribute_index[attribute.path] = attribute
            #    self.zones[i].add_attribute(attribute)

    def _populate_system_stats(self):
        self.system_stats = []
        formatted_serial = unicode("<{0}>".format(self.serial).upper())
        for attribute in definitions.populate_stats(self.attribute_tree['lastKnownState'][formatted_serial]):
            self.attribute_index[attribute.path] = attribute
            self.system_stats.append(attribute)

    def populate(self, lastKnownStateDump):
        self.attribute_tree = lastKnownStateDump
        formatted_serial = unicode("<{0}>".format(self.serial).upper())
        self.attribute_index.refresh(self.attribute_tree['lastKnownState'])
        #self.attribute_index.dump_data()

        #print pprint.pprint(lastKnownStateDump)
        self._populate_zones()
        print self.zones
        #self._populate_system_stats()

    def get_attribute(self, path):
        try:
            return self.attribute_index.get_attribute(path)
        except KeyError:
            return None


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

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._disconnect()

    def __repr__(self):
        repr_string = '{0}({username}, ******, device_id={device_id}, device_name={device_name})'
        return repr_string.format(self.__class__.__name__, **self.__dict__)

    def _connect(self):
        self._get_oath_token()
        self._populate()

    def _disconnect(self):
        self.request_session.close()

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
    with ActronQueClient(sys.argv[1], sys.argv[2]) as test:
        #test.connect()
        while True:
            time.sleep(10)
            print(time.time())
            test.refresh_data()
        print(test.get_ac_systems())
