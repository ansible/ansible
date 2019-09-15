#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: netapp_e_host
short_description: NetApp E-Series manage eseries hosts
description: Create, update, remove hosts on NetApp E-series storage arrays
version_added: '2.2'
author:
    - Kevin Hulquest (@hulquest)
    - Nathan Swartz (@ndswartz)
extends_documentation_fragment:
    - netapp.eseries
options:
    name:
        description:
            - If the host doesn't yet exist, the label/name to assign at creation time.
            - If the hosts already exists, this will be used to uniquely identify the host to make any required changes
        required: True
        aliases:
            - label
    state:
        description:
            - Set to absent to remove an existing host
            - Set to present to modify or create a new host definition
        choices:
            - absent
            - present
        default: present
        version_added: 2.7
    host_type:
        description:
            - This is the type of host to be mapped
            - Required when C(state=present)
            - Either one of the following names can be specified, Linux DM-MP, VMWare, Windows, Windows Clustered, or a
              host type index which can be found in M(netapp_e_facts)
        type: str
        aliases:
            - host_type_index
    ports:
        description:
            - A list of host ports you wish to associate with the host.
            - Host ports are uniquely identified by their WWN or IQN. Their assignments to a particular host are
             uniquely identified by a label and these must be unique.
        required: False
        suboptions:
            type:
                description:
                  - The interface type of the port to define.
                  - Acceptable choices depend on the capabilities of the target hardware/software platform.
                required: true
                choices:
                  - iscsi
                  - sas
                  - fc
                  - ib
                  - nvmeof
                  - ethernet
            label:
                description:
                    - A unique label to assign to this port assignment.
                required: true
            port:
                description:
                    - The WWN or IQN of the hostPort to assign to this port definition.
                required: true
    force_port:
        description:
            - Allow ports that are already assigned to be re-assigned to your current host
        required: false
        type: bool
        version_added: 2.7
    group:
        description:
            - The unique identifier of the host-group you want the host to be a member of; this is used for clustering.
        required: False
        aliases:
            - cluster
    log_path:
        description:
            - A local path to a file to be used for debug logging
        required: False
        version_added: 2.7
"""

EXAMPLES = """
    - name: Define or update an existing host named 'Host1'
      netapp_e_host:
        ssid: "1"
        api_url: "10.113.1.101:8443"
        api_username: admin
        api_password: myPassword
        name: "Host1"
        state: present
        host_type_index: Linux DM-MP
        ports:
          - type: 'iscsi'
            label: 'PORT_1'
            port: 'iqn.1996-04.de.suse:01:56f86f9bd1fe'
          - type: 'fc'
            label: 'FC_1'
            port: '10:00:FF:7C:FF:FF:FF:01'
          - type: 'fc'
            label: 'FC_2'
            port: '10:00:FF:7C:FF:FF:FF:00'

    - name: Ensure a host named 'Host2' doesn't exist
      netapp_e_host:
        ssid: "1"
        api_url: "10.113.1.101:8443"
        api_username: admin
        api_password: myPassword
        name: "Host2"
        state: absent
"""

RETURN = """
msg:
    description:
        - A user-readable description of the actions performed.
    returned: on success
    type: str
    sample: The host has been created.
id:
    description:
        - the unique identifier of the host on the E-Series storage-system
    returned: on success when state=present
    type: str
    sample: 00000000600A098000AAC0C3003004700AD86A52
    version_added: "2.6"

ssid:
    description:
        - the unique identifier of the E-Series storage-system with the current api
    returned: on success
    type: str
    sample: 1
    version_added: "2.6"

api_url:
    description:
        - the url of the API that this request was processed by
    returned: on success
    type: str
    sample: https://webservices.example.com:8443
    version_added: "2.6"
