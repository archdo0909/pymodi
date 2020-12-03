import os
from typing import List

import serial.tools.list_ports as stl
from serial.tools.list_ports_common import ListPortInfo


def is_on_pi() -> bool:
    """Returns whether connected to pi

    :return: true if connected to pi
    :rtype: bool
    """
    return os.name != "nt" and os.uname()[4][:3] == "arm"


def is_network_module_connected() -> bool:
    """Returns whether network module is connected

    :return: true if connected
    :rtype: bool
    """
    return bool(list_modi_ports())


def list_modi_ports() -> List[ListPortInfo]:
    """Returns a list of connected MODI ports

    :return: List[ListPortInfo]
    """

    def __is_modi_port(port):
        return (
            port.manufacturer == "LUXROBO"
            or port.product in ( "MODI Network Module",
                "MODI Network Module(BootLoader)",
                "STM32 Virtual ComPort",
                )
            or port.description == "MODI Network Module"
            or (port.vid == 0x2fdc and port.pid == 0x2))

    return [port for port in stl.comports() if __is_modi_port(port)]


def is_modi_pi() -> bool:
    """Returns whether connection is on pi

    :return: true is on pi
    :rtype: bool
    """
    return is_on_pi() and not is_network_module_connected()


class AIModuleNotFoundException(Exception):
    """Exception class which determine whether MODI AI module has connected
    """
    def __init__(self):
        super().__init__('Please connect MODI AI module')


class AIModuleFaultsException(Exception):
    """Exception class which check if MODI AI module features are fault
    """
    def __init__(self, message):
        super().__init__(message)


class MODIConnectionError(Exception):
    pass
