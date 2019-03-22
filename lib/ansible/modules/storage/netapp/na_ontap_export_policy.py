#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
module: na_ontap_export_policy
short_description: NetApp ONTAP manage export-policy
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create or destroy or rename export-policies on ONTAP
options:
  state:
    description:
    - Whether the specified export policy should exist or not.
    choices: ['present', 'absent']
    default: present
  name:
    description:
    - The name of the export-policy to manage.
    required: true
  from_name:
    description:
    - The name of the export-policy to be renamed.
    version_added: '2.7'
  vserver:
    description:
    - Name of the vserver to use.
'''

EXAMPLES = """
    - name: Create Export Policy
      na_ontap_export_policy:
        state: present
        name: ansiblePolicyName
        vserver: vs_hack
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Rename Export Policy
      na_ontap_export_policy:
        action: present
        from_name: ansiblePolicyName
        vserver: vs_hack
        name: newPolicyName
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Delete Export Policy
      na_ontap_export_policy:
        state: absent
        name: ansiblePolicyName
        vserver: vs_hack
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPExportPolicy(object):
    """
    Class with export policy methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str', default=None),
            vserver=dict(required=False, type='str')
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['vserver'])
            ],
            supports_check_mode=True
        )
        parameters = self.module.params
        # set up state variables
        self.state = parameters['state']
        self.name = parameters['name']
        self.from_name = parameters['from_name']
        self.vserver = parameters['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_export_policy(self, name=None):
        """
        Return details about the export-policy
        :param:
            name : Name of the export-policy
        :return: Details about the export-policy. None if not found.
        :rtype: dict
        """
        if name is None:
            name = self.name
        export_policy_iter = netapp_utils.zapi.NaElement('export-policy-get-iter')
        export_policy_info = netapp_utils.zapi.NaElement('export-policy-info')
        export_policy_info.add_new_child('policy-name', name)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(export_policy_info)
        export_policy_iter.add_child_elem(query)
        result = self.server.invoke_successfully(export_policy_iter, True)
        return_value = None
        # check if query returns the expected export-policy
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            export_policy = result.get_child_by_name('attributes-list').get_child_by_name('export-policy-info').get_child_by_name('policy-name')
            return_value = {
                'policy-name': export_policy
            }
        return return_value

    def create_export_policy(self):
        """
        Creates an export policy
        """
        export_policy_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-policy-create', **{'policy-name': self.name})
        try:
            self.server.invoke_successfully(export_policy_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating export-policy %s: %s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_export_policy(self):
        """
        Delete export-policy
        """
        export_policy_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-policy-destroy', **{'policy-name': self.name, })
        try:
            self.server.invoke_successfully(export_policy_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting export-policy %s: %s'
                                  % (self.name,
                                     to_native(error)), exception=traceback.format_exc())

    def rename_export_policy(self):
        """
        Rename the export-policy.
        """
        export_policy_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'export-policy-rename', **{'policy-name': self.from_name,
                                       'new-policy-name': self.name})
        try:
            self.server.invoke_successfully(export_policy_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming export-policy %s:%s'
                                  % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to export-policy
        """
        changed = False
        export_policy_exists = False
        netapp_utils.ems_log_event("na_ontap_export_policy", self.server)
        rename_flag = False
        export_policy_details = self.get_export_policy()
        if export_policy_details:
            export_policy_exists = True
            if self.state == 'absent':  # delete
                changed = True
        else:
            if self.state == 'present':  # create or rename
                if self.from_name is not None:
                    if self.get_export_policy(self.from_name):
                        changed = True
                        rename_flag = True
                    else:
                        self.module.fail_json(msg='Error renaming export-policy %s: does not exists' % self.from_name)
                else:  # create
                    changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute create or rename_export_policy
                    if rename_flag:
                        self.rename_export_policy()
                    else:
                        self.create_export_policy()
                elif self.state == 'absent':  # execute delete
                    self.delete_export_policy()
        self.module.exit_json(changed=changed)


def main():
    """
    Execute action
    """
    export_policy = NetAppONTAPExportPolicy()
    export_policy.apply()


if __name__ == '__main__':
    main()
