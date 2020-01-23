# -*- coding: utf-8 -*-

"""Env module."""

from enum import Enum
from modi.module.module import InputModule


class Env(InputModule):
    """
    :param int id: The id of the module.
    :param int uuid: The uuid of the module.
    :param modi: The :class:`~modi.modi.MODI` instance.
    :type modi: :class:`~modi.modi.MODI`
    """

    class PropertyType(Enum):
        TEMPERATURE = 6
        HUMIDITY = 7
        BRIGHTNESS = 2
        RED = 3
        GREEN = 4
        BLUE = 5

    def __init__(self, module_id, uuid, modi, serial_write_q):
        super(Env, self).__init__(module_id, uuid, modi, serial_write_q)
        self._type = "env"

    def temperature(self):
        """
        :return: Temperature.
        :rtype: float
        """
        return self._get_property(self.PropertyType.TEMPERATURE)

    def humidity(self):
        """
        :return: Humidity.
        :rtype: float
        """
        return self._get_property(self.PropertyType.HUMIDITY)

    def brightness(self):
        """
        :return: Brightness.
        :rtype: float
        """
        return self._get_property(self.PropertyType.BRIGHTNESS)

    def red(self):
        """
        :return: Red component of light.
        :rtype: float
        """
        return self._get_property(self.PropertyType.RED)

    def green(self):
        """
        :return: Green component of light.
        :rtype: float
        """
        return self._get_property(self.PropertyType.GREEN)

    def blue(self):
        """
        :return: Blue component of light.
        :rtype: float
        """
        return self._get_property(self.PropertyType.BLUE)
