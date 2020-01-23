# -*- coding: utf-8 -*-

"""Dial module."""

from enum import Enum

from modi.module.module import InputModule


class Dial(InputModule):
    """
    :param int id: The id of the module.
    :param int uuid: The uuid of the module.
    :param modi: The :class:`~modi.modi.MODI` instance.
    :type modi: :class:`~modi.modi.MODI`
    """

    class PropertyType(Enum):
        DEGREE = 2
        TURNSPEED = 3

    def __init__(self, module_id, uuid, modi, serial_write_q):
        super(Dial, self).__init__(module_id, uuid, modi, serial_write_q)
        self._type = "dial"

    def degree(self):
        """
        :return: The dial's angle.
        :rtype: float
        """
        return self._get_property(self.PropertyType.DEGREE)

    def turnspeed(self):
        return self._get_property(self.PropertyType.TURNSPEED)
