#!/usr/bin/python
"""
create Autosupport module to enable, disable or modify
"""

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - "Create/Delete Unix user group"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_unix_group
options:
  state:
    description:
    - Whether the specified group should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - Specifies UNIX group's name, unique for each group.
    - Non-modifiable.
    required: true

  id:
    description:
    - Specifies an identification number for the UNIX group.
    - Group ID is unique for each UNIX group.
    - Required for create, modifiable.

  vserver:
    description:
    - Specifies the Vserver for the UNIX group.
    - Non-modifiable.
    required: true

  skip_name_validation:
    description:
    - Specifies if group name validation is skipped.
    type: bool

short_description: NetApp ONTAP UNIX Group
version_added: "2.8"

"""

EXAMPLES = """
    - name: Create UNIX group
      na_ontap_unix_group:
        state: present
        name: SampleGroup
        vserver: ansibleVServer
        id: 2
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete UNIX group
      na_ontap_unix_group:
        state: absent
        name: SampleGroup
        vserver: ansibleVServer
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


class NetAppOntapUnixGroup(object):
    """
    Common operations to manage UNIX groups
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            id=dict(required=False, type='int'),
            skip_name_validation=dict(required=False, type='bool'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.set_playbook_zapi_key_map()

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def set_playbook_zapi_key_map(self):
        self.na_helper.zapi_string_keys = {
            'name': 'group-name'
        }
        self.na_helper.zapi_int_keys = {
            'id': 'group-id'
        }
        self.na_helper.zapi_bool_keys = {
            'skip_name_validation': 'skip-name-validation'
        }

    def get_unix_group(self):
        """
        Checks if the UNIX group exists.

        :return:
            dict() if group found
            None if group is not found
        """

        get_unix_group = netapp_utils.zapi.NaElement('name-mapping-unix-group-get-iter')
        attributes = {
            'query': {
                'unix-group-info': {
                    'group-name': self.parameters['name'],
                    'vserver': self.parameters['vserver'],
                }
            }
        }
        get_unix_group.translate_struct(attributes)
        try:
            result = self.server.invoke_successfully(get_unix_group, enable_tunneling=True)
            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                group_info = result['attributes-list']['unix-group-info']
                group_details = dict()
            else:
                return None
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting UNIX group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        for item_key, zapi_key in self.na_helper.zapi_string_keys.items():
            group_details[item_key] = group_info[zapi_key]
        for item_key, zapi_key in self.na_helper.zapi_int_keys.items():
            group_details[item_key] = self.na_helper.get_value_for_int(from_zapi=True,
                                                                       value=group_info[zapi_key])
        return group_details

    def create_unix_group(self):
        """
        Creates an UNIX group in the specified Vserver

        :return: None
        """
        if self.parameters.get('id') is None:
            self.module.fail_json(msg='Error: Missing a required parameter for create: (id)')

        group_create = netapp_utils.zapi.NaElement('name-mapping-unix-group-create')
        group_details = {}
        for item in self.parameters:
            if item in self.na_helper.zapi_string_keys:
                zapi_key = self.na_helper.zapi_string_keys.get(item)
                group_details[zapi_key] = self.parameters[item]
            elif item in self.na_helper.zapi_bool_keys:
                zapi_key = self.na_helper.zapi_bool_keys.get(item)
                group_details[zapi_key] = self.na_helper.get_value_for_bool(from_zapi=False,
                                                                            value=self.parameters[item])
            elif item in self.na_helper.zapi_int_keys:
                zapi_key = self.na_helper.zapi_int_keys.get(item)
                group_details[zapi_key] = self.na_helper.get_value_for_int(from_zapi=True,
                                                                           value=self.parameters[item])
        group_create.translate_struct(group_details)
        try:
            self.server.invoke_successfully(group_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating UNIX group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_unix_group(self):
        """
        Deletes an UNIX group from a vserver

        :return: None
        """
        group_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'name-mapping-unix-group-destroy', **{'group-name': self.parameters['name']})

        try:
            self.server.invoke_successfully(group_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing UNIX group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_unix_group(self, params):
        group_modify = netapp_utils.zapi.NaElement('name-mapping-unix-group-modify')
        group_details = {'group-name': self.parameters['name']}
        for key in params:
            if key in self.na_helper.zapi_int_keys:
                zapi_key = self.na_helper.zapi_int_keys.get(key)
                group_details[zapi_key] = self.na_helper.get_value_for_int(from_zapi=True,
                                                                           value=params[key])
        group_modify.translate_struct(group_details)

        try:
            self.server.invoke_successfully(group_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying UNIX group %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        """
          Autosupport log for unix_group
          :return: None
          """
        netapp_utils.ems_log_event("na_ontap_unix_group", self.server)

    def apply(self):
        """
        Invoke appropriate action based on playbook parameters

        :return: None
        """
        self.autosupport_log()
        current = self.get_unix_group()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if self.parameters['state'] == 'present' and cd_action is None:
            modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_unix_group()
                elif cd_action == 'delete':
                    self.delete_unix_group()
                else:
                    self.modify_unix_group(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    obj = NetAppOntapUnixGroup()
    obj.apply()


if __name__ == '__main__':
    main()
