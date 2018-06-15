#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: na_ontap_net_ifgrp
short_description: Create, modify, destroy the network interface group
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)
description:
- Create, modify, destroy the network interface group
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

  port:
    description:
    - Adds the specified port.

"""

EXAMPLES = """
    - name: create ifgrp
      na_ontap_net_ifgrp:
        state=present
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        distribution_function=ip
        name=a0c
        port=e0d
        mode=multimode
        node={{ Vsim node name }}
    - name: delete ifgrp
      na_ontap_net_ifgrp:
        state=absent
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
        name=a0c
        node={{ Vsim node name }}
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
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
            port=dict(required=False, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['distribution_function', 'mode'])
            ],
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.distribution_function = parameters['distribution_function']
        self.name = parameters['name']
        self.mode = parameters['mode']
        self.node = parameters['node']
        self.port = parameters['port']

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
        if_group_info.add_new_child('port', self.name)
        if_group_info.add_new_child('port-type', 'if_group')
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(if_group_info)
        if_group_iter.add_child_elem(query)
        result = self.server.invoke_successfully(if_group_iter, True)

        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            if_group_attributes = result.get_child_by_name('attributes-list').get_child_by_name('net-port-info')
            distribution_function = if_group_attributes.get_child_content('ifgrp-distribution-function')
            name = if_group_attributes.get_child_content('port')
            mode = if_group_attributes.get_child_content('ifgrp-mode')
            ports = if_group_attributes.get_child_content('ifgrp-port')
            node = if_group_attributes.get_child_content('node')

            return_value = {
                'name': name,
                'distribution_function': distribution_function,
                'mode': mode,
                'node': node,
                'ports': ports
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
        if_group_iter.add_new_child('ifgrp-name', self.name)
        if_group_iter.add_new_child('node', self.node)
        result = self.server.invoke_successfully(if_group_iter, True)

        return_value = None

        if result.get_child_by_name('attributes'):
            if_group_attributes = result.get_child_by_name('attributes').get_child_by_name('net-ifgrp-info')
            name = if_group_attributes.get_child_content('ifgrp-name')
            mode = if_group_attributes.get_child_content('mode')
            port_list = []
            if if_group_attributes.get_child_by_name('ports'):
                ports = if_group_attributes.get_child_by_name('ports').get_children()
                for each in ports:
                    port_list.append(each.get_content())
            node = if_group_attributes.get_child_content('node')
            return_value = {
                'name': name,
                'mode': mode,
                'node': node,
                'ports': port_list
            }
        return return_value

    def create_if_grp(self):
        """
        Creates a new ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-create")
        route_obj.add_new_child("distribution-function", self.distribution_function)
        route_obj.add_new_child("ifgrp-name", self.name)
        route_obj.add_new_child("mode", self.mode)
        route_obj.add_new_child("node", self.node)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating if_group %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_if_grp(self):
        """
        Deletes a ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-destroy")
        route_obj.add_new_child("ifgrp-name", self.name)
        route_obj.add_new_child("node", self.node)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting if_group %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def add_port_to_if_grp(self):
        """
        adds port to a ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-add-port")
        route_obj.add_new_child("ifgrp-name", self.name)
        route_obj.add_new_child("port", self.port)
        route_obj.add_new_child("node", self.node)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding port %s to if_group %s: %s' %
                                      (self.port, self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def remove_port_to_if_grp(self):
        """
        removes port from a ifgrp
        """
        route_obj = netapp_utils.zapi.NaElement("net-port-ifgrp-remove-port")
        route_obj.add_new_child("ifgrp-name", self.name)
        route_obj.add_new_child("port", self.port)
        route_obj.add_new_child("node", self.node)
        try:
            self.server.invoke_successfully(route_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing port %s to if_group %s: %s' %
                                      (self.port, self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        ifgroup_exists = False
        add_ports_exists = True
        remove_ports_exists = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_net_ifgrp", cserver)
        if_group_detail = self.get_if_grp()
        if if_group_detail:
            ifgroup_exists = True
            ifgrp_ports_detail = self.get_if_grp_ports()
            if self.state == 'absent':
                changed = True
                if self.port:
                    if self.port in ifgrp_ports_detail['ports']:
                        remove_ports_exists = True
            elif self.state == 'present':
                if self.port:
                    if not ifgrp_ports_detail['ports']:
                        add_ports_exists = False
                        changed = True
                    else:
                        if self.port not in ifgrp_ports_detail['ports']:
                            add_ports_exists = False
                            changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not ifgroup_exists:
                        self.create_if_grp()
                        if self.port:
                            self.add_port_to_if_grp()
                    else:
                        if not add_ports_exists:
                            self.add_port_to_if_grp()
                elif self.state == 'absent':
                    if remove_ports_exists:
                        self.remove_port_to_if_grp()
                    self.delete_if_grp()

        self.module.exit_json(changed=changed)


def main():
    """
    Creates the NetApp Ontap Net Route object and runs the correct play task
    """
    obj = NetAppOntapIfGrp()
    obj.apply()


if __name__ == '__main__':
    main()
