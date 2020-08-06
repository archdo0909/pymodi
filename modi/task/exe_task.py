import json
import time
from typing import Callable, Dict, Union

from enum import IntEnum

from modi.module.module import Module, BROADCAST_ID
from modi.util.misc import get_module_from_name, get_module_type_from_uuid
from modi.util.msgutil import unpack_data, decode_data, parse_message
from modi.util.conn_util import is_network_module_connected


class ExeTask:

    def __init__(self, modules, topology_data, conn_task):
        self._modules = modules
        self._topology_data = topology_data
        self._conn = conn_task

        # Reboot all modules
        self.__set_module_state(
            BROADCAST_ID, Module.State.REBOOT, Module.State.PNP_OFF
        )
        if is_network_module_connected():
            self.__request_network_uuid()
        print('Start initializing connected MODI modules')

    def run(self, delay: float):
        """ Run in ExecutorThread

        :param delay: time value to wait in seconds
        :type delay: float
        """
        json_pkt = self._conn.recv()
        if not json_pkt:
            time.sleep(delay)
        else:
            try:
                json_msg = json.loads(json_pkt)
                self.__command_handler(json_msg['c'])(json_msg)
            except json.decoder.JSONDecodeError:
                print('current json message:', json_pkt)

    def __command_handler(self,
                          command: int) -> Callable[[Dict[str, int]], None]:
        """ Execute task based on command message

        :param command: command code
        :type command: int
        :return: a function the corresponds to the command code
        :rtype: Callable[[Dict[str, int]], None]
        """
        return {
            0x00: self.__update_health,
            0x05: self.__update_modules,
            0x07: self.__update_topology,
            0x1F: self.__update_property,
        }.get(command, lambda _: None)

    def __update_topology(self, message: Dict[str, Union[int, str]]) -> None:
        """Update the topology of the connected modules

        :param message: Dictionary format message of the module
        :return: None
        """
        # Setup prerequisites
        src_id = message["s"]
        byte_data = message["b"]
        topology_by_id = {}
        topology_ids = unpack_data(byte_data, (2, 2, 2, 2))

        module = self.__get_module_by_id(src_id)
        if module:
            topology_by_id['type'] = get_module_type_from_uuid(module.uuid)
        else:
            topology_by_id['type'] = None

        for idx, direction in enumerate(('r', 't', 'l', 'b')):
            topology_by_id[direction] = topology_ids[idx] \
                if topology_ids[idx] != 0xFFFF else None

        # Update topology data for the module
        self._topology_data[src_id] = topology_by_id

    def __get_module_by_id(self, module_id):
        for module in self._modules:
            if module.id == module_id:
                return module

    def __update_health(self, message: Dict[str, Union[int, str]]) -> None:
        """ Update information by health message

        :param message: Dictionary format message of the module
        :type message: Dictionary
        :return: None
        """
        # Record battery information and user code state
        module_id = message["s"]
        _, _, _, battery_state, user_code_state \
            = unpack_data(message['b'], (1, 1, 1, 1, 1))
        curr_time = time.time()
        # Checking starts only when module is registered
        if module_id in (module.id for module in self._modules):
            module = self.__get_module_by_id(module_id)
            module.last_updated = curr_time
            module.is_connected = True
            # Warn if user code is in the module
            if not module.has_user_code and user_code_state % 2 == 1:
                print(f"Your MODI module {module_id} has user code in it.")
                print("You can reset your MODI modules by calling "
                      "'update_module_firmware()'")
                module.has_user_code = True
            # Turn off pnp if pnp flag is on
            if user_code_state < 2:
                self.__set_module_state(
                    module_id, Module.State.RUN, Module.State.PNP_OFF
                )
        # Disconnect module with no health message for more than 2 second
        for module in self._modules:
            if curr_time - module.last_updated > 2:
                module.is_connected = False

    def __update_modules(self, message: Dict[str, Union[str, int]]) -> None:
        """ Update module information
        :param message: Dictionary format module info
        :type message: Dictionary
        :return: None
        """
        module_id = message['s']
        module_uuid, module_version_info = \
            unpack_data(message['b'], (6, 2))

        # Handle new modules
        if module_id not in (module.id for module in self._modules):
            module_type = get_module_type_from_uuid(module_uuid)
            self.request_topology(module_id)
            new_module = self.__add_new_module(
                module_type, module_id, module_uuid, module_version_info
            )
            new_module.module_type = module_type
            # if module_type != 'Network':
            #     new_module.is_up_to_date = self.__check_module_version(
            #         module_version_info
            #     )
        elif not self.__get_module_by_id(module_id).is_connected:
            # Handle Reconnected modules
            self.__get_module_by_id(module_id).is_connected = True

    def __check_module_version(self, current_version):
        latest_version = self.__get_latest_version()
        if latest_version and current_version < latest_version:
            print("Your MODI module(s) is not up-to-date.")
            print("You can update your MODI modules by calling "
                  "'update_module_firmware()'")
            return False
        return True

    def __add_new_module(self, module_type, module_id,
                         module_uuid, module_version_info):
        module_template = get_module_from_name(module_type)
        module_instance = module_template(
            module_id, module_uuid, self._conn
        )
        self.__set_module_state(module_instance.id, Module.State.RUN,
                                Module.State.PNP_OFF)
        module_instance.version = module_version_info
        self._modules.append(module_instance)
        print(f"{type(module_instance).__name__} ({module_id}) "
              f"has been connected!")
        return module_instance

    def __update_property(self, message: Dict[str, str]) -> None:
        """ Update module property

        :param message: Dictionary format message
        :type message: Dictionary
        :return: None
        """
        # Do not update reserved property
        property_number = message["d"]
        if property_number == 0 or property_number == 1:
            return
        module = self.__get_module_by_id(message['s'])
        if not module:
            return
        module.update_property(property_number, decode_data(message['b']))

    def __set_module_state(self, destination_id: int, module_state: IntEnum,
                           pnp_state: IntEnum) -> None:
        """ Generate message for set module state and pnp state

        :param destination_id: Id to target destination
        :type destination_id: int
        :param module_state: State value of the module
        :type module_state: int
        :param pnp_state: Pnp state value
        :type pnp_state: IntEnum
        :return: None
        """
        self._conn.send(parse_message(0x09, 0, destination_id,
                                      (module_state, pnp_state)))

    def __request_network_uuid(self):
        self._conn.send(
            parse_message(0x28, BROADCAST_ID, BROADCAST_ID, (0xFF, 0x0F))
        )

    def request_topology(self, module_id: int = BROADCAST_ID) -> None:
        """Request module topology

        :return: json serialized topology request message
        :rtype: str
        """
        self._conn.send(
            parse_message(0x07, 0, module_id, (0, 0, 0, 0, 0, 0, 0, 0))
        )
        self._conn.send(
            parse_message(0x2A, 0, module_id, (0, 0, 0, 0, 0, 0, 0, 0))
        )
