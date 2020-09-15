#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_qos_policy_group
short_description: NetApp ONTAP manage policy group in Quality of Service.
extends_documentation_fragment:
  - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
  - Create, destroy, modify, or rename QoS policy group on NetApp ONTAP.

options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified policy group should exist or not.
    default: 'present'

  name:
    description:
    - The name of the policy group to manage.

  vserver:
    description:
    - Name of the vserver to use.

  from_name:
    description:
    - Name of the existing policy group to be renamed to name.

  max_throughput:
    description:
    - Maximum throughput defined by this policy.

  min_throughput:
    description:
    - Minimum throughput defined by this policy.

  force:
    type: bool
    default: False
    description:
    - Setting to 'true' forces the deletion of the workloads associated with the policy group along with the policy group.
'''

EXAMPLES = """
    - name: create qos policy group
      na_ontap_qos_policy_group:
        state: present
        name: policy_1
        vserver: policy_vserver
        max_throughput: 800KB/s,800iops
        min_throughput: 100iops
        hostname: 10.193.78.30
        username: admin
        password: netapp1!

    - name: modify qos policy group max throughput
      na_ontap_qos_policy_group:
        state: present
        name: policy_1
        vserver: policy_vserver
        max_throughput: 900KB/s,800iops
        min_throughput: 100iops
        hostname: 10.193.78.30
        username: admin
        password: netapp1!

    - name: delete qos policy group
      na_ontap_qos_policy_group:
        state: absent
        name: policy_1
        vserver: policy_vserver
        hostname: 10.193.78.30
        username: admin
        password: netapp1!

"""

RETURN = """
"""

import traceback

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapQosPolicyGroup(object):
    """
    Create, delete, modify and rename a policy group.
    """
    def __init__(self):
        """
        Initialize the Ontap qos policy group class.
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            vserver=dict(required=True, type='str'),
            max_throughput=dict(required=False, type='str'),
            min_throughput=dict(required=False, type='str'),
            force=dict(required=False, type='bool', default=False)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module)

    def get_policy_group(self, policy_group_name=None):
        """
        Return details of a policy group.
        :param policy_group_name: policy group name
        :return: policy group details.
        :rtype: dict.
        """
        if policy_group_name is None:
            policy_group_name = self.parameters['name']
        policy_group_get_iter = netapp_utils.zapi.NaElement('qos-policy-group-get-iter')
        policy_group_info = netapp_utils.zapi.NaElement('qos-policy-group-info')
        policy_group_info.add_new_child('policy-group', policy_group_name)
        policy_group_info.add_new_child('vserver', self.parameters['vserver'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(policy_group_info)
        policy_group_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(policy_group_get_iter, True)
        policy_group_detail = None

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) == 1:
            policy_info = result.get_child_by_name('attributes-list').get_child_by_name('qos-policy-group-info')

            policy_group_detail = {
                'name': policy_info.get_child_content('policy-group'),
                'vserver': policy_info.get_child_content('vserver'),
                'max_throughput': policy_info.get_child_content('max-throughput'),
                'min_throughput': policy_info.get_child_content('min-throughput')
            }
        return policy_group_detail

    def create_policy_group(self):
        """
        create a policy group name.
        """
        policy_group = netapp_utils.zapi.NaElement('qos-policy-group-create')
        policy_group.add_new_child('policy-group', self.parameters['name'])
        policy_group.add_new_child('vserver', self.parameters['vserver'])
        if self.parameters.get('max_throughput'):
            policy_group.add_new_child('max-throughput', self.parameters['max_throughput'])
        if self.parameters.get('min_throughput'):
            policy_group.add_new_child('min-throughput', self.parameters['min_throughput'])
        try:
            self.server.invoke_successfully(policy_group, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating qos policy group %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_policy_group(self, policy_group=None):
        """
        delete an existing policy group.
        :param policy_group: policy group name.
        """
        if policy_group is None:
            policy_group = self.parameters['name']
        policy_group_obj = netapp_utils.zapi.NaElement('qos-policy-group-delete')
        policy_group_obj.add_new_child('policy-group', policy_group)
        if self.parameters.get('force'):
            policy_group_obj.add_new_child('force', str(self.parameters['force']))
        try:
            self.server.invoke_successfully(policy_group_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting qos policy group %s: %s' %
                                  (policy_group, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_policy_group(self):
        """
        Modify policy group.
        """
        policy_group_obj = netapp_utils.zapi.NaElement('qos-policy-group-modify')
        policy_group_obj.add_new_child('policy-group', self.parameters['name'])
        if self.parameters.get('max_throughput'):
            policy_group_obj.add_new_child('max-throughput', self.parameters['max_throughput'])
        if self.parameters.get('min_throughput'):
            policy_group_obj.add_new_child('min-throughput', self.parameters['min_throughput'])
        try:
            self.server.invoke_successfully(policy_group_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying qos policy group %s: %s' %
                                      (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def rename_policy_group(self):
        """
        Rename policy group name.
        """
        rename_obj = netapp_utils.zapi.NaElement('qos-policy-group-rename')
        rename_obj.add_new_child('new-name', self.parameters['name'])
        rename_obj.add_new_child('policy-group-name', self.parameters['from_name'])
        try:
            self.server.invoke_successfully(rename_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming qos policy group %s: %s' %
                                      (self.parameters['from_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_helper(self, modify):
        """
        helper method to modify policy group.
        :param modify: modified attributes.
        """
        for attribute in modify.keys():
            if attribute in ['max_throughput', 'min_throughput']:
                self.modify_policy_group()

    def apply(self):
        """
        Run module based on playbook
        """
        self.asup_log_for_cserver("na_ontap_qos_policy_group")
        current = self.get_policy_group()
        rename, cd_action = None, None
        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_policy_group(self.parameters['from_name']), current)
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_policy_group()
                if cd_action == 'create':
                    self.create_policy_group()
                elif cd_action == 'delete':
                    self.delete_policy_group()
                elif modify:
                    self.modify_helper(modify)
        self.module.exit_json(changed=self.na_helper.changed)

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


def main():
    '''Apply vserver operations from playbook'''
    qos_policy_group = NetAppOntapQosPolicyGroup()
    qos_policy_group.apply()


if __name__ == '__main__':
    main()
