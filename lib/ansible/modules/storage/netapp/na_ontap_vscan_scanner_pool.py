#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_vscan_scanner_pool
short_description: NetApp ONTAP Vscan Scanner Pools Configuration.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Configure a Vscan Scanner Pool
options:
  state:
    description:
    - Whether a Vscan Scanner pool is present or not
    choices: ['present', 'absent']
    default: present

  vserver:
    description:
    - the name of the data vserver to use.
    required: true

  hostnames:
    description:
    - List of hostnames of Vscan servers which are allowed to connect to Data ONTAP

  privileged_users:
    description:
    - List of privileged usernames. Username must be in the form "domain-name\\user-name"

  scanner_pool:
    description:
    - the name of the virus scanner pool
    required: true

  scanner_policy:
    description:
    - The name of the Virus scanner Policy
    choices: ['primary', 'secondary', 'idle']
'''

EXAMPLES = """
- name: Create and enable Scanner pool
  na_ontap_vscan_scanner_pool:
    state: present
    username: '{{ netapp_username }}'
    password: '{{ netapp_password }}'
    hostname: '{{ netapp_hostname }}'
    vserver: carchi-vsim2
    hostnames: ['name', 'name2']
    privileged_users: ['sim.rtp.openeng.netapp.com\\admin', 'sim.rtp.openeng.netapp.com\\carchi']
    scanner_pool: Scanner1
    scanner_policy: primary

- name: Delete a scanner pool
  na_ontap_vscan_scanner_pool:
    state: absent
    username: '{{ netapp_username }}'
    password: '{{ netapp_password }}'
    hostname: '{{ netapp_hostname }}'
    vserver: carchi-vsim2
    scanner_pool: Scanner1
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVscanScannerPool(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            hostnames=dict(required=False, type='list'),
            privileged_users=dict(required=False, type='list'),
            scanner_pool=dict(required=True, type='str'),
            scanner_policy=dict(required=False, choices=['primary', 'secondary', 'idle'])
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        parameters = self.module.params
        self.hostnames = parameters['hostnames']
        self.vserver = parameters['vserver']
        self.privileged_users = parameters['privileged_users']
        self.scanner_pool = parameters['scanner_pool']
        self.state = parameters['state']
        self.scanner_policy = parameters['scanner_policy']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def create_scanner_pool(self):
        """
        Create a Vscan Scanner Pool
        :return: nothing
        """
        scanner_pool_obj = netapp_utils.zapi.NaElement('vscan-scanner-pool-create')
        if self.hostnames:
            string_obj = netapp_utils.zapi.NaElement('hostnames')
            scanner_pool_obj.add_child_elem(string_obj)
            for hostname in self.hostnames:
                string_obj.add_new_child('string', hostname)
        if self.privileged_users:
            users_obj = netapp_utils.zapi.NaElement('privileged-users')
            scanner_pool_obj.add_child_elem(users_obj)
            for user in self.privileged_users:
                users_obj.add_new_child('privileged-user', user)
        scanner_pool_obj.add_new_child('scanner-pool', self.scanner_pool)
        try:
            self.server.invoke_successfully(scanner_pool_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating Vscan Scanner Pool %s: %s' %
                                      (self.scanner_pool, to_native(error)),
                                  exception=traceback.format_exc())

    def apply_policy(self):
        """
        Apply a Scanner policy to a Scanner pool
        :return: nothing
        """
        apply_policy_obj = netapp_utils.zapi.NaElement('vscan-scanner-pool-apply-policy')
        apply_policy_obj.add_new_child('scanner-policy', self.scanner_policy)
        apply_policy_obj.add_new_child('scanner-pool', self.scanner_pool)
        try:
            self.server.invoke_successfully(apply_policy_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error applying policy %s to pool %s: %s' %
                                      (self.scanner_policy, self.scanner_pool, to_native(error)),
                                  exception=traceback.format_exc())

    def get_scanner_pool(self):
        """
        Check to see if a scanner pool exist or not
        :return: True if it exist, False if it does not
        """
        scanner_pool_obj = netapp_utils.zapi.NaElement('vscan-scanner-pool-get-iter')
        scanner_pool_info = netapp_utils.zapi.NaElement('scan-scanner-pool-info')
        scanner_pool_info.add_new_child('scanner-pool', self.scanner_pool)
        scanner_pool_info.add_new_child('vserver', self.vserver)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(scanner_pool_info)
        scanner_pool_obj.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(scanner_pool_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error searching for Vscan Scanner Pool %s: %s' %
                                      (self.scanner_pool, to_native(error)),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            if result.get_child_by_name('attributes-list').get_child_by_name('vscan-scanner-pool-info').get_child_content(
                    'scanner-pool') == self.scanner_pool:
                return result.get_child_by_name('attributes-list').get_child_by_name('vscan-scanner-pool-info')
            return False
        return False

    def delete_scanner_pool(self):
        """
        Delete a Scanner pool
        :return: nothing
        """
        scanner_pool_obj = netapp_utils.zapi.NaElement('vscan-scanner-pool-delete')
        scanner_pool_obj.add_new_child('scanner-pool', self.scanner_pool)
        try:
            self.server.invoke_successfully(scanner_pool_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting Vscan Scanner Pool %s: %s' %
                                      (self.scanner_pool, to_native(error)),
                                  exception=traceback.format_exc())

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)

    def apply(self):
        self.asup_log_for_cserver("na_ontap_vscan_scanner_pool")
        changed = False
        scanner_pool_obj = self.get_scanner_pool()
        if self.state == 'present':
            if not scanner_pool_obj:
                self.create_scanner_pool()
                if self.scanner_policy:
                    self.apply_policy()
                changed = True
            # apply Scanner policy
            if scanner_pool_obj:
                if self.scanner_policy:
                    if scanner_pool_obj.get_child_content('scanner-policy') != self.scanner_policy:
                        self.apply_policy()
                        changed = True
        if self.state == 'absent':
            if scanner_pool_obj:
                self.delete_scanner_pool()
                changed = True
        self.module.exit_json(changed=changed)


def main():
    """
    Execute action from playbook
    """
    command = NetAppOntapVscanScannerPool()
    command.apply()


if __name__ == '__main__':
    main()
