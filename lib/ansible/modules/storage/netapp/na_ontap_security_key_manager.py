#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_security_key_manager

short_description: NetApp ONTAP security key manager.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Add or delete or setup key management on NetApp ONTAP.

options:

  state:
    description:
    - Whether the specified key manager should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  ip_address:
    description:
    - The IP address of the key management server.
    required: true

  tcp_port:
    description:
    - The TCP port on which the key management server listens for incoming connections.
    default: 5696

  node:
    description:
    - The node which key management server runs on.

'''

EXAMPLES = """

    - name: Delete Key Manager
      tags:
      - delete
      na_ontap_security_key_manager:
        state: absent
        node: swenjun-vsim1
        hostname: "{{ hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        https: False
        ip_address: 0.0.0.0

    - name: Add Key Manager
      tags:
      - add
      na_ontap_security_key_manager:
        state: present
        node: swenjun-vsim1
        hostname: "{{ hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        https: False
        ip_address: 0.0.0.0

"""

RETURN = """
"""

import traceback
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapSecurityKeyManager(object):
    '''class with key manager operations'''

    def __init__(self):
        '''Initialize module parameters'''
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            ip_address=dict(required=True, type='str'),
            node=dict(required=False, type='str'),
            tcp_port=dict(required=False, type='int', default=5696)
        )
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required"
            )
        else:
            self.cluster = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_key_manager(self):
        """
        get key manager by ip address.
        :return: a dict of key manager
        """
        key_manager_info = netapp_utils.zapi.NaElement('security-key-manager-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'key-manager-info', **{'key-manager-ip-address': self.parameters['ip_address']})
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        key_manager_info.add_child_elem(query)

        try:
            result = self.cluster.invoke_successfully(key_manager_info, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching key manager %s : %s'
                                  % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())

        return_value = None
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            key_manager = result.get_child_by_name('attributes-list').get_child_by_name('key-manager-info')
            return_value = {}
            if key_manager.get_child_by_name('key-manager-ip-address'):
                return_value['ip_address'] = key_manager.get_child_content('key-manager-ip-address')
            if key_manager.get_child_by_name('key-manager-server-status'):
                return_value['server_status'] = key_manager.get_child_content('key-manager-server-status')
            if key_manager.get_child_by_name('key-manager-tcp-port'):
                return_value['tcp_port'] = key_manager.get_child_content('key-manager-tcp-port')
            if key_manager.get_child_by_name('node-name'):
                return_value['node'] = key_manager.get_child_content('node-name')

        return return_value

    def key_manager_setup(self):
        """
        set up external key manager.
        """
        key_manager_setup = netapp_utils.zapi.NaElement('security-key-manager-setup')
        # if specify on-boarding passphrase, it is on-boarding key management.
        # it not, then it's external key management.
        try:
            self.cluster.invoke_successfully(key_manager_setup, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error setting up key manager %s : %s'
                                  % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())

    def create_key_manager(self):
        """
        add key manager.
        """
        key_manager_create = netapp_utils.zapi.NaElement('security-key-manager-add')
        key_manager_create.add_new_child('key-manager-ip-address', self.parameters['ip_address'])
        if self.parameters.get('tcp_port'):
            key_manager_create.add_new_child('key-manager-tcp-port', str(self.parameters['tcp_port']))
        try:
            self.cluster.invoke_successfully(key_manager_create, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating key manager %s : %s'
                                  % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_key_manager(self):
        """
        delete key manager.
        """
        key_manager_delete = netapp_utils.zapi.NaElement('security-key-manager-delete')
        key_manager_delete.add_new_child('key-manager-ip-address', self.parameters['ip_address'])
        try:
            self.cluster.invoke_successfully(key_manager_delete, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting key manager %s : %s'
                                  % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        self.asup_log_for_cserver("na_ontap_security_key_manager")
        self.key_manager_setup()
        current = self.get_key_manager()
        cd_action = None
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_key_manager()
                elif cd_action == 'delete':
                    self.delete_key_manager()
        self.module.exit_json(changed=self.na_helper.changed)

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.cluster)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)


def main():
    '''Apply volume operations from playbook'''
    obj = NetAppOntapSecurityKeyManager()
    obj.apply()


if __name__ == '__main__':
    main()
