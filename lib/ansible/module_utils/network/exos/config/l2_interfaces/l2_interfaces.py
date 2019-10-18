#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos_l2_interfaces class
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


class L2_interfaces(ConfigBase):
    """
    The exos_l2_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l2_interfaces',
    ]

    L2_INTERFACE_NATIVE = {
        "data": {
            "openconfig-vlan:config": {
                "interface-mode": "TRUNK",
                "native-vlan": None,
                "trunk-vlans": []
            }
        },
        "method": "PATCH",
        "path": None
    }

    L2_INTERFACE_TRUNK = {
        "data": {
            "openconfig-vlan:config": {
                "interface-mode": "TRUNK",
                "trunk-vlans": []
            }
        },
        "method": "PATCH",
        "path": None
    }

    L2_INTERFACE_ACCESS = {
        "data": {
            "openconfig-vlan:config": {
                "interface-mode": "ACCESS",
                "access-vlan": None
            }
        },
        "method": "PATCH",
        "path": None
    }

    L2_PATH = "/rest/restconf/data/openconfig-interfaces:interfaces/interface="

    def __init__(self, module):
        super(L2_interfaces, self).__init__(module)

    def get_l2_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        l2_interfaces_facts = facts['ansible_network_resources'].get(
            'l2_interfaces')
        if not l2_interfaces_facts:
            return []
        return l2_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        requests = list()

        existing_l2_interfaces_facts = self.get_l2_interfaces_facts()
        requests.extend(self.set_config(existing_l2_interfaces_facts))
        if requests:
            if not self._module.check_mode:
                send_requests(self._module, requests=requests)
            result['changed'] = True
        result['requests'] = requests

        changed_l2_interfaces_facts = self.get_l2_interfaces_facts()

        result['before'] = existing_l2_interfaces_facts
        if result['changed']:
            result['after'] = changed_l2_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l2_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l2_interfaces_facts
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
                if w["name"] == h["name"]:
                    if dict_diff(w, h):
                        l2_request = self._update_patch_request(w, h)
                        l2_request["data"] = json.dumps(l2_request["data"])
                        requests.append(l2_request)
                    break

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
                if w["name"] == h["name"]:
                    if dict_diff(w, h):
                        l2_request = self._update_patch_request(w, h)
                        l2_request["data"] = json.dumps(l2_request["data"])
                        requests.append(l2_request)
                    have_copy.append(h)
                    break

        for h in have:
            if h not in have_copy:
                l2_delete = self._update_delete_request(h)
                if l2_delete["path"]:
                    l2_delete["data"] = json.dumps(l2_delete["data"])
                    requests.append(l2_delete)

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
                if w["name"] == h["name"]:
                    if dict_diff(h, w):
                        l2_request = self._update_patch_request(w, h)
                        l2_request["data"] = json.dumps(l2_request["data"])
                        requests.append(l2_request)
                    break

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
                    if w["name"] == h["name"]:
                        l2_delete = self._update_delete_request(h)
                        if l2_delete["path"]:
                            l2_delete["data"] = json.dumps(l2_delete["data"])
                            requests.append(l2_delete)
                        break

        else:
            for h in have:
                l2_delete = self._update_delete_request(h)
                if l2_delete["path"]:
                    l2_delete["data"] = json.dumps(l2_delete["data"])
                    requests.append(l2_delete)

        return requests

    def _update_patch_request(self, want, have):

        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, ['vlans', ])
        vlans_facts = facts['ansible_network_resources'].get('vlans')

        vlan_id = []

        for vlan in vlans_facts:
            vlan_id.append(vlan['vlan_id'])

        if want.get("access"):
            if want["access"]["vlan"] in vlan_id:
                l2_request = deepcopy(self.L2_INTERFACE_ACCESS)
                l2_request["data"]["openconfig-vlan:config"]["access-vlan"] = want["access"]["vlan"]
                l2_request["path"] = self.L2_PATH + str(want["name"]) + "/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
            else:
                self._module.fail_json(msg="VLAN %s does not exist" % (want["access"]["vlan"]))

        elif want.get("trunk"):
            if want["trunk"]["native_vlan"]:
                if want["trunk"]["native_vlan"] in vlan_id:
                    l2_request = deepcopy(self.L2_INTERFACE_NATIVE)
                    l2_request["data"]["openconfig-vlan:config"]["native-vlan"] = want["trunk"]["native_vlan"]
                    l2_request["path"] = self.L2_PATH + str(want["name"]) + "/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
                    for vlan in want["trunk"]["trunk_allowed_vlans"]:
                        if int(vlan) in vlan_id:
                            l2_request["data"]["openconfig-vlan:config"]["trunk-vlans"].append(int(vlan))
                        else:
                            self._module.fail_json(msg="VLAN %s does not exist" % (vlan))
                else:
                    self._module.fail_json(msg="VLAN %s does not exist" % (want["trunk"]["native_vlan"]))
            else:
                l2_request = deepcopy(self.L2_INTERFACE_TRUNK)
                l2_request["path"] = self.L2_PATH + str(want["name"]) + "/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"
                for vlan in want["trunk"]["trunk_allowed_vlans"]:
                    if int(vlan) in vlan_id:
                        l2_request["data"]["openconfig-vlan:config"]["trunk-vlans"].append(int(vlan))
                    else:
                        self._module.fail_json(msg="VLAN %s does not exist" % (vlan))
        return l2_request

    def _update_delete_request(self, have):

        l2_request = deepcopy(self.L2_INTERFACE_ACCESS)

        if have["access"] and have["access"]["vlan"] != 1 or have["trunk"] or not have["access"]:
            l2_request["data"]["openconfig-vlan:config"]["access-vlan"] = 1
            l2_request["path"] = self.L2_PATH + str(have["name"]) + "/openconfig-if-ethernet:ethernet/openconfig-vlan:switched-vlan/config"

        return l2_request
