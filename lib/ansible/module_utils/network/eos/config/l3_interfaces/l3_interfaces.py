# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_l3_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, param_list_to_dict
from ansible.module_utils.network.eos.facts.facts import Facts
from ansible.module_utils.network.eos.utils.utils import normalize_interface


class L3_interfaces(ConfigBase):
    """
    The eos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get('l3_interfaces')
        if not l3_interfaces_facts:
            return []
        return l3_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_l3_interfaces_facts = self.get_l3_interfaces_facts()
        commands.extend(self.set_config(existing_l3_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_l3_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_l3_interfaces_facts
        if result['changed']:
            result['after'] = changed_l3_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l3_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        want = param_list_to_dict(want)
        have = param_list_to_dict(have)
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for key, desired in want.items():
            interface_name = normalize_interface(key)
            if interface_name in have:
                extant = have[interface_name]
            else:
                extant = dict()

            intf_commands = set_interface(desired, extant)
            intf_commands.extend(clear_interface(desired, extant))

            if intf_commands:
                commands.append("interface {0}".format(interface_name))
                commands.extend(intf_commands)

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for key, extant in have.items():
            if key in want:
                desired = want[key]
            else:
                desired = dict()
            if desired.get("ipv4"):
                for ipv4 in desired["ipv4"]:
                    if ipv4["secondary"] is None:
                        del ipv4["secondary"]

            intf_commands = set_interface(desired, extant)
            intf_commands.extend(clear_interface(desired, extant))

            if intf_commands:
                commands.append("interface {0}".format(key))
                commands.extend(intf_commands)

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        for key, desired in want.items():
            interface_name = normalize_interface(key)
            if interface_name in have:
                extant = have[interface_name]
            else:
                extant = dict()

            intf_commands = set_interface(desired, extant)

            if intf_commands:
                commands.append("interface {0}".format(interface_name))
                commands.extend(intf_commands)

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for key in want:
            desired = dict()
            if key in have:
                extant = have[key]
            else:
                continue

            intf_commands = clear_interface(desired, extant)

            if intf_commands:
                commands.append("interface {0}".format(key))
                commands.extend(intf_commands)

        return commands


def set_interface(want, have):
    commands = []

    want_ipv4 = set(tuple(address.items()) for address in want.get("ipv4") or [])
    have_ipv4 = set(tuple(address.items()) for address in have.get("ipv4") or [])
    for address in want_ipv4 - have_ipv4:
        address = dict(address)
        if "secondary" in address and not address["secondary"]:
            del address["secondary"]
            if tuple(address.items()) in have_ipv4:
                continue

        address_cmd = "ip address {0}".format(address["address"])
        if address.get("secondary"):
            address_cmd += " secondary"
        commands.append(address_cmd)

    want_ipv6 = set(tuple(address.items()) for address in want.get("ipv6") or [])
    have_ipv6 = set(tuple(address.items()) for address in have.get("ipv6") or [])
    for address in want_ipv6 - have_ipv6:
        address = dict(address)
        commands.append("ipv6 address {0}".format(address["address"]))

    return commands


def clear_interface(want, have):
    commands = []

    want_ipv4 = set(tuple(address.items()) for address in want.get("ipv4") or [])
    have_ipv4 = set(tuple(address.items()) for address in have.get("ipv4") or [])
    if not want_ipv4:
        commands.append("no ip address")
    else:
        for address in have_ipv4 - want_ipv4:
            address = dict(address)
            if "secondary" not in address:
                address["secondary"] = False
                if tuple(address.items()) in want_ipv4:
                    continue

            address_cmd = "no ip address"
            if address.get("secondary"):
                address_cmd += " {0} secondary".format(address["address"])
            commands.append(address_cmd)

            if "secondary" not in address:
                # Removing non-secondary removes all other interfaces
                break

    want_ipv6 = set(tuple(address.items()) for address in want.get("ipv6") or [])
    have_ipv6 = set(tuple(address.items()) for address in have.get("ipv6") or [])
    for address in have_ipv6 - want_ipv6:
        address = dict(address)
        commands.append("no ipv6 address {0}".format(address["address"]))

    return commands
