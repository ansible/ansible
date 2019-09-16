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
author: Kevin Hulquest (@hulquest)
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
    host_type_index:
        description:
            - The index that maps to host type you wish to create. It is recommended to use the M(netapp_e_facts) module to gather this information.
              Alternatively you can use the WSP portal to retrieve the information.
            - Required when C(state=present)
        aliases:
            - host_type
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
        api_username: "admin"
        api_password: "myPassword"
        name: "Host1"
        state: present
        host_type_index: 28
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
        api_username: "admin"
        api_password: "myPassword"
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
from pprint import pformat

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class Host(object):
    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            group=dict(type='str', required=False, aliases=['cluster']),
            ports=dict(type='list', required=False),
            force_port=dict(type='bool', default=False),
            name=dict(type='str', required=True, aliases=['label']),
            host_type_index=dict(type='int', aliases=['host_type']),
            log_path=dict(type='str', required=False),
        ))

        required_if = [
            ["state", "absent", ["name"]],
            ["state", "present", ["name", "host_type"]]
        ]

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)
        self.check_mode = self.module.check_mode
        args = self.module.params
        self.group = args['group']
        self.ports = args['ports']
        self.force_port = args['force_port']
        self.name = args['name']
        self.host_type_index = args['host_type_index']
        self.state = args['state']
        self.ssid = args['ssid']
        self.url = args['api_url']
        self.user = args['api_username']
        self.pwd = args['api_password']
        self.certs = args['validate_certs']
        self.post_body = dict()

        self.all_hosts = list()
        self.newPorts = list()
        self.portsForUpdate = list()
        self.force_port_update = False

        log_path = args['log_path']

        # logging setup
        self._logger = logging.getLogger(self.__class__.__name__)

        if log_path:
            logging.basicConfig(
                level=logging.DEBUG, filename=log_path, filemode='w',
                format='%(relativeCreated)dms %(levelname)s %(module)s.%(funcName)s:%(lineno)d\n %(message)s')

        if not self.url.endswith('/'):
            self.url += '/'

        # Fix port representation if they are provided with colons
        if self.ports is not None:
            for port in self.ports:
                if port['type'] != 'iscsi':
                    port['port'] = port['port'].replace(':', '')

    @property
    def valid_host_type(self):
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

    @property
    def host_ports_available(self):
        """Determine if the hostPorts requested have already been assigned"""
        for host in self.all_hosts:
            if host['label'] != self.name:
                for host_port in host['hostSidePorts']:
                    for port in self.ports:
                        if (port['port'] == host_port['address'] or port['label'] == host_port['label']):
                            if not self.force_port:
                                self.module.fail_json(
                                    msg="There are no host ports available OR there are not enough unassigned host ports")
                            else:
                                return False
        return True

    @property
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

    @property
    def host_exists(self):
        """Determine if the requested host exists
        As a side effect, set the full list of defined hosts in 'all_hosts', and the target host in 'host_obj'.
        """
        all_hosts = list()
        try:
            (rc, all_hosts) = request(self.url + 'storage-systems/%s/hosts' % self.ssid, url_password=self.pwd,
                                      url_username=self.user, validate_certs=self.certs, headers=HEADERS)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to determine host existence. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))

        self.all_hosts = all_hosts

        # Augment the host objects
        for host in all_hosts:
            # Augment hostSidePorts with their ID (this is an omission in the API)
            host_side_ports = host['hostSidePorts']
            initiators = dict((port['label'], port['id']) for port in host['initiators'])
            ports = dict((port['label'], port['id']) for port in host['ports'])
            ports.update(initiators)
            for port in host_side_ports:
                if port['label'] in ports:
                    port['id'] = ports[port['label']]

        try:  # Try to grab the host object
            self.host_obj = list(filter(lambda host: host['label'] == self.name, all_hosts))[0]
            return True
        except IndexError:
            # Host with the name passed in does not exist
            return False

    @property
    def needs_update(self):
        """Determine whether we need to update the Host object
        As a side effect, we will set the ports that we need to update (portsForUpdate), and the ports we need to add
        (newPorts), on self.
        :return:
        """
        needs_update = False

        if self.host_obj['clusterRef'] != self.group_id or self.host_obj['hostTypeIndex'] != self.host_type_index:
            self._logger.info("Either hostType or the clusterRef doesn't match, an update is required.")
            needs_update = True

        if self.ports:
            self._logger.debug("Determining if ports need to be updated.")
            # Find the names of all defined ports
            port_names = set(port['label'] for port in self.host_obj['hostSidePorts'])
            port_addresses = set(port['address'] for port in self.host_obj['hostSidePorts'])

            # If we have ports defined and there are no ports on the host object, we need an update
            if not self.host_obj['hostSidePorts']:
                needs_update = True
            for arg_port in self.ports:
                # First a quick check to see if the port is mapped to a different host
                if not self.port_on_diff_host(arg_port):
                    # The port (as defined), currently does not exist
                    if arg_port['label'] not in port_names:
                        needs_update = True
                        # This port has not been defined on the host at all
                        if arg_port['port'] not in port_addresses:
                            self.newPorts.append(arg_port)
                        # A port label update has been requested
                        else:
                            self.portsForUpdate.append(arg_port)
                    # The port does exist, does it need to be updated?
                    else:
                        for obj_port in self.host_obj['hostSidePorts']:
                            if arg_port['label'] == obj_port['label']:
                                # Confirmed that port arg passed in exists on the host
                                # port_id = self.get_port_id(obj_port['label'])
                                if arg_port['type'] != obj_port['type']:
                                    needs_update = True
                                    self.portsForUpdate.append(arg_port)
                                if 'iscsiChapSecret' in arg_port:
                                    # No way to know the current secret attr, so always return True just in case
                                    needs_update = True
                                    self.portsForUpdate.append(arg_port)
                else:
                    # If the user wants the ports to be reassigned, do it
                    if self.force_port:
                        self.force_port_update = True
                        needs_update = True
                    else:
                        self.module.fail_json(
                            msg="The port you specified:\n%s\n is associated with a different host. Specify force_port"
                                " as True or try a different port spec" % arg_port
                        )
        self._logger.debug("Is an update required ?=%s", needs_update)
        return needs_update

    def get_ports_on_host(self):
        """Retrieve the hostPorts that are defined on the target host
        :return: a list of hostPorts with their labels and ids
        Example:
        [
            {
                'name': 'hostPort1',
                'id': '0000000000000000000000'
            }
        ]
        """
        ret = dict()
        for host in self.all_hosts:
            if host['name'] == self.name:
                ports = host['hostSidePorts']
                for port in ports:
                    ret[port['address']] = {'label': port['label'], 'id': port['id'], 'address': port['address']}
        return ret

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

    def get_port(self, label, address):
        for host in self.all_hosts:
            for port in host['hostSidePorts']:
                if port['label'] == label or port['address'] == address:
                    return port

    def reassign_ports(self, apply=True):
        post_body = dict(
            portsToUpdate=dict()
        )

        for port in self.ports:
            if self.port_on_diff_host(port):
                host_port = self.get_port(port['label'], port['port'])
                post_body['portsToUpdate'].update(dict(
                    portRef=host_port['id'],
                    hostRef=self.host_obj['id'],
                    label=port['label']
                    # Doesn't yet address port identifier or chap secret
                ))

        self._logger.info("reassign_ports: %s", pformat(post_body))

        if apply:
            try:
                (rc, self.host_obj) = request(
                    self.url + 'storage-systems/%s/hosts/%s' % (self.ssid, self.host_obj['id']),
                    url_username=self.user, url_password=self.pwd, headers=HEADERS,
                    validate_certs=self.certs, method='POST', data=json.dumps(post_body))
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to reassign host port. Host Id [%s]. Array Id [%s]. Error [%s]." % (
                        self.host_obj['id'], self.ssid, to_native(err)))

        return post_body

    def update_host(self):
        self._logger.debug("Beginning the update for host=%s.", self.name)

        if self.ports:
            self._logger.info("Requested ports: %s", pformat(self.ports))
            if self.host_ports_available or self.force_port:
                self.reassign_ports(apply=True)
                # Make sure that only ports that aren't being reassigned are passed into the ports attr
                host_ports = self.get_ports_on_host()
                ports_for_update = list()
                self._logger.info("Ports on host: %s", pformat(host_ports))
                for port in self.portsForUpdate:
                    if port['port'] in host_ports:
                        defined_port = host_ports.get(port['port'])
                        defined_port.update(port)
                        defined_port['portRef'] = defined_port['id']
                        ports_for_update.append(defined_port)
                self._logger.info("Ports to update: %s", pformat(ports_for_update))
                self._logger.info("Ports to define: %s", pformat(self.newPorts))
                self.post_body['portsToUpdate'] = ports_for_update
                self.post_body['ports'] = self.newPorts
        else:
            self._logger.debug("No host ports were defined.")

        if self.group:
            self.post_body['groupId'] = self.group_id

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
        needs_reassignment = False
        post_body = dict(
            name=self.name,
            hostType=dict(index=self.host_type_index),
            groupId=self.group_id,
        )
        if self.ports:
            # Check that all supplied port args are valid
            if self.host_ports_available:
                self._logger.info("The host-ports requested are available.")
                post_body.update(ports=self.ports)
            elif not self.force_port:
                self.module.fail_json(
                    msg="You supplied ports that are already in use."
                        " Supply force_port to True if you wish to reassign the ports")
            else:
                needs_reassignment = True

        api = self.url + "storage-systems/%s/hosts" % self.ssid
        self._logger.info('POST => url=%s, body=%s', api, pformat(post_body))

        if not (self.host_exists and self.check_mode):
            try:
                (rc, self.host_obj) = request(api, method='POST',
                                              url_username=self.user, url_password=self.pwd, validate_certs=self.certs,
                                              data=json.dumps(post_body), headers=HEADERS)
            except Exception as err:
                self.module.fail_json(
                    msg="Failed to create host. Array Id [%s]. Error [%s]." % (self.ssid, to_native(err)))
        else:
            payload = self.build_success_payload(self.host_obj)
            self.module.exit_json(changed=False,
                                  msg="Host already exists. Id [%s]. Host [%s]." % (self.ssid, self.name), **payload)

        self._logger.info("Created host, beginning port re-assignment.")
        if needs_reassignment:
            self.reassign_ports()

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
            if self.host_exists:
                if self.needs_update and self.valid_host_type:
                    self.update_host()
                else:
                    payload = self.build_success_payload(self.host_obj)
                    self.module.exit_json(changed=False, msg="Host already present; no changes required.", **payload)
            elif self.valid_host_type:
                self.create_host()
        else:
            payload = self.build_success_payload()
            if self.host_exists:
                self.remove_host()
                self.module.exit_json(changed=True, msg="Host removed.", **payload)
            else:
                self.module.exit_json(changed=False, msg="Host already absent.", **payload)


def main():
    host = Host()
    host.apply()


if __name__ == '__main__':
    main()
