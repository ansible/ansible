#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos_lldp_interfaces class
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
from ansible.module_utils.network.exos.exos import send_requests


class Lldp_interfaces(ConfigBase):
    """
    The exos_lldp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_interfaces',
    ]

    LLDP_INTERFACE = {
        "data": {
            "openconfig-lldp:config": {
                "name": None,
                "enabled": True
            }
        },
        "method": "PATCH",
        "path": None
    }

    LLDP_PATH = "/rest/restconf/data/openconfig-lldp:lldp/interfaces/interface="

    def __init__(self, module):
        super(Lldp_interfaces, self).__init__(module)

    def get_lldp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        lldp_interfaces_facts = facts['ansible_network_resources'].get(
            'lldp_interfaces')
        if not lldp_interfaces_facts:
            return []
        return lldp_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        requests = list()

        existing_lldp_interfaces_facts = self.get_lldp_interfaces_facts()
        requests.extend(self.set_config(existing_lldp_interfaces_facts))
        if requests:
            if not self._module.check_mode:
                send_requests(self._module, requests=requests)
            result['changed'] = True
        result['requests'] = requests

        changed_lldp_interfaces_facts = self.get_lldp_interfaces_facts()

        result['before'] = existing_lldp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lldp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

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
            requests = self._state_overridden(want, have)
        elif state == 'deleted':
            requests = self._state_deleted(want, have)
        elif state == 'merged':
            requests = self._state_merged(want, have)
        elif state == 'replaced':
            requests = self._state_replaced(want, have)
        return requests

    def _state_replaced(self, want, have):
        """ The request generator when state is replaced

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []

        for w in want:
            for h in have:
                if w['name'] == h['name']:
                    lldp_request = self._update_patch_request(w, h)
                    if lldp_request["path"]:
                        lldp_request["data"] = json.dumps(lldp_request["data"])
                        requests.append(lldp_request)

        return requests

    def _state_overridden(self, want, have):
        """ The request generator when state is overridden

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []
        have_copy = []
        for w in want:
            for h in have:
                if w['name'] == h['name']:
                    lldp_request = self._update_patch_request(w, h)
                    if lldp_request["path"]:
                        lldp_request["data"] = json.dumps(lldp_request["data"])
                        requests.append(lldp_request)
                    have_copy.append(h)

        for h in have:
            if h not in have_copy:
                if not h['enabled']:
                    lldp_delete = self._update_delete_request(h)
                    if lldp_delete["path"]:
                        lldp_delete["data"] = json.dumps(lldp_delete["data"])
                        requests.append(lldp_delete)

        return requests

    def _state_merged(self, want, have):
        """ The request generator when state is merged

        :rtype: A list
        :returns: the requests necessary to merge the provided into
                  the current configuration
        """
        requests = []
        for w in want:
            for h in have:
                if w['name'] == h['name']:
                    lldp_request = self._update_patch_request(w, h)
                    if lldp_request["path"]:
                        lldp_request["data"] = json.dumps(lldp_request["data"])
                        requests.append(lldp_request)

        return requests

    def _state_deleted(self, want, have):
        """ The request generator when state is deleted

        :rtype: A list
        :returns: the requests necessary to remove the current configuration
                  of the provided objects
        """
        requests = []
        if want:
            for w in want:
                for h in have:
                    if w['name'] == h['name']:
                        if not h['enabled']:
                            lldp_delete = self._update_delete_request(h)
                            if lldp_delete["path"]:
                                lldp_delete["data"] = json.dumps(
                                    lldp_delete["data"])
                                requests.append(lldp_delete)
        else:
            for h in have:
                if not h['enabled']:
                    lldp_delete = self._update_delete_request(h)
                    if lldp_delete["path"]:
                        lldp_delete["data"] = json.dumps(lldp_delete["data"])
                        requests.append(lldp_delete)

        return requests

    def _update_patch_request(self, want, have):

        lldp_request = deepcopy(self.LLDP_INTERFACE)

        if have['enabled'] != want['enabled']:
            lldp_request["data"]["openconfig-lldp:config"]["name"] = want[
                'name']
            lldp_request["data"]["openconfig-lldp:config"]["enabled"] = want[
                'enabled']
            lldp_request["path"] = self.LLDP_PATH + str(
                want['name']) + "/config"

        return lldp_request

    def _update_delete_request(self, have):

        lldp_delete = deepcopy(self.LLDP_INTERFACE)

        lldp_delete["data"]["openconfig-lldp:config"]["name"] = have['name']
        lldp_delete["data"]["openconfig-lldp:config"]["enabled"] = True
        lldp_delete["path"] = self.LLDP_PATH + str(have['name']) + "/config"

        return lldp_delete
