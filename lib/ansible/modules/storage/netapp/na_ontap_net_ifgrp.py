#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = """
module: na_ontap_net_ifgrp
short_description: NetApp Ontap modify network interface group
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, modify ports, destroy the network interface group
options:
  state:
    description:
    - Whether the specified network interface group should exist or not.
    choices: ['present', 'absent']
    default: present

  distribution_function:
    description:
    - Specifies the traffic distribution function for the ifgrp.
    choices: ['mac', 'ip', 'sequential', 'port']

  name:
    description:
    - Specifies the interface group name.
    required: true

  mode:
    description:
    - Specifies the link policy for the ifgrp.

  node:
    description:
    - Specifies the name of node.
    required: true

  ports:
    aliases:
    - port
    description:
    - List of expected ports to be present in the interface group.
    - If a port is present in this list, but not on the target, it will be added.
    - If a port is not in the list, but present on the target, it will be removed.
    - Make sure the list contains all ports you want to see on the target.
    version_added: '2.8'
"""

EXAMPLES = """
    - name: create ifgrp
      na_ontap_net_ifgrp:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        distribution_function: ip
        name: a0c
        ports: [e0a]
        mode: multimode
        node: "{{ Vsim node name }}"
    - name: modify ports in an ifgrp
      na_ontap_net_ifgrp:
        state: present
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        distribution_function: ip
        name: a0c
        port: [e0a, e0c]
        mode: multimode
        node: "{{ Vsim node name }}"
    - name: delete ifgrp
      na_ontap_net_ifgrp:
        state: absent
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        hostname: "{{ netapp_hostname }}"
        name: a0c
        node: "{{ Vsim node name }}"
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapIfGrp(object):
    """
        Create, Modifies and Destroys a IfGrp
    """
    def __init__(self):
        """
            Initialize the Ontap IfGrp class
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            distribution_function=dict(required=False, type='str', choices=['mac', 'ip', 'sequential', 'port']),
            name=dict(required=True, type='str'),
            mode=dict(required=False, type='str'),
            node=dict(required=True, type='str'),
            ports=dict(required=False, type='list', aliases=["port"]),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['distribution_function', 'mode'])
            ],
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)
        return

    def get_if_grp(self):
        """
        Return details about the if_group
        :param:
            name : Name of the if_group

        :return: Details about the if_group. None if not found.
        :rtype: dict
        """
        if_group_iter = netapp_utils.zapi.NaElement('net-port-get-iter')
        if_group_info = netapp_utils.zapi.NaElement('net-port-info')
        if_group_info.add_new_child('port', self.parameters['name'])
        if_group_info.add_new_child('port-type', 'if_group')
        if_group_info.add_new_child('node', self.parameters['node'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(if_group_info)
        if_group_iter.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(if_group_iter, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting if_group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

        return_value = None

        if result.get_child_by_name('num-records') and int(result['num-records']) >= 1:
            if_group_attributes = result['attributes-list']['net-port-info']
            return_value = {
                'name': if_group_attributes['port'],
                'distribution_function': if_group_attributes['ifgrp-distribution-function'],
                'mode': if_group_attributes['ifgrp-mode'],
                'node': if_group_attributes['node'],
            }

        return return_value

    def get_if_grp_ports(self):
        """
        Return ports of the if_group
        :param:
            name : Name of the if_group
        :return: Ports of the if_group. None if not found.
        :rtype: dict
        """
        if_group_iter = netapp_utils.zapi.NaElement('net-port-ifgrp-get')
        if_group_iter.add_new_child('ifgrp-name', self.parameters['name'])
        if_group_iter.add_new_child('node', self.parameters['node'])
        try:
            result = self.server.invoke_successfully(if_group_iter, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting if_group ports %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

        port_list = []
        if result.get_child_by_name('attributes'):
            if_group_attributes = result['attributes']['net-ifgrp-info']
            if if_group_attributes.get_child_by_name('ports'):
                ports = if_group_attributes.get_child_by_name('ports').get_children()
                for each in ports:
                    port_list.append(each.get_content())
        return {'ports': port_list}

    def create_if_grp(self):
        """
        Creates a new ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-create")
        route_obj.add_new_child("distribution-function", self.parameters['distribution_function'])
        route_obj.add_new_child("ifgrp-name", self.parameters['name'])
        route_obj.add_new_child("mode", self.parameters['mode'])
        route_obj.add_new_child("node", self.parameters['node'])
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating if_group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        for port in self.parameters.get('ports'):
            self.add_port_to_if_grp(port)

    def delete_if_grp(self):
        """
        Deletes a ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-destroy")
        route_obj.add_new_child("ifgrp-name", self.parameters['name'])
        route_obj.add_new_child("node", self.parameters['node'])
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting if_group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def add_port_to_if_grp(self, port):
        """
        adds port to a ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-add-port")
        route_obj.add_new_child("ifgrp-name", self.parameters['name'])
        route_obj.add_new_child("port", port)
        route_obj.add_new_child("node", self.parameters['node'])
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding port %s to if_group %s: %s' %
                                      (port, self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_ports(self, current_ports):
        add_ports = set(self.parameters['ports']) - set(current_ports)
        remove_ports = set(current_ports) - set(self.parameters['ports'])
        for port in add_ports:
            self.add_port_to_if_grp(port)
        for port in remove_ports:
            self.remove_port_to_if_grp(port)

    def remove_port_to_if_grp(self, port):
        """
        removes port from a ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-remove-port")
        route_obj.add_new_child("ifgrp-name", self.parameters['name'])
        route_obj.add_new_child("port", port)
        route_obj.add_new_child("node", self.parameters['node'])
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing port %s to if_group %s: %s' %
                                      (port, self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_net_ifgrp", cserver)

    def apply(self):
        self.autosupport_log()
        current, modify = self.get_if_grp(), None
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action is None and self.parameters['state'] == 'present':
            current_ports = self.get_if_grp_ports()
            modify = self.na_helper.get_modified_attributes(current_ports, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_if_grp()
                elif cd_action == 'delete':
                    self.delete_if_grp()
                elif modify:
                    self.modify_ports(current_ports['ports'])
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Creates the NetApp Ontap Net Route object and runs the correct play task
    """
    obj = NetAppOntapIfGrp()
    obj.apply()


if __name__ == '__main__':
    main()
