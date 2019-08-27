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
from ansible.module_utils.network.common.utils import to_list, dict_diff
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

    VLAN_POST = {
        "data": {"openconfig-vlan:vlan": []},
        "method": "POST",
        "path": "/rest/restconf/data/openconfig-vlan:vlans/"
    }

    VLAN_PATCH = {
        "data": {"openconfig-vlan:vlans":{"vlan": []}},
        "method": "PATCH",
        "path": "/rest/restconf/data/openconfig-vlan:vlans/" 
    } 

    VLAN_DELETE = {
        "method": "DELETE"
        "path": None
    }

    DEL_PATH = "/rest/restconf/data/openconfig-vlan:vlans/vlan="

    REQUEST_BODY = {
        "config": {"name": None , "status": None , "tpid": "oc-vlan-types:TPID_0x8100", "vlan-id": None }
        }

    def __init__(self, module):
        super(Vlans, self).__init__(module)

    def get_vlans_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
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
    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []

        request_post = deepcopy(self.VLAN_POST)
        request_patch = deepcopy(self.VLAN_PATCH)
        request_body = deepcopy(self.REQUEST_BODY)

        for w in want:
            if w.get('vlan_id'):
                h = self._search_vlan_in_list(w['vlan_id'], have)
                if h:
                    if dict_diff(w, h):
                        request_body = self._update_vlan_config_body(w, request_body)
                        request_patch["data"]["openconfig-vlan:vlans"]["vlan"].append(request_body)
                else:
                    request_body = self._update_vlan_config_body(w, request_body)
                    request_post["data"]["openconfig-vlan:vlans"].append(request_body)            

        if len(request_patch["data"]["openconfig-vlan:vlans"]["vlan"]):
            request_patch["data"] = json.dumps(request_patch["data"])
            requests.append(request_patch)
        
        if len(request_post["data"]["openconfig-vlan:vlans"]):
            request_post["data"] = json.dumps(request_post["data"])
            requests.append(request_post)              
                            
        return requests

    @staticmethod
    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        requests = []

        request_post = deepcopy(self.VLAN_POST)
        request_patch = deepcopy(self.VLAN_PATCH)
        request_body = deepcopy(self.REQUEST_BODY)
        request_delete = deepcopy(self.VLAN_DELETE)
        have_copy = []
        for w in want:
            if w.get('vlan_id'):
                h = self._search_vlan_in_list(w['vlan_id'], have)
                if h:
                    if dict_diff(w, h):
                        request_body = self._update_vlan_config_body(w, request_body)
                        request_patch["data"]["openconfig-vlan:vlans"]["vlan"].append(request_body)
                    have_copy.append(h)
                else:
                    request_body = self._update_vlan_config_body(w, request_body)
                    request_post["data"]["openconfig-vlan:vlans"].append(request_body)            
        
        have_del = list(set(have)-set(have_copy))
        if have_del:
            for h in have_del:
                request_delete["path"] = self.DEL_PATH + str(h['vlan_id'])
                requests.append(request_delete)

        if len(request_patch["data"]["openconfig-vlan:vlans"]["vlan"]):
            request_patch["data"] = json.dumps(request_patch["data"])
            requests.append(request_patch)
        
        if len(request_post["data"]["openconfig-vlan:vlans"]):
            request_post["data"] = json.dumps(request_post["data"])
            requests.append(request_post)
        
        return requests

    @staticmethod
    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        requests = []

        request_post = deepcopy(self.VLAN_POST)
        request_body = deepcopy(self.REQUEST_BODY)

        for w in want: 
            if w.get('vlan_id'):
                request_body = self._update_vlan_config_body(w, request_body)
                request_post["data"]["openconfig-vlan:vlans"].append(request_body)

        if len(request_post["data"]["openconfig-vlan:vlans"]):
            request_post["data"] = json.dumps(request_post["data"])
            requests.append(request_post)  

        return requests

    @staticmethod
    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        requests = []

        request_delete = deepcopy(self.VLAN_DELETE)
        if want:
            for w in want:
                if w.get('vlan_id'):
                    h = self._search_vlan_in_list(w['vlan_id'], have)
                    if h:
                        request_delete["path"] = self.DEL_PATH + str(h['vlan_id'])
                        requests.append(request_delete)

        else:
            if not have:
                return requests
            for h in have:
                request_delete["path"] = self.DEL_PATH + str(h['vlan_id'])
                requests.append(request_delete)

        return requests

    def _update_vlan_config_body(self, want, request):
        request["config"]["name"] = want["name"]
        request["config"]["status"] = want["state"]
        request["config"]["vlan-id"] = want["vlan_id"]
        return request

    def _search_vlan_in_list(vlan_id, lst):
        for o in lst:
            if o['vlan_id'] == vlan_id:
                return o
        return None
