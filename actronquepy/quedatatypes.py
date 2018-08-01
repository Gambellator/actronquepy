# -*- coding: utf-8 -*-
''' quedatatypes.py '''
import logging
import pprint

logger = logging.getLogger(__name__)

class ActronAttribute(object):

    def __init__(self, path, value, mutable=True):
        self.path = path
        self.attribute = self.path.split(".")[-1]
        self._value = value
        self.mutable = mutable
        logger.debug("Creating Attribute: %s", self.__repr__())

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return 'ActronAttribute({0}, {1})'.format(self.path, self.value)

    def __eq__(self, other):
        return self.path == other

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value != self._value:
            logging.debug("Updated value for %s from %s to %s", self.path, self._value, value)
        self._value = value
        
    def update_value(self, value):
        self.value = value
        return ActronQueCommand(self.path, self._value)

    def get_path_value(self):
        return (self.path, self.value)


class ActronQueZone(object):

    def __init__(self, index):
        self.index = index
        self.title = ''
        self.zone_position = 0
        self.live_temp = 0.0

    def __repr__(self):
        return '{0} {1} {2} {3}'.format(self.index, self.title.value, self.zone_position.value * 5, self.live_temp.value)

    def populate(self):
        pass

    def add_attribute(self, attribute):
        self.attributes.append(attribute)


class ActronQueSensor(object):
    pass


class ActronQueCommand(object):

    COMMAND_STRUCT = {'command':{'type': 'set-settings'}}

    def __init__(self, command, value):
        self.command = command
        self.value = value

    def __str__(self):
        return '{0}: {1}'.format(self.command, self.value)

    def get_formatted(self):
        formatted_command = COMMAND_STRUCT
        formatted_command[self.command] = self.value
        return formatted_command