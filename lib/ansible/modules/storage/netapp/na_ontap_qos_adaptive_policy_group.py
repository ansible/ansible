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
module: na_ontap_qos_adaptive_policy_group
short_description: NetApp ONTAP Adaptive Quality of Service policy group.
extends_documentation_fragment:
  - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@joshedmonds) <ng-ansibleteam@netapp.com>

description:
  - Create, destroy, modify, or rename an Adaptive QoS policy group on NetApp ONTAP. Module is based on the standard QoS policy group module.

options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified policy group should exist or not.
    default: 'present'
    type: str

  name:
    description:
    - The name of the policy group to manage.
    type: str
    required: true

  vserver:
    description:
    - Name of the vserver to use.
    type: str
    required: true

  from_name:
    description:
    - Name of the existing policy group to be renamed to name.
    type: str

  absolute_min_iops:
    description:
    - Absolute minimum IOPS defined by this policy.
    type: str

  expected_iops:
    description:
    - Minimum expected IOPS defined by this policy.
    type: str

  peak_iops:
    description:
    - Maximum possible IOPS per allocated or used TB|GB.
    type: str

  peak_iops_allocation:
    choices: ['allocated_space', 'used_space']
    description:
      - Whether peak_iops is specified by allocated or used space.
    default: 'used_space'
    type: str

  force:
    type: bool
    default: False
    description:
    - Setting to 'true' forces the deletion of the workloads associated with the policy group along with the policy group.
