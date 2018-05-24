#!/usr/bin/python
""" this is interface module

 (c) 2018, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---

module: na_ontap_interface
short_description: ONTAP LIF configuration

extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: chhaya gunawat (chhayag@netapp.com)

description:
    - Creating / deleting and modifying the LIF.

options:
  state:
    description:
    - Whether the specified interface should exist or not.
    choices: ['present', 'absent']
    default: present

  interface_name:
    description:
    - Specifies the logical interface (LIF) name.
    required: true

  home_node:
    description:
    - Specifies the LIF's home node.
    - Required when C(state=present).

  home_port:
    description:
    - Specifies the LIF's home port.
    - Required when C(state=present)

  role:
    description:
    - Specifies the role of the LIF.
    - Required when C(state=present).

  address:
    description:
    - Specifies the LIF's IP address.
    - Required when C(state=present)

  netmask:
    description:
    - Specifies the LIF's netmask.
    - Required when C(state=present).

  vserver:
    description:
    - The name of the vserver to use.
    required: true

  firewall_policy:
    description:
    - Specifies the firewall policy for the LIF.

  failover_policy:
    description:
    - Specifies the failover policy for the LIF.

  admin_status:
    choices: ['up', 'down']
    description:
    - Specifies the administrative status of the LIF.

  is_auto_revert:
    description:
       If true, data LIF will revert to its home node under certain circumstances such as startup, and load balancing
       migration capability is disabled automatically

  protocols:
    description:
       Specifies the list of data protocols configured on the LIF. By default, the values in this element are nfs, cifs and fcache.
       Other supported protocols are iscsi and fcp. A LIF can be configured to not support any data protocols by specifying 'none'.
       Protocol values of none, iscsi or fcp can't be combined with any other data protocol(s).

'''

EXAMPLES = '''
    - name: Create interface
      na_ontap_interface:
        state: present
        interface_name: data2
        home_port: e0d
        home_node: laurentn-vsim1
        role: data
        protocols: nfs
        admin_status: up
        failover_policy: local-only
        firewall_policy: mgmt
        is_auto_revert: true
        address: 10.10.10.10
        netmask: 255.255.255.0
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete interface
      na_ontap_interface:
        state: absent
        interface_name: data2
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

'''

RETURN = """