"""
import json
import logging
import re
from pprint import pformat

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class Host(object):
    HOST_TYPE_INDEXES = {"linux dm-mp": 28, "vmware": 10, "windows": 1, "windows clustered": 8}

    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            group=dict(type='str', required=False, aliases=['cluster']),
            ports=dict(type='list', required=False),
            force_port=dict(type='bool', default=False),
            name=dict(type='str', required=True, aliases=['label']),
            host_type_index=dict(type='str', aliases=['host_type']),
            log_path=dict(type='str', required=False),
        ))

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
        self.check_mode = self.module.check_mode
        args = self.module.params
        self.group = args['group']
        self.ports = args['ports']
        self.force_port = args['force_port']
        self.name = args['name']
        self.state = args['state']
        self.ssid = args['ssid']
        self.url = args['api_url']
        self.user = args['api_username']
        self.pwd = args['api_password']
        self.certs = args['validate_certs']

        self.post_body = dict()
        self.all_hosts = list()
        self.host_obj = dict()
        self.newPorts = list()
        self.portsForUpdate = list()
        self.portsForRemoval = list()

        # Update host type with the corresponding index
        host_type = args['host_type_index']
        if host_type:
            host_type = host_type.lower()
            if host_type in [key.lower() for key in list(self.HOST_TYPE_INDEXES.keys())]:
                self.host_type_index = self.HOST_TYPE_INDEXES[host_type]
            elif host_type.isdigit():
                self.host_type_index = int(args['host_type_index'])
            else:
                self.module.fail_json(msg="host_type must be either a host type name or host type index found integer"
                                          " the documentation.")

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)
        if args['log_path']:
            logging.basicConfig(
                level=logging.DEBUG, filename=args['log_path'], filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

        # Ensure when state==present then host_type_index is defined
        if self.state == "present" and self.host_type_index is None:
            self.module.fail_json(msg="Host_type_index is required when state=='present'. Array Id: [%s]" % self.ssid)

        # Fix port representation if they are provided with colons
        if self.ports is not None:
            for port in self.ports:
                port['label'] = port['label'].lower()
                port['type'] = port['type'].lower()
                port['port'] = port['port'].lower()

                # Determine whether address is 16-byte WWPN and, if so, remove
                if re.match(r'^(0x)?[0-9a-f]{16}$', port['port'].replace(':', '')):
                    port['port'] = port['port'].replace(':', '').replace('0x', '')

    def valid_host_type(self):
        host_types = None
        try:
            (rc, host_types) = request(self.url + 'storage-systems/%s/host-types' % self.ssid, url_password=self.pwd,
                                       url_username=self.user, validate_certs=self.certs, headers=HEADERS)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to get host types. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))

        try:
            match = list(filter(lambda host_type: host_type['index'] == self.host_type_index, host_types))[0]
            return True
        except IndexError:
            self.module.fail_json(msg="There is no host type with index %s" % self.host_type_index)

    def assigned_host_ports(self, apply_unassigning=False):
        """Determine if the hostPorts requested have already been assigned and return list of required used ports."""
        used_host_ports = {}
        for host in self.all_hosts:
            if host['label'] != self.name:
                for host_port in host['hostSidePorts']:
                    for port in self.ports:
                        if port['port'] == host_port["address"] or port['label'] == host_port['label']:
                            if not self.force_port:
                                self.module.fail_json(msg="There are no host ports available OR there are not enough"
                                                          " unassigned host ports")
                            else:
                                # Determine port reference
                                port_ref = [port["hostPortRef"] for port in host["ports"]
                                            if port["hostPortName"] == host_port["address"]]
                                port_ref.extend([port["initiatorRef"] for port in host["initiators"]
                                                 if port["nodeName"]["iscsiNodeName"] == host_port["address"]])

                                # Create dictionary of hosts containing list of port references
                                if host["hostRef"] not in used_host_ports.keys():
                                    used_host_ports.update({host["hostRef"]: port_ref})
                                else:
                                    used_host_ports[host["hostRef"]].extend(port_ref)
            else:
                for host_port in host['hostSidePorts']:
                    for port in self.ports:
                        if ((host_port['label'] == port['label'] and host_port['address'] != port['port']) or
                                (host_port['label'] != port['label'] and host_port['address'] == port['port'])):
                            if not self.force_port:
                                self.module.fail_json(msg="There are no host ports available OR there are not enough"
                                                          " unassigned host ports")
                            else:
                                # Determine port reference
                                port_ref = [port["hostPortRef"] for port in host["ports"]
                                            if port["hostPortName"] == host_port["address"]]
                                port_ref.extend([port["initiatorRef"] for port in host["initiators"]
                                                 if port["nodeName"]["iscsiNodeName"] == host_port["address"]])

                                # Create dictionary of hosts containing list of port references
                                if host["hostRef"] not in used_host_ports.keys():
                                    used_host_ports.update({host["hostRef"]: port_ref})
                                else:
                                    used_host_ports[host["hostRef"]].extend(port_ref)

        # Unassign assigned ports
        if apply_unassigning:
            for host_ref in used_host_ports.keys():
                try:
                    rc, resp = request(self.url + 'storage-systems/%s/hosts/%s' % (self.ssid, host_ref),
                                       url_username=self.user, url_password=self.pwd, headers=HEADERS,
                                       validate_certs=self.certs, method='POST',
                                       data=json.dumps({"portsToRemove": used_host_ports[host_ref]}))
                except Exception as err:
                    self.module.fail_json(msg="Failed to unassign host port. Host Id [%s]. Array Id [%s]. Ports [%s]."
                                              " Error [%s]." % (self.host_obj['id'], self.ssid,
                                                                used_host_ports[host_ref], to_native(err)))

        return used_host_ports

    def group_id(self):
        if self.group:
            try:
                (rc, all_groups) = request(self.url + 'storage-systems/%s/host-groups' % self.ssid,
                                           url_password=self.pwd,
                                           url_username=self.user, validate_certs=self.certs, headers=HEADERS)
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to get host groups. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))

            try:
                group_obj = list(filter(lambda group: group['name'] == self.group, all_groups))[0]
                return group_obj['id']
            except IndexError:
                self.module.fail_json(msg="No group with the name: %s exists" % self.group)
        else:
            # Return the value equivalent of no group
            return "0000000000000000000000000000000000000000"

    def host_exists(self):
        """Determine if the requested host exists
        As a side effect, set the full list of defined hosts in 'all_hosts', and the target host in 'host_obj'.
        """
        match = False
        all_hosts = list()

        try:
            (rc, all_hosts) = request(self.url + 'storage-systems/%s/hosts' % self.ssid, url_password=self.pwd,
                                      url_username=self.user, validate_certs=self.certs, headers=HEADERS)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to determine host existence. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))

        # Augment the host objects
        for host in all_hosts:
            for port in host['hostSidePorts']:
                port['type'] = port['type'].lower()
                port['address'] = port['address'].lower()
                port['label'] = port['label'].lower()

            # Augment hostSidePorts with their ID (this is an omission in the API)
            ports = dict((port['label'], port['id']) for port in host['ports'])
            ports.update((port['label'], port['id']) for port in host['initiators'])

            for host_side_port in host['hostSidePorts']:
                if host_side_port['label'] in ports:
                    host_side_port['id'] = ports[host_side_port['label']]

            if host['label'] == self.name:
                self.host_obj = host
                match = True

        self.all_hosts = all_hosts
        return match

    def needs_update(self):
        """Determine whether we need to update the Host object
        As a side effect, we will set the ports that we need to update (portsForUpdate), and the ports we need to add
        (newPorts), on self.
        """
        changed = False
        if (self.host_obj["clusterRef"].lower() != self.group_id().lower() or
                self.host_obj["hostTypeIndex"] != self.host_type_index):
            self._logger.info("Either hostType or the clusterRef doesn't match, an update is required.")
            changed = True
        current_host_ports = dict((port["id"], {"type": port["type"], "port": port["address"], "label": port["label"]})
                                  for port in self.host_obj["hostSidePorts"])

        if self.ports:
            for port in self.ports:
                for current_host_port_id in current_host_ports.keys():
                    if port == current_host_ports[current_host_port_id]:
                        current_host_ports.pop(current_host_port_id)
                        break
                    elif port["port"] == current_host_ports[current_host_port_id]["port"]:
                        if self.port_on_diff_host(port) and not self.force_port:
                            self.module.fail_json(msg="The port you specified [%s] is associated with a different host."
                                                      " Specify force_port as True or try a different port spec" % port)

                        if (port["label"] != current_host_ports[current_host_port_id]["label"] or
                                port["type"] != current_host_ports[current_host_port_id]["type"]):
                            current_host_ports.pop(current_host_port_id)
                            self.portsForUpdate.append({"portRef": current_host_port_id, "port": port["port"],
                                                        "label": port["label"], "hostRef": self.host_obj["hostRef"]})
                            break
                else:
                    self.newPorts.append(port)

            self.portsForRemoval = list(current_host_ports.keys())
            changed = any([self.newPorts, self.portsForUpdate, self.portsForRemoval, changed])

        return changed

    def port_on_diff_host(self, arg_port):
        """ Checks to see if a passed in port arg is present on a different host """
        for host in self.all_hosts:
            # Only check 'other' hosts
            if host['name'] != self.name:
                for port in host['hostSidePorts']:
                    # Check if the port label is found in the port dict list of each host
                    if arg_port['label'] == port['label'] or arg_port['port'] == port['address']:
                        self.other_host = host
                        return True
        return False

    def update_host(self):
        self._logger.info("Beginning the update for host=%s.", self.name)

        if self.ports:

            # Remove ports that need reassigning from their current host.
            self.assigned_host_ports(apply_unassigning=True)

            self.post_body["portsToUpdate"] = self.portsForUpdate
            self.post_body["ports"] = self.newPorts
            self._logger.info("Requested ports: %s", pformat(self.ports))
        else:
            self._logger.info("No host ports were defined.")

        if self.group:
            self.post_body['groupId'] = self.group_id()

        self.post_body['hostType'] = dict(index=self.host_type_index)

        api = self.url + 'storage-systems/%s/hosts/%s' % (self.ssid, self.host_obj['id'])
        self._logger.info("POST => url=%s, body=%s.", api, pformat(self.post_body))

        if not self.check_mode:
            try:
                (rc, self.host_obj) = request(api, url_username=self.user, url_password=self.pwd, headers=HEADERS,
                                              validate_certs=self.certs, method='POST', data=json.dumps(self.post_body))
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to update host. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))

        payload = self.build_success_payload(self.host_obj)
        self.module.exit_json(changed=True, **payload)

    def create_host(self):
        self._logger.info("Creating host definition.")

        # Remove ports that need reassigning from their current host.
        self.assigned_host_ports(apply_unassigning=True)

        # needs_reassignment = False
        post_body = dict(
            name=self.name,
            hostType=dict(index=self.host_type_index),
            groupId=self.group_id(),
        )

        if self.ports:
            post_body.update(ports=self.ports)

        api = self.url + "storage-systems/%s/hosts" % self.ssid
        self._logger.info('POST => url=%s, body=%s', api, pformat(post_body))

        if not self.check_mode:
            if not self.host_exists():
                try:
                    (rc, self.host_obj) = request(api, method='POST', url_username=self.user, url_password=self.pwd, validate_certs=self.certs,
                                                  data=json.dumps(post_body), headers=HEADERS)
                except Exception as err:
                    self.module.fail_json(
                        msg="Failed to create host. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))
            else:
                payload = self.build_success_payload(self.host_obj)
                self.module.exit_json(changed=False, msg="Host already exists. Id [%s]. Host [%s]." % (self.ssid, self.name), **payload)

        payload = self.build_success_payload(self.host_obj)
        self.module.exit_json(changed=True, msg='Host created.', **payload)

    def remove_host(self):
        try:
            (rc, resp) = request(self.url + "storage-systems/%s/hosts/%s" % (self.ssid, self.host_obj['id']),
                                 method='DELETE',
                                 url_username=self.user, url_password=self.pwd, validate_certs=self.certs)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to remove host.  Host[%s]. Array Id [%s]. Error [%s]." % (self.host_obj['id'],
                                                                                      self.ssid,
                                                                                      to_native(err)))

    def build_success_payload(self, host=None):
        keys = ['id']
        if host is not None:
            result = dict((key, host[key]) for key in keys)
        else:
            result = dict()
        result['ssid'] = self.ssid
        result['api_url'] = self.url
        return result

    def apply(self):
        if self.state == 'present':
            if self.host_exists():
                if self.needs_update() and self.valid_host_type():
                    self.update_host()
                else:
                    payload = self.build_success_payload(self.host_obj)
                    self.module.exit_json(changed=False, msg="Host already present; no changes required.", **payload)
            elif self.valid_host_type():
                self.create_host()
        else:
            payload = self.build_success_payload()
            if self.host_exists():
                self.remove_host()
                self.module.exit_json(changed=True, msg="Host removed.", **payload)
            else:
                self.module.exit_json(changed=False, msg="Host already absent.", **payload)


def main():
    host = Host()
    host.apply()


if __name__ == '__main__':
    main()
