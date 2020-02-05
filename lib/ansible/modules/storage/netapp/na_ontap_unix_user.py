#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_unix_user

short_description: NetApp ONTAP UNIX users
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create, delete or modify UNIX users local to ONTAP.

options:

  state:
    description:
    - Whether the specified user should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - Specifies user's UNIX account name.
    - Non-modifiable.
    required: true

  group_id:
    description:
    - Specifies the primary group identification number for the UNIX user
    - Required for create, modifiable.

  vserver:
    description:
    - Specifies the Vserver for the UNIX user.
    - Non-modifiable.
    required: true

  id:
    description:
    - Specifies an identification number for the UNIX user.
    - Required for create, modifiable.

  full_name:
    description:
    - Specifies the full name of the UNIX user
    - Optional for create, modifiable.
'''

EXAMPLES = """

    - name: Create UNIX User
      na_ontap_unix_user:
        state: present
        name: SampleUser
        vserver: ansibleVServer
        group_id: 1
        id: 2
        full_name: Test User
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete UNIX User
      na_ontap_unix_user:
        state: absent
        name: SampleUser
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


class NetAppOntapUnixUser(object):
    """
    Common operations to manage users and roles.
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            group_id=dict(required=False, type='int'),
            id=dict(required=False, type='int'),
            full_name=dict(required=False, type='str'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_unix_user(self):
        """
        Checks if the UNIX user exists.

        :return:
            dict() if user found
            None if user is not found
        """

        get_unix_user = netapp_utils.zapi.NaElement('name-mapping-unix-user-get-iter')
        attributes = {
            'query': {
                'unix-user-info': {
                    'user-name': self.parameters['name'],
                    'vserver': self.parameters['vserver'],
                }
            }
        }
        get_unix_user.translate_struct(attributes)
        try:
            result = self.server.invoke_successfully(get_unix_user, enable_tunneling=True)
            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                user_info = result['attributes-list']['unix-user-info']
                return {'group_id': int(user_info['group-id']),
                        'id': int(user_info['user-id']),
                        'full_name': user_info['full-name']}
            return None
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error getting UNIX user %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def create_unix_user(self):
        """
        Creates an UNIX user in the specified Vserver

        :return: None
        """
        if self.parameters.get('group_id') is None or self.parameters.get('id') is None:
            self.module.fail_json(msg='Error: Missing one or more required parameters for create: (group_id, id)')

        user_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'name-mapping-unix-user-create', **{'user-name': self.parameters['name'],
                                                'group-id': str(self.parameters['group_id']),
                                                'user-id': str(self.parameters['id'])})
        if self.parameters.get('full_name') is not None:
            user_create.add_new_child('full-name', self.parameters['full_name'])

        try:
            self.server.invoke_successfully(user_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating UNIX user %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_unix_user(self):
        """
        Deletes an UNIX user from a vserver

        :return: None
        """
        user_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'name-mapping-unix-user-destroy', **{'user-name': self.parameters['name']})

        try:
            self.server.invoke_successfully(user_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing UNIX user %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_unix_user(self, params):
        user_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'name-mapping-unix-user-modify', **{'user-name': self.parameters['name']})
        for key in params:
            if key == 'group_id':
                user_modify.add_new_child('group-id', str(params['group_id']))
            if key == 'id':
                user_modify.add_new_child('user-id', str(params['id']))
            if key == 'full_name':
                user_modify.add_new_child('full-name', params['full_name'])

        try:
            self.server.invoke_successfully(user_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying UNIX user %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        """
          Autosupport log for unix_user
          :return: None
          """
        netapp_utils.ems_log_event("na_ontap_unix_user", self.server)

    def apply(self):
        """
        Invoke appropriate action based on playbook parameters

        :return: None
        """
        self.autosupport_log()
        current = self.get_unix_user()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if self.parameters['state'] == 'present' and cd_action is None:
            modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_unix_user()
                elif cd_action == 'delete':
                    self.delete_unix_user()
                else:
                    self.modify_unix_user(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    obj = NetAppOntapUnixUser()
    obj.apply()


if __name__ == '__main__':
    main()