"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapInterface(object):
    ''' object to describe  interface info '''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            interface_name=dict(required=True, type='str'),
            home_node=dict(required=False, type='str', default=None),
            home_port=dict(required=False, type='str'),
            role=dict(required=False, type='str'),
            address=dict(required=False, type='str'),
            netmask=dict(required=False, type='str'),
            vserver=dict(required=True, type='str'),
            firewall_policy=dict(required=False, type='str', default=None),
            failover_policy=dict(required=False, type='str', default=None),
            admin_status=dict(required=False, choices=['up', 'down']),
            is_auto_revert=dict(required=False, type='str', default=None),
            protocols=dict(required=False, type='list')

        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        params = self.module.params

        # set up state variables
        self.state = params['state']
        self.interface_name = params['interface_name']
        self.home_node = params['home_node']
        self.home_port = params['home_port']
        self.role = params['role']
        self.vserver = params['vserver']
        self.address = params['address']
        self.netmask = params['netmask']
        self.admin_status = params['admin_status']
        self.failover_policy = params['failover_policy']
        self.firewall_policy = params['firewall_policy']
        self.is_auto_revert = params['is_auto_revert']
        self.protocols = params['protocols']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_interface(self):
        """
        Return details about the interface
        :param:
            name : Name of the name of the interface

        :return: Details about the interface. None if not found.
        :rtype: dict
        """
        interface_info = netapp_utils.zapi.NaElement('net-interface-get-iter')
        interface_attributes = netapp_utils.zapi.NaElement(
            'net-interface-info')
        interface_attributes.add_new_child(
            'interface-name', self.interface_name)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(interface_attributes)
        interface_info.add_child_elem(query)
        result = self.server.invoke_successfully(interface_info, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            interface_attributes = result.get_child_by_name('attributes-list').\
                get_child_by_name('net-interface-info')
            return_value = {
                'interface_name': self.interface_name,
                'admin_status': interface_attributes.get_child_content('administrative-status'),
                'home_port': interface_attributes.get_child_content('home-port'),
                'home_node': interface_attributes.get_child_content('home-node'),
                'address': interface_attributes.get_child_content('address'),
                'netmask': interface_attributes.get_child_content('netmask'),
                'failover_policy': interface_attributes.get_child_content('failover-policy'),
                'firewall_policy': interface_attributes.get_child_content('firewall-policy'),
                'is_auto_revert': interface_attributes.get_child_content('is-auto-revert'),
            }
        return return_value

    def create_interface(self):
        ''' calling zapi to create interface '''

        options = {'interface-name': self.interface_name,
                   'vserver': self.vserver}
        if self.home_port is not None:
            options['home-port'] = self.home_port
        if self.home_node is not None:
            options['home-node'] = self.home_node
        if self.address is not None:
            options['address'] = self.address
        if self.netmask is not None:
            options['netmask'] = self.netmask
        if self.role is not None:
            options['role'] = self.role
        if self.failover_policy is not None:
            options['failover-policy'] = self.failover_policy
        if self.firewall_policy is not None:
            options['firewall-policy'] = self.firewall_policy
        if self.is_auto_revert is not None:
            options['is-auto-revert'] = self.is_auto_revert
        if self.admin_status is not None:
            options['administrative-status'] = self.admin_status

        interface_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-interface-create', **options)
        if self.protocols is not None:
            data_protocols_obj = netapp_utils.zapi.NaElement('data-protocols')
            interface_create.add_child_elem(data_protocols_obj)
            for protocol in self.protocols:
                data_protocols_obj.add_new_child('data-protocol', protocol)

        try:
            self.server.invoke_successfully(interface_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error Creating interface %s: %s' %
                                  (self.interface_name, to_native(exc)), exception=traceback.format_exc())

    def delete_interface(self, current_status):
        ''' calling zapi to delete interface '''
        if current_status == 'up':
            self.admin_status = 'down'
            self.modify_interface()

        interface_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-interface-delete', **{'interface-name': self.interface_name,
                                       'vserver': self.vserver})
        try:
            self.server.invoke_successfully(interface_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error deleting interface %s: %s' % (self.interface_name, to_native(exc)),
                                  exception=traceback.format_exc())

    def modify_interface(self):
        """
        Modify the interface.
        """
        options = {'interface-name': self.interface_name,
                   'vserver': self.vserver
                   }
        if self.admin_status is not None:
            options['administrative-status'] = self.admin_status
        if self.failover_policy is not None:
            options['failover-policy'] = self.failover_policy
        if self.firewall_policy is not None:
            options['firewall-policy'] = self.firewall_policy
        if self.is_auto_revert is not None:
            options['is-auto-revert'] = self.is_auto_revert
        if self.netmask is not None:
            options['netmask'] = self.netmask
        if self.address is not None:
            options['address'] = self.address

        interface_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'net-interface-modify', **options)
        try:
            self.server.invoke_successfully(interface_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying interface %s: %s' % (self.interface_name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        ''' calling all interface features '''
        changed = False
        interface_exists = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(
            module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_interface", cserver)
        interface_detail = self.get_interface()
        if interface_detail:
            interface_exists = True
            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                if (self.admin_status is not None and self.admin_status != interface_detail['admin_status']) or \
                   (self.address is not None and self.address != interface_detail['address']) or \
                   (self.netmask is not None and self.netmask != interface_detail['netmask']) or \
                   (self.failover_policy is not None and self.failover_policy != interface_detail['failover_policy']) or \
                   (self.firewall_policy is not None and self.firewall_policy != interface_detail['firewall_policy']) or \
                   (self.is_auto_revert is not None and self.is_auto_revert != interface_detail['is_auto_revert']):
                    changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if interface_exists is False:
                        self.create_interface()
                    else:
                        self.modify_interface()

                elif self.state == 'absent':
                    self.delete_interface(interface_detail['admin_status'])

        self.module.exit_json(changed=changed)


def main():
    interface = NetAppOntapInterface()
    interface.apply()


if __name__ == '__main__':
    main()