'''

EXAMPLES = """
    - name: create adaptive qos policy group
      na_ontap_qos_adaptive_policy_group:
        state: present
        name: aq_policy_1
        vserver: policy_vserver
        absolute_min_iops: 70IOPS
        expected_iops: 100IOPS/TB
        peak_iops: 250IOPS/TB
        peak_iops_allocation: allocated_space
        hostname: 10.193.78.30
        username: admin
        password: netapp1!

    - name: modify adaptive qos policy group expected iops
      na_ontap_qos_adaptive_policy_group:
        state: present
        name: aq_policy_1
        vserver: policy_vserver
        absolute_min_iops: 70IOPS
        expected_iops: 125IOPS/TB
        peak_iops: 250IOPS/TB
        peak_iops_allocation: allocated_space
        hostname: 10.193.78.30
        username: admin
        password: netapp1!

    - name: modify adaptive qos policy group peak iops allocation
      na_ontap_qos_adaptive_policy_group:
        state: present
        name: aq_policy_1
        vserver: policy_vserver
        absolute_min_iops: 70IOPS
        expected_iops: 125IOPS/TB
        peak_iops: 250IOPS/TB
        peak_iops_allocation: used_space
        hostname: 10.193.78.30
        username: admin
        password: netapp1!

    - name: delete qos policy group
      na_ontap_qos_adaptive_policy_group:
        state: absent
        name: aq_policy_1
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


class NetAppOntapAdaptiveQosPolicyGroup(object):
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
            absolute_min_iops=dict(required=False, type='str'),
            expected_iops=dict(required=False, type='str'),
            peak_iops=dict(required=False, type='str'),
            peak_iops_allocation=dict(choices=['allocated_space', 'used_space'], default='used_space'),
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
        policy_group_get_iter = netapp_utils.zapi.NaElement('qos-adaptive-policy-group-get-iter')
        policy_group_info = netapp_utils.zapi.NaElement('qos-adaptive-policy-group-info')
        policy_group_info.add_new_child('policy-group', policy_group_name)
        policy_group_info.add_new_child('vserver', self.parameters['vserver'])
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(policy_group_info)
        policy_group_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(policy_group_get_iter, True)
        policy_group_detail = None

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) == 1:
            policy_info = result.get_child_by_name('attributes-list').get_child_by_name('qos-adaptive-policy-group-info')

            policy_group_detail = {
                'name': policy_info.get_child_content('policy-group'),
                'vserver': policy_info.get_child_content('vserver'),
                'absolute_min_iops': policy_info.get_child_content('absolute-min-iops'),
                'expected_iops': policy_info.get_child_content('expected-iops'),
                'peak_iops': policy_info.get_child_content('peak-iops'),
                'peak_iops_allocation': policy_info.get_child_content('peak-iops-allocation')
            }
        return policy_group_detail

    def create_policy_group(self):
        """
        create a policy group name.
        """
        policy_group = netapp_utils.zapi.NaElement('qos-adaptive-policy-group-create')
        policy_group.add_new_child('policy-group', self.parameters['name'])
        policy_group.add_new_child('vserver', self.parameters['vserver'])
        if self.parameters.get('absolute_min_iops'):
            policy_group.add_new_child('absolute-min-iops', self.parameters['absolute_min_iops'])
        if self.parameters.get('expected_iops'):
            policy_group.add_new_child('expected-iops', self.parameters['expected_iops'])
        if self.parameters.get('peak_iops'):
            policy_group.add_new_child('peak-iops', self.parameters['peak_iops'])
        if self.parameters.get('peak_iops_allocation'):
            policy_group.add_new_child('peak-iops-allocation', self.parameters['peak_iops_allocation'])
        try:
            self.server.invoke_successfully(policy_group, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating adaptive qos policy group %s: %s' %
                                  (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_policy_group(self, policy_group=None):
        """
        delete an existing policy group.
        :param policy_group: policy group name.
        """
        if policy_group is None:
            policy_group = self.parameters['name']
        policy_group_obj = netapp_utils.zapi.NaElement('qos-adaptive-policy-group-delete')
        policy_group_obj.add_new_child('policy-group', policy_group)
        if self.parameters.get('force'):
            policy_group_obj.add_new_child('force', str(self.parameters['force']))
        try:
            self.server.invoke_successfully(policy_group_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting adaptive qos policy group %s: %s' %
                                  (policy_group, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_policy_group(self):
        """
        Modify policy group.
        """
        policy_group_obj = netapp_utils.zapi.NaElement('qos-adaptive-policy-group-modify')
        policy_group_obj.add_new_child('policy-group', self.parameters['name'])
        if self.parameters.get('absolute_min_iops'):
            policy_group_obj.add_new_child('absolute-min-iops', self.parameters['absolute_min_iops'])
        if self.parameters.get('expected_iops'):
            policy_group_obj.add_new_child('expected-iops', self.parameters['expected_iops'])
        if self.parameters.get('peak_iops'):
            policy_group_obj.add_new_child('peak-iops', self.parameters['peak_iops'])
        if self.parameters.get('peak_iops_allocation'):
            policy_group_obj.add_new_child('peak-iops-allocation', self.parameters['peak_iops_allocation'])
        try:
            self.server.invoke_successfully(policy_group_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying adaptive qos policy group %s: %s' %
                                      (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def rename_policy_group(self):
        """
        Rename policy group name.
        """
        rename_obj = netapp_utils.zapi.NaElement('qos-adaptive-policy-group-rename')
        rename_obj.add_new_child('new-name', self.parameters['name'])
        rename_obj.add_new_child('policy-group-name', self.parameters['from_name'])
        try:
            self.server.invoke_successfully(rename_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming adaptive qos policy group %s: %s' %
                                      (self.parameters['from_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_helper(self, modify):
        """
        helper method to modify policy group.
        :param modify: modified attributes.
        """
        for attribute in modify.keys():
            if attribute in ['absolute_min_iops', 'expected_iops', 'peak_iops', 'peak_iops_allocation']:
                self.modify_policy_group()

    def apply(self):
        """
        Run module based on playbook
        """
        self.autosupport_log("na_ontap_qos_policy_group")
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

    def autosupport_log(self, event_name):
        """
        Create a log event against the provided vserver
        """
        server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])
        netapp_utils.ems_log_event(event_name, server)


def main():
    '''Apply vserver operations from playbook'''
    qos_policy_group = NetAppOntapAdaptiveQosPolicyGroup()
    qos_policy_group.apply()


if __name__ == '__main__':
    main()
