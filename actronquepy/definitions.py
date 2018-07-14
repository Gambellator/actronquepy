# -*- coding: utf-8 -*-
import logging
import pprint

from quedatatypes import ActronAttribute

logger = logging.getLogger(__name__)

ZONES = {
    'mutable': True,
    'index': '[zone]',
    'index_type': list,
    'contents': {
        'RemoteZoneInfo.[zone].CanOperate': {'type': bool},
        'RemoteZoneInfo.[zone].LiveHumidity_pc': {'type': int},
        'RemoteZoneInfo.[zone].LiveTempHysteresis_oC': {'type': float},
        'RemoteZoneInfo.[zone].LiveTemp_oC': {'type': float},
        'RemoteZoneInfo.[zone].MaxCoolSetpoint': {'type': int},
        'RemoteZoneInfo.[zone].MaxHeatSetpoint': {'type': int},
        'RemoteZoneInfo.[zone].MinCoolSetpoint': {'type': int},
        'RemoteZoneInfo.[zone].MinHeatSetpoint': {'type': int},
        'RemoteZoneInfo.[zone].NV_Exists': {'type': bool},
        'RemoteZoneInfo.[zone].NV_Title': {'type': unicode},
        'RemoteZoneInfo.[zone].NV_VAV': {'type': bool},
        'RemoteZoneInfo.[zone].NV_amSetup': {'type': bool},
        'RemoteZoneInfo.[zone].TemperatureSetpoint_Cool_oC': {'type': int},
        'RemoteZoneInfo.[zone].TemperatureSetpoint_Heat_oC': {'type': int},
        'RemoteZoneInfo.[zone].ZonePosition': {'type': int},
        'UserAirconSettings.EnabledZones.[zone]': {'type': int},
        'UserAirconSettings.NV_SavedZoneState.[zone]': {'type': int},
    },
}

SENSORS = {
    'mutable': False,
    'contents': {
        'RemoteZoneInfo.[zone].Sensors.{sensor}.Connected': {'type': bool},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.NV_Kind': {'type': unicode},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.NV_isPaired': {'type': bool},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.Signal_of3': {'type': int},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.lastRssi': {'type': int},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.TX_Power': {'type': int},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.FW_Version': {'type': int},
        'RemoteZoneInfo.[zone].Sensors.{sensor}.Battery_pc': {'type': int},
    },
}

LIVE_STATS = {
    'mutable': False,
    'contents': {
        'Cloud.ConnectionState': {'type': unicode},
        'Cloud.ReceivedPackets': {'type': int},
        'Cloud.SentPackets': {'type': int},
        'SystemState.CpuFreq_MHz': {'type': int},
        'SystemState.CpuId': {'type': unicode},
        'SystemState.CpuTempMax_oC': {'type': float},
        'SystemState.CpuTemp_oC': {'type': float},
        'SystemState.LinkedToMaster': {'type': int},
        'SystemState.MemUsage_K': {'type': int},
        'SystemState.NV_LastBootFromUnsafeUTC': {'type': unicode},
        'SystemState.ScreenIsOn': {'type': bool},
        'SystemState.WCFirmwareVersion': {'type': unicode},
        'SystemState.ZCFirmwareVersion': {'type': unicode},
        'SystemState.hasInternet': {'type': bool},
    },
}

SUPPORTED = (ZONES, LIVE_STATS)


class DottedAttribute(object):

    def __init__(self):
        self.attributes = {}

    def __contains__(self, item):
        return item in self.attributes

    def _get_values(self, data, path=''):
        if isinstance(data, dict):
            for key, value in data.iteritems():
                if path == '':
                     self._get_values(value, path = str(key))
                else:
                    self._get_values(value, path='{0}.{1}'.format(path, key))
        elif isinstance(data, list):
            for i, value in enumerate(data):
                self._get_values(value, path='{0}.[{1}]'.format(path, i))
        else:
            if path in self:
                self.get_attribute(path).value = data
            else:
                self.attributes[path] = ActronAttribute(path, data)

    def get_attribute(self, attribute_path):
        '''
        Checks if ActronAttribute exits for a given path and returns
        an ActronAttribute if it exits.
        '''
        try:
            return self.attributes[attribute_path]
        except KeyError:
            return None

    def refresh(self, json_data):
        self._get_values(json_data)

    def dump_data(self):
        print pprint.pprint(self.attributes)


def dot_notation(json_data, split_path):
    for key in split_path:
        json_data = json_data[key]
    return json_data

def populate_zone(attribute_tree, index):
    '''
    Takes JSON/dict data recieved from the api and churns out
    object data based on the definitions.
    '''
    mutable = ZONES['mutable']
    attribute_objects = []
    for attribute_path, definition in ZONES['contents'].iteritems():
        split_path = attribute_path.split('.')
        if ZONES['index_type'] == list:
            for i, part in enumerate(split_path):
                if part == ZONES['index']:
                    split_path[i] = index
            path = ".".join(map(lambda x: "[{0}]".format(x) if isinstance(x, int) else x, split_path))
            try:
                value = definition['type'](dot_notation(attribute_tree, split_path))
            except KeyError:
                logger.debug("Unable to find value for path: %s", path)
                continue
            attribute_objects.append(ActronAttribute(path, value,
                                                     mutable=ZONES['mutable']))
    return attribute_objects

def populate_stats(attribute_tree):
    '''
    Takes JSON/dict data recieved from the api and churns out
    object data based on the definitions.
    '''
    mutable = LIVE_STATS['mutable']
    attribute_objects = []
    for attribute_path, definition in LIVE_STATS['contents'].iteritems():
        split_path = attribute_path.split('.')
        path = ".".join(map(lambda x: "[{0}]".format(x) if isinstance(x, int) else x, split_path))
        try:
            value = definition['type'](dot_notation(attribute_tree, split_path))
        except KeyError:
            logger.debug("Unable to find value for path: %s", path)
            continue
        attribute_objects.append(ActronAttribute(path, value,
                                                 mutable=LIVE_STATS['mutable']))
    return attribute_objects

def populate_sensors(attribute_tree):
    '''
    '''
    pass
