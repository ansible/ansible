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
module: na_ontap_quotas
short_description: NetApp ONTAP Quotas
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Set/Modify/Delete quota on ONTAP
options:
  state:
    description:
    - Whether the specified quota should exist or not.
    choices: ['present', 'absent']
    default: present
    type: str
  vserver:
    required: true
    description:
      - Name of the vserver to use.
    type: str
  volume:
    description:
    - The name of the volume that the quota resides on.
    required: true
    type: str
  quota_target:
    description:
    - The quota target of the type specified.
    required: true
    type: str
  qtree:
    description:
    - Name of the qtree for the quota.
    - For user or group rules, it can be the qtree name or "" if no qtree.
    - For tree type rules, this field must be "".
    default: ""
    type: str
  type:
    description:
    - The type of quota rule
    choices: ['user', 'group', 'tree']
    required: true
    type: str
  policy:
    description:
    - Name of the quota policy from which the quota rule should be obtained.
    type: str
  set_quota_status:
    description:
    - Whether the specified volume should have quota status on or off.
    type: bool
  file_limit:
    description:
    - The number of files that the target can have.
    default: '-'
    type: str
  disk_limit:
    description:
    - The amount of disk space that is reserved for the target.
    default: '-'
    type: str
  threshold:
    description:
    - The amount of disk space the target would have to exceed before a message is logged.
    default: '-'
    type: str
