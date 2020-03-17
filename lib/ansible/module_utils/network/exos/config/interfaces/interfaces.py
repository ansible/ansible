#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.network.exos.facts.facts import Facts
from ansible.module_utils.network.exos.exos import send_requests, run_commands


class Interfaces(ConfigBase):
    """
    The exos_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'interfaces',
    ]

    INTERFACE_CONFIG = {
        "data": {"openconfig-interfaces:config": {}},
        "method": "PATCH",
        "path": None
    }

    INTERFACE_AUTO = {
        "data": {"openconfig-if-ethernet:config": {"auto-negotiate": True}},
        "method": "PATCH",
        "path": None
    }

    INTERFACE_PATH = "/rest/restconf/data/openconfig-interfaces:interfaces/interface="

    PORT_SPEED = {
        "SPEED_10MB": "10",
        "SPEED_100MB": "100",
        "SPEED_1GB": "1000",
        "SPEED_10GB": "10000",
        "SPEED_25GB": "25000",
        "SPEED_40GB": "40000",
        "SPEED_50GB": "50000",
        "SPEED_100GB": "100000",
    }

    def __init__(self, module):
        super(Interfaces, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        interfaces_facts = facts['ansible_network_resources'].get('interfaces')
        if not interfaces_facts:
            return []
        return interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        requests = list()
        commands = list()

        existing_interfaces_facts = self.get_interfaces_facts()
        req, cmd = self.set_config(existing_interfaces_facts)
        requests.extend(req)
        commands.extend(cmd)

        if requests:
            if not self._module.check_mode:
                send_requests(self._module, requests=requests)
            result['changed'] = True
        result['requests'] = requests

        if commands:
            if not self._module.check_mode:
                run_commands(self._module, commands=commands)
            result['changed'] = True
        result['commands'] = commands

        changed_interfaces_facts = self.get_interfaces_facts()

        result['before'] = existing_interfaces_facts
        if result['changed']:
            result['after'] = changed_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_interfaces_facts
        resp_req, resp_cmd = self.set_state(want, have)
        return to_list(resp_req), to_list(resp_cmd)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state == 'overridden':
            requests, commands = self._state_overridden(want, have)
        elif state == 'deleted':
            requests, commands = self._state_deleted(want, have)
        elif state == 'merged':
            requests, commands = self._state_merged(want, have)
        elif state == 'replaced':
            requests, commands = self._state_replaced(want, have)
        return requests, commands

    def _state_replaced(self, want, have):
        """ The request generator when state is replaced

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []
        commands = []
        for w in want:
            for h in have:
                if w['name'] == h['name']:
                    diff = dict_diff(h, w)
                    if diff:
                        interface_request, interface_command = self._update_patch_request(diff, h)
                        for request in interface_request:
                            if request["data"].get("openconfig-interfaces:config") and len(request["data"]["openconfig-interfaces:config"]):
                                request['data'] = json.dumps(request['data'])
                                requests.append(request)
                            elif request['data'].get('openconfig-if-ethernet:config') and len(request['data']['openconfig-if-ethernet:config']):
                                request['data'] = json.dumps(request['data'])
                                requests.append(request)
                        commands.extend(interface_command)
                    break

        return requests, commands

    def _state_overridden(self, want, have):
        """ The request generator when state is overridden

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []
        commands = []
        have_copy = []
        for w in want:
            for h in have:
                if w['name'] == h['name']:
                    diff = dict_diff(h, w)
                    if diff:
                        interface_request, interface_command = self._update_patch_request(diff, h)
                        for request in interface_request:
                            if request["data"].get("openconfig-interfaces:config") and len(request["data"]["openconfig-interfaces:config"]):
                                request['data'] = json.dumps(request['data'])
                                requests.append(request)
                            elif request['data'].get('openconfig-if-ethernet:config') and len(request['data']['openconfig-if-ethernet:config']):
                                request['data'] = json.dumps(request['data'])
                                requests.append(request)
                        commands.extend(interface_command)
                    have_copy.append(h)
                    break

        for h in have:
            if h not in have_copy:
                interface_del_req, interface_del_cmd = self._update_delete_request(h)
                if len(interface_del_req["data"]["openconfig-interfaces:config"]):
                    interface_del_req["data"] = json.dumps(interface_del_req["data"])
                    requests.append(interface_del_req)
                commands.extend(interface_del_cmd)

        return requests, commands

    def _state_merged(self, want, have):
        """ The request generator when state is merged

        :rtype: A list
        :returns: the requests necessary to merge the provided into
                  the current configuration
        """
        requests = []
        commands = []
        for w in want:
            for h in have:
                if w['name'] == h['name']:
                    diff = dict_diff(h, w)
                    if diff:
                        interface_request, interface_command = self._update_patch_request(diff, h)
                        for request in interface_request:
                            if request["data"].get("openconfig-interfaces:config") and len(request["data"]["openconfig-interfaces:config"]):
                                request['data'] = json.dumps(request['data'])
                                requests.append(request)
                            elif request['data'].get('openconfig-if-ethernet:config') and len(request['data']['openconfig-if-ethernet:config']):
                                request['data'] = json.dumps(request['data'])
                                requests.append(request)
                        commands.extend(interface_command)
                    break
        return requests, commands

    def _state_deleted(self, want, have):
        """ The request generator when state is deleted

        :rtype: A list
        :returns: the requests necessary to remove the current configuration
                  of the provided objects
        """
        requests = []
        commands = []
        if want:
            for w in want:
                for h in have:
                    if w["name"] == h["name"]:
                        interface_del_req, interface_del_cmd = self._update_delete_request(h)
                        if len(interface_del_req["data"]["openconfig-interfaces:config"]):
                            interface_del_req["data"] = json.dumps(interface_del_req["data"])
                            requests.append(interface_del_req)
                        commands.extend(interface_del_cmd)
                        break
        else:
            for h in have:
                interface_del_req, interface_del_cmd = self._update_delete_request(h)
                if len(interface_del_req["data"]["openconfig-interfaces:config"]):
                    interface_del_req["data"] = json.dumps(interface_del_req["data"])
                    requests.append(interface_del_req)
                commands.extend(interface_del_cmd)
        return requests, commands

    def _update_delete_request(self, have):

        interface_del_req = deepcopy(self.INTERFACE_CONFIG)
        if not have["enabled"]:
            interface_del_req["data"]["openconfig-interfaces:config"]["enabled"] = True
        interface_del_req["path"] = self.INTERFACE_PATH + have["name"] + "/config"

        interface_del_cmd = []
        if have['description'] is not None and have['description'] != 'Insight':
            interface_del_cmd.append('unconfigure ports ' + have['name'] + ' description-string')
        if have["jumbo_frames"]["enabled"]:
            interface_del_cmd.append("disable jumbo-frame ports " + have["name"])
        if have['speed'] != 'AUTO' or have['duplex'] != 'AUTO':
            interface_del_cmd.append("configure ports " + have["name"] + " auto on")

        return interface_del_req, interface_del_cmd

    def _update_patch_request(self, diff, have):

        requests = []
        commands = []

        interface_request = deepcopy(self.INTERFACE_CONFIG)
        if diff.get('description'):
            interface_request['data']['openconfig-interfaces:config']['description'] = diff['description']
        if diff.get('enabled') == False or diff.get('enabled') == True:
            interface_request['data']['openconfig-interfaces:config']['enabled'] = diff['enabled']
        interface_request["path"] = self.INTERFACE_PATH + have['name'] + '/config'
        requests.append(interface_request)

        if diff.get('duplex') and diff.get('speed'):
            if (diff['speed'] not in self.PORT_SPEED.keys() and diff['speed'] != 'AUTO'):
                self._module.fail_json(msg="Unable to configure port-speed with provided configuration")
            else:
                if (diff['duplex'] != 'AUTO' and diff['speed'] != 'AUTO') and (have['duplex'] == 'AUTO' and have['speed'] == 'AUTO'):
                    requests.append(self._conf_auto_neg_requests(have['name'], diff['duplex'], diff['speed']))
                else:
                    commands.append(self._conf_auto_neg_commands(have['name'], diff['duplex'], diff['speed']))

        elif diff.get('duplex'):
            commands.append(self._conf_auto_neg_commands(have['name'], diff['duplex'], have['speed']))

        elif diff.get('speed'):
            if diff['speed'] in self.PORT_SPEED.keys() or diff['speed'] == 'AUTO':
                commands.append(self._conf_auto_neg_commands(have['name'], have['duplex'], diff['speed']))
            else:
                self._module.fail_json(msg="Unable to configure port-speed with provided configuration")

        if diff.get('jumbo_frames'):
            if diff['jumbo_frames']['enabled']:
                commands.append('enable jumbo-frame ports ' + have["name"])
            else:
                commands.append('disable jumbo-frame ports ' + have["name"])

        return requests, commands

    def _conf_auto_neg_commands(self, name, duplex, speed):
        if duplex == 'AUTO' and speed != 'AUTO':
            return 'configure ports ' + name + ' auto on speed ' + self.PORT_SPEED[speed]
        elif duplex != 'AUTO' and speed == 'AUTO':
            return 'configure ports ' + name + ' auto on duplex '+duplex
        elif duplex == 'AUTO' and speed == 'AUTO':
            return 'configure ports ' + name + ' auto on'
        else:
            return 'configure ports ' + name + ' auto on speed ' + self.PORT_SPEED[speed] + ' duplex ' + duplex

    def _conf_auto_neg_requests(self, name, duplex, speed):
        interface_auto_request = deepcopy(self.INTERFACE_AUTO)
        interface_auto_request['data']['openconfig-if-ethernet:config']['duplex-mode'] = duplex
        interface_auto_request['data']['openconfig-if-ethernet:config']['port-speed'] = speed
        interface_auto_request['path'] = self.INTERFACE_PATH + name + '/openconfig-if-ethernet:ethernet/config'
        return interface_auto_request
