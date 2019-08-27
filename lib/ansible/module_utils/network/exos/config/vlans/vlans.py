#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos_vlans class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

import json
from copy import deepcopy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.exos.facts.facts import Facts
from ansible.module_utils.network.exos.exos import send_requests

class Vlans(ConfigBase):
    """
    The exos_vlans class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'vlans',
    ]

    def __init__(self, module):
        super(Vlans, self).__init__(module)

    def get_vlans_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        vlans_facts = facts['ansible_network_resources'].get('vlans')
        if not vlans_facts:
            return []
        return vlans_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        requests = list()

        existing_vlans_facts = self.get_vlans_facts()
        requests.extend(self.set_config(existing_vlans_facts))
        if requests:
            if not self._module.check_mode:
                send_requests(self._module, requests=requests)
            result['changed'] = True
        result['requests'] = requests
        
        changed_vlans_facts = self.get_vlans_facts()

        result['before'] = existing_vlans_facts
        if result['changed']:
            result['after'] = changed_vlans_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_vlans_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_vlans_facts
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
        if state == 'overridden':
            requests = self._state_overridden(want, have)
        elif state == 'deleted':
            requests = self._state_deleted(want, have)
        elif state == 'merged':
            requests = self._state_merged(want, have)
        elif state == 'replaced':
            requests = self._state_replaced(want, have)
        return requests
        
    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []

        request = {
                "data": {"openconfig-vlan:vlans":{"vlan": [{"config": {"name": None , "status": None , "tpid": "oc-vlan-types:TPID_0x8100", "vlan-id": None }}]}},
            "method": "PATCH",
            "path": None
        }

        for w in want:
            if w.get('vlan_id'):
                for h in have:
                    if w['vlan_id'] == h['vlan_id']:
                        if w['name'] != h['name'] or w['state'] != h['state']:
                            request["data"]["openconfig-vlan:vlans"]["vlan"][0]["config"]["name"] = w["name"]
                            request["data"]["openconfig-vlan:vlans"]["vlan"][0]["config"]["status"] = w["state"].upper()
                            request["data"]["openconfig-vlan:vlans"]["vlan"][0]["config"]["vlan-id"] = w["vlan_id"]
                            request["data"] = json.dumps(request["data"])
                            request["path"] = "/rest/restconf/data/openconfig-vlan:vlans/"
                            requests.append(request)

        return requests

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []

        request_1 = {
                "data": {"openconfig-vlan:vlans": {"vlan": [{"config": {"name": None , "status": None , "tpid": "oc-vlan-types:TPID_0x8100", "vlan-id": None }}]}},
            "method": "PATCH",
            "path": "/rest/restconf/data/openconfig-vlan:vlans/"
        }

        request_2 = {
            "method": "DELETE",
            "path": None
        }

        have_copy = deepcopy(have)

        for w in want:
            if w.get('vlan_id'):
                for h in have_copy:
                    if w['vlan_id'] == h['vlan_id']:
                        if w != h:
                            request_1["data"]["openconfig-vlan:vlans"]["vlan"][0]["config"]["name"] = w["name"]
                            request_1["data"]["openconfig-vlan:vlans"]["vlan"][0]["config"]["status"] = w["state"].upper()
                            request_1["data"]["openconfig-vlan:vlans"]["vlan"][0]["config"]["vlan-id"] = w["vlan_id"]
                            request_1["data"] = json.dumps(request_1["data"])
                            requests.append(request_1)
                        have_copy.remove(h)
        for h in have_copy:
#            if h["vlan_id"] == 1:
 #               continue
  #          else:
            request_2["path"] = "/rest/restconf/data/openconfig-vlan:vlans/vlan=" + str(h["vlan_id"])
            requests.append(request_2)

        return requests

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        requests = []

        request = {
                "data": {"openconfig-vlan:vlans": [{"config": {"name": None , "status": None , "tpid": "oc-vlan-types:TPID_0x8100", "vlan-id": None }}]},
            "method": "POST",
            "path": "/rest/restconf/data/openconfig-vlan:vlans/"
        }

        for w in want:
            check = False
            if w.get('vlan_id'):
                for h in have:
                    if w['vlan_id'] == h['vlan_id']:
                        check = True
                        break
                if not check:
                    request["data"]["openconfig-vlan:vlans"][0]["config"]["name"] = w["name"]
                    request["data"]["openconfig-vlan:vlans"][0]["config"]["status"] = w["state"].upper()
                    request["data"]["openconfig-vlan:vlans"][0]["config"]["vlan-id"] = w["vlan_id"]
                    request["data"] = json.dumps(request["data"])
                    requests.append(request)

        return requests

    @staticmethod
    def _state_deleted( want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        requests = []

        request = {
            "method": "DELETE",
            "path": None 
        }
        if want:
            for w in want:
                check = False
                for h in have:
                    if w["vlan_id"] == h["vlan_id"]:
                        check = True
                        break
                if check:
                    request["path"] = "/rest/restconf/data/openconfig-vlan:vlans/vlan=" + str(w["vlan_id"])
                    requests.append(request)

        else:
            if not have:
                return requests
            for h in have:
                if h["vlan_id"] == 1:
                    continue
                request["path"] = "/rest/restconf/data/openconfig-vlan:vlans/vlan=" + str(h["vlan_id"])
                requests.append(request)

        return requests
        
