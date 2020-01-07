#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos_guest_virtual_machines class
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
from ansible.module_utils.network.exos.utils.utils import search_obj_in_list


class Guest_virtual_machines(ConfigBase):
    """
    The exos_guest_virtual_machines class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'guest_virtual_machines',
    ]

    VM_POST = {
        "data": {"extreme-virtual-service:input": {}},
        "method": "POST",
        "path": None
    }

    VM_PATCH = {
        "data": {"extreme-virtual-service:virtual-service-config": [{}]},
        "method": "PATCH",
        "path": None
    }

    VM_POST_VPORT = {
        "data": {"extreme-virtual-service:vport": [{}]},
        "method": "POST",
        "path": None
    }

    VM_DELETE_VPORT = {
        "method": "DELETE",
        "path": None
    }

    VM_POST_VPORT_VLAN = {"vlan": [{"id": None}]}

    POST_PATH = "/rest/restconf/operations/extreme-virtual-service:"

    PATH = "/rest/restconf/data/extreme-virtual-service:virtual-services-config/virtual-service-config="

    def __init__(self, module):
        super(Guest_virtual_machines, self).__init__(module)

    def get_guest_virtual_machines_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        guest_virtual_machines_facts = facts['ansible_network_resources'].get('guest_virtual_machines')
        if not guest_virtual_machines_facts:
            return []
        return guest_virtual_machines_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        requests = list()

        existing_guest_virtual_machines_facts = self.get_guest_virtual_machines_facts()
        requests.extend(self.set_config(existing_guest_virtual_machines_facts))
        if requests:
            if not self._module.check_mode:
                send_requests(self._module, requests=requests)
            result['changed'] = True
        result['requests'] = requests

        changed_guest_virtual_machines_facts = self.get_guest_virtual_machines_facts()

        result['before'] = existing_guest_virtual_machines_facts
        if result['changed']:
            result['after'] = changed_guest_virtual_machines_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_guest_virtual_machines_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the requests necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_guest_virtual_machines_facts
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
            if w.get("name"):
                h = search_obj_in_list(w['name'], have, 'name')
                if h:
                    diff = dict_diff(h, w)
                    if diff:
                        if w.get("virtual_ports"):
                            if h.get("virtual_ports"):
                                existing_vports = self._compare_vports(w["virtual_ports"], h["virtual_ports"])
                            for vport in w["virtual_ports"]:
                                self._compare_dedicated_ports(vport, have)
                                if vport not in existing_vports:
                                    request_post_vport = self._update_vport_request(vport, w["name"], have)
                                    request_post_vport["data"] = json.dumps(request_post_vport["data"])
                                    requests.append(request_post_vport)
                            for vport in h["virtual_ports"]:
                                if vport not in existing_vports:
                                    request_delete_vport = self._update_vport_delete_request(vport, w["name"])
                                    requests.append(request_delete_vport)
                        request_patch = self._update_existing_config(diff, h, w, have)
                        requests.extend(request_patch)
                else:
                    request_post = self._create_vm(w, have)
                    requests.extend(request_post)

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
            if w.get("name"):
                h = search_obj_in_list(w['name'], have, 'name')
                if h:
                    have_copy.append(h)
                    diff = dict_diff(h, w)
                    if diff:
                        if w.get("virtual_ports"):
                            if h.get("virtual_ports"):
                                existing_vports = self._compare_vports(w["virtual_ports"], h["virtual_ports"])
                            for vport in w["virtual_ports"]:
                                self._compare_dedicated_ports(vport, have)
                                if vport not in existing_vports:
                                    request_post_vport = self._update_vport_request(vport, w["name"], have)
                                    request_post_vport["data"] = json.dumps(request_post_vport["data"])
                                    requests.append(request_post_vport)
                            for vport in h["virtual_ports"]:
                                if vport not in existing_vports:
                                    request_delete_vport = self._update_vport_delete_request(vport, w["name"])
                                    requests.append(request_delete_vport)
                        request_patch = self._update_existing_config(diff, h, w, have)
                        requests.extend(request_patch)
                else:
                    request_post = self._create_vm(w, have)
                    requests.extend(request_post)

        for h in have:
            if h not in have_copy:
                if h['operational_state'] == 'started':
                    request_stop = self._update_stop_request(h)
                    request_stop["data"] = json.dumps(request_stop["data"])
                    requests.append(request_stop)
                request_delete = self._update_delete_request(h)
                request_delete["data"] = json.dumps(request_delete["data"])
                requests.append(request_delete)

        return requests

    def _state_merged(self, want, have):
        """ The request generator when state is merged

        :rtype: A list
        :returns: the requests necessary to merge the provided into
                  the current configuration
        """
        requests = []
        for w in want:
            if w.get("name"):
                h = search_obj_in_list(w['name'], have, 'name')
                if h:
                    diff = dict_diff(h, w)
                    if diff:
                        if w.get("virtual_ports"):
                            existing_vports = []
                            if h.get("virtual_ports"):
                                existing_vports = self._compare_vports(w["virtual_ports"], h["virtual_ports"])
                            for vport in w["virtual_ports"]:
                                self._compare_dedicated_ports(vport, have)
                                if vport not in existing_vports:
                                    request_post_vport = self._update_vport_request(vport, w["name"], have)
                                    request_post_vport["data"] = json.dumps(request_post_vport["data"])
                                    requests.append(request_post_vport)
                        request_patch = self._update_existing_config(diff, h, w, have)
                        requests.extend(request_patch)

                else:
                    request_post = self._create_vm(w, have)
                    requests.extend(request_post)

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
                if w.get('name'):
                    for h in have:
                        if w["name"] == h["name"]:
                            if h['operational_state'] == 'started':
                                request_stop = self._update_stop_request(h)
                                request_stop["data"]["extreme-virtual-service:input"]["forceful"] = str(True).lower()
                                request_stop["data"] = json.dumps(request_stop["data"])
                                requests.append(request_stop)
                            request_delete = self._update_delete_request(h)
                            request_delete["data"] = json.dumps(request_delete["data"])
                            requests.append(request_delete)
                            break
        else:
            if not have:
                return requests
            for h in have:
                if h['operational_state'] == 'started':
                    request_stop = self._update_stop_request(h)
                    request_stop["data"]["extreme-virtual-service:input"]["forceful"] = str(True).lower()
                    request_stop["data"] = json.dumps(request_stop["data"])
                    requests.append(request_stop)
                request_delete = self._update_delete_request(h)
                request_delete["data"] = json.dumps(request_delete["data"])
                requests.append(request_delete)

        return requests

    def _update_post_request(self, want):
        request_install = deepcopy(self.VM_POST)
        request_install["data"]["extreme-virtual-service:input"]["name"] = want["name"]
        request_install["data"]["extreme-virtual-service:input"]["package"] = want["image"]
        request_install["path"] = self.POST_PATH + "install"

        return request_install

    def _update_delete_request(self, have):
        request_delete = deepcopy(self.VM_POST)
        request_delete["data"]["extreme-virtual-service:input"]["name"] = have["name"]
        request_delete["path"] = self.POST_PATH + "uninstall"

        return request_delete

    def _update_start_request(self, want):
        request_start = deepcopy(self.VM_POST)
        request_start["data"]["extreme-virtual-service:input"]["name"] = want["name"]
        request_start["path"] = self.POST_PATH + "start"

        return request_start

    def _update_stop_request(self, have):
        request_stop = deepcopy(self.VM_POST)
        request_stop["data"]["extreme-virtual-service:input"]["name"] = have["name"]
        if have.get("forceful"):
            request_stop["data"]["extreme-virtual-service:input"]["forceful"] = str(True).lower()
        request_stop["path"] = self.POST_PATH + "stop"

        return request_stop

    def _update_restart_request(self, want):
        request_restart = deepcopy(self.VM_POST)
        request_restart["data"]["extreme-virtual-service:input"]["name"] = want["name"]
        if want.get("forceful"):
            request_restart["data"]["extreme-virtual-service:input"]["forceful"] = str(True).lower()
        request_restart["path"] = self.POST_PATH + "restart"

        return request_restart

    def _update_patch_request(self, diff, want, have):
        request_patch = deepcopy(self.VM_PATCH)
        request_patch["path"] = self.PATH + want["name"]
        if diff.get("num_cores"):
            if diff["num_cores"] > 2:
                self._module.fail_json(msg="Requested CPU allocation exceeds node limit of 2")
            request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]["num-cores"] = diff["num_cores"]
        if diff.get("memory_size"):
            if diff["memory_size"] > 9750:
                self._module.fail_json(msg="Requested memory allocation exceeds limit of 9750 MB")
            request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]["memory-size"] = diff["memory_size"]
        if diff.get("vnc"):
            if want["vnc"]["enabled"]:
                if want["vnc"]["port"] < 5900 or want["vnc"]["port"] > 5915:
                    self._module.fail_json(msg="vnc number must be in the range [5900, 5915]")
                for h in have:
                    if h.get("vnc"):
                        if want["vnc"]["port"] == h["vnc"]["port"] and h["operational_state"] == "started":
                            self._module.fail_json(msg="VNC port %s is already in use" % str(want["vnc"]["port"]))
                request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]["vnc-port"] = diff["vnc"]["port"]
            else:
                request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]["vnc-port"] = 0
        if diff.get("auto_start") or not diff.get("auto_start"):
            request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]["enable"] = str(diff["auto_start"]).lower()

        return request_patch

    def _update_vport_request(self, vport, name, have):
        request_post_vport = deepcopy(self.VM_POST_VPORT)
        request_post_vport["path"] = self.PATH + name + "/vports"
        request_post_vport["data"]["extreme-virtual-service:vport"][0]["name"] = str(vport["name"])
        request_post_vport["data"]["extreme-virtual-service:vport"][0]["connect-type"] = vport["type"].upper()
        if vport["type"] == "sriov":
            insight_port_vf = self._collect_insight_port_vf(vport["port"], have)
            if len(insight_port_vf) >= 16:
                self._module.fail_json(msg="Port %s already has 16 active VFs" % str(vport["port"]))
            request_post_vport["data"]["extreme-virtual-service:vport"][0]["port"] = vport["port"]
            if vport.get("vlan"):
                vlan = deepcopy(self.VM_POST_VPORT_VLAN)
                vlan["vlan"][0]["id"] = vport["vlan"]
                request_post_vport["data"]["extreme-virtual-service:vport"][0]["vlans"] = vlan

        return request_post_vport

    def _update_vport_delete_request(self, vport, name):
        request_delete_vport = deepcopy(self.VM_DELETE_VPORT)
        request_delete_vport["path"] = self.PATH + name + "/vports/vport=" + vport["name"]

        return request_delete_vport

    def _collect_insight_port_vf(self, wvport, have):
        insight_port_vf = []
        for h in have:
            if h.get("virtual_ports"):
                for vport in h["virtual_ports"]:
                    if vport["type"] == "sriov" and vport["port"] == str(wvport) and h["operational_state"] == "started":
                        insight_port_vf.append(vport["name"])
        return insight_port_vf

    def _compare_vports(self, wvport, hvport):
        vports = []
        for w in wvport:
            for h in hvport:
                if w["name"] == h["name"]:
                    vports.append(w)
        return vports

    def _compare_dedicated_ports(self, wvport, have):
        for h in have:
            if h.get("virtual_ports"):
                for vport in h["virtual_ports"]:
                    if vport["type"] == "vtd":
                        if ((wvport["type"] == "vtd" and str(wvport["name"]) == str(vport["port"])) or 
                                (wvport["type"] == "sriov" and str(wvport["port"]) == str(vport["port"]))):
                            self._module.fail_json(msg="Port %s is currently in use by a VM as a dedicated port" % str(vport["port"]))
                    elif vport["type"] == "sriov":
                        if wvport["type"] == "vtd" and str(wvport["name"]) == str(vport["port"]):
                            self._module.fail_json(msg="Port %s is already in use with defined VF interfaces" % str(vport["port"]))

    def _create_vm(self, w, have):
        requests = []

        request_post = self._update_post_request(w)
        request_post["data"] = json.dumps(request_post["data"])
        requests.append(request_post)

        if w.get("virtual_ports"):
            for vport in w["virtual_ports"]:
                self._compare_dedicated_ports(vport, have)
                request_post_vport = self._update_vport_request(vport, w["name"], have)
                request_post_vport["data"] = json.dumps(request_post_vport["data"])
                requests.append(request_post_vport)

        request_patch = self._update_patch_request(w, w, have)
        if request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]:
            request_patch["data"] = json.dumps(request_patch["data"])
            requests.append(request_patch)
        if w.get("operational_state") == "started" and not w.get("auto_start"):
            request_start = self._update_start_request(w)
            request_start["data"] = json.dumps(request_start["data"])
            requests.append(request_start)
        if w.get("operational_state") == "stopped" and w.get("auto_start"):
            request_stop = self._update_stop_request(w)
            request_stop["data"] = json.dumps(request_stop["data"])
            requests.append(request_stop)

        return requests

    def _update_existing_config(self, diff, h, w, have):
        requests = []

        if h["operational_state"] == "started" and diff.get("auto_start"):
            del diff["auto_start"]
        request_patch = self._update_patch_request(diff, w, have)
        if request_patch["data"]["extreme-virtual-service:virtual-service-config"][0]:
            request_patch["data"] = json.dumps(request_patch["data"])
            requests.append(request_patch)

        if diff.get("operational_state"):
            if diff["operational_state"] == "stopped" and h["operational_state"] == "started":
                if not diff.get("auto_start"):
                    return requests
                else:
                    request_stop = self._update_stop_request(w)
                    request_stop["data"] = json.dumps(request_stop["data"])
                    requests.append(request_stop)
            elif diff["operational_state"] == "started" and h["operational_state"] == "stopped":
                if diff.get("auto_start"):
                    return requests
                else:
                    request_start = self._update_start_request(w)
                    request_start["data"] = json.dumps(request_start["data"])
                    requests.append(request_start)
            elif diff["operational_state"] == "restarted":
                if h["operational_state"] == "stopped":
                    if diff.get("auto_start"):
                        request_restart = self._update_restart_request(w)
                        request_restart["data"] = json.dumps(request_restart["data"])
                        requests.append(request_restart)
                    else:
                        request_start = self._update_start_request(w)
                        request_start["data"] = json.dumps(request_start["data"])
                        requests.append(request_start)
                elif h["operational_state"] == "started":
                    if not diff.get("auto_start"):
                        request_start = self._update_start_request(w)
                        request_start["data"] = json.dumps(request_start["data"])
                        requests.append(request_start)
                    else:
                        request_restart = self._update_restart_request(w)
                        request_restart["data"] = json.dumps(request_restart["data"])
                        requests.append(request_restart)
        return requests