'''

EXAMPLES = """
    - name: Add/Set quota
      na_ontap_quotas:
        state: present
        vserver: ansible
        volume: ansible
        quota_target: /vol/ansible
        type: user
        policy: ansible
        file_limit: 2
        disk_limit: 3
        set_quota_status: True
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: modify quota
      na_ontap_quotas:
        state: present
        vserver: ansible
        volume: ansible
        quota_target: /vol/ansible
        type: user
        policy: ansible
        file_limit: 2
        disk_limit: 3
        threshold: 3
        set_quota_status: False
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Delete quota
      na_ontap_quotas:
        state: absent
        vserver: ansible
        volume: ansible
        quota_target: /vol/ansible
        type: user
        policy: ansible
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
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPQuotas(object):
    '''Class with quotas methods'''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            volume=dict(required=True, type='str'),
            quota_target=dict(required=True, type='str'),
            qtree=dict(required=False, type='str', default=""),
            type=dict(required=True, type='str', choices=['user', 'group', 'tree']),
            policy=dict(required=False, type='str'),
            set_quota_status=dict(required=False, type='bool'),
            file_limit=dict(required=False, type='str', default='-'),
            disk_limit=dict(required=False, type='str', default='-'),
            threshold=dict(required=False, type='str', default='-')
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
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_quota_status(self):
        """
        Return details about the quota status
        :param:
            name : volume name
        :return: status of the quota. None if not found.
        :rtype: dict
        """
        quota_status_get = netapp_utils.zapi.NaElement('quota-status')
        quota_status_get.translate_struct({
            'volume': self.parameters['volume']
        })
        try:
            result = self.server.invoke_successfully(quota_status_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching quotas status info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result:
            return result['status']
        return None

    def get_quotas(self):
        """
        Get quota details
        :return: name of volume if quota exists, None otherwise
        """
        quota_get = netapp_utils.zapi.NaElement('quota-list-entries-iter')
        query = {
            'query': {
                'quota-entry': {
                    'volume': self.parameters['volume'],
                    'quota-target': self.parameters['quota_target'],
                    'quota-type': self.parameters['type']
                }
            }
        }
        quota_get.translate_struct(query)
        if self.parameters.get('policy'):
            quota_get['query']['quota-entry'].add_new_child('policy', self.parameters['policy'])
        try:
            result = self.server.invoke_successfully(quota_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching quotas info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            return_values = {'volume': result['attributes-list']['quota-entry']['volume'],
                             'file_limit': result['attributes-list']['quota-entry']['file-limit'],
                             'disk_limit': result['attributes-list']['quota-entry']['disk-limit'],
                             'threshold': result['attributes-list']['quota-entry']['threshold']}
            return return_values
        return None

    def quota_entry_set(self):
        """
        Adds a quota entry
        """
        options = {'volume': self.parameters['volume'],
                   'quota-target': self.parameters['quota_target'],
                   'quota-type': self.parameters['type'],
                   'qtree': self.parameters['qtree'],
                   'file-limit': self.parameters['file_limit'],
                   'disk-limit': self.parameters['disk_limit'],
                   'threshold': self.parameters['threshold']}
        if self.parameters.get('policy'):
            options['policy'] = self.parameters['policy']
        set_entry = netapp_utils.zapi.NaElement.create_node_with_children(
            'quota-set-entry', **options)
        try:
            self.server.invoke_successfully(set_entry, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error adding/modifying quota entry %s: %s'
                                  % (self.parameters['volume'], to_native(error)),
                                  exception=traceback.format_exc())

    def quota_entry_delete(self):
        """
        Deletes a quota entry
        """
        options = {'volume': self.parameters['volume'],
                   'quota-target': self.parameters['quota_target'],
                   'quota-type': self.parameters['type'],
                   'qtree': self.parameters['qtree']}
        set_entry = netapp_utils.zapi.NaElement.create_node_with_children(
            'quota-delete-entry', **options)
        if self.parameters.get('policy'):
            set_entry.add_new_child('policy', self.parameters['policy'])
        try:
            self.server.invoke_successfully(set_entry, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting quota entry %s: %s'
                                  % (self.parameters['volume'], to_native(error)),
                                  exception=traceback.format_exc())

    def quota_entry_modify(self, modify_attrs):
        """
        Modifies a quota entry
        """
        options = {'volume': self.parameters['volume'],
                   'quota-target': self.parameters['quota_target'],
                   'quota-type': self.parameters['type'],
                   'qtree': self.parameters['qtree']}
        options.update(modify_attrs)
        if self.parameters.get('policy'):
            options['policy'] = str(self.parameters['policy'])
        modify_entry = netapp_utils.zapi.NaElement.create_node_with_children(
            'quota-modify-entry', **options)
        try:
            self.server.invoke_successfully(modify_entry, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying quota entry %s: %s'
                                  % (self.parameters['volume'], to_native(error)),
                                  exception=traceback.format_exc())

    def on_or_off_quota(self, status):
        """
        on or off quota
        """
        quota = netapp_utils.zapi.NaElement.create_node_with_children(
            status, **{'volume': self.parameters['volume']})
        try:
            self.server.invoke_successfully(quota,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error setting %s for %s: %s'
                                  % (status, self.parameters['volume'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to quotas
        """
        netapp_utils.ems_log_event("na_ontap_quotas", self.server)
        modify_quota_status = None
        modify_quota = None
        current = self.get_quotas()
        if 'set_quota_status' in self.parameters:
            quota_status = self.get_quota_status()
            if quota_status is not None:
                quota_status_action = self.na_helper.get_modified_attributes(
                    {'set_quota_status': True if quota_status == 'on' else False}, self.parameters)
                if quota_status_action:
                    modify_quota_status = 'quota-on' if quota_status_action['set_quota_status'] else 'quota-off'
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action is None:
            modify_quota = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.quota_entry_set()
                elif cd_action == 'delete':
                    self.quota_entry_delete()
                elif modify_quota is not None:
                    for key in list(modify_quota):
                        modify_quota[key.replace("_", "-")] = modify_quota.pop(key)
                    self.quota_entry_modify(modify_quota)
                if modify_quota_status is not None:
                    self.on_or_off_quota(modify_quota_status)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    '''Execute action'''
    quota_obj = NetAppONTAPQuotas()
    quota_obj.apply()


if __name__ == '__main__':
    main()
