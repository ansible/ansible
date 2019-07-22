#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_user_role

short_description: NetApp ONTAP user role configuration and management
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create or destroy user roles

options:

  state:
    description:
    - Whether the specified user should exist or not.
    choices: ['present', 'absent']
    default: present

  name:
    description:
    - The name of the role to manage.
    required: true

  command_directory_name:
    description:
    - The command or command directory to which the role has an access.
    required: true

  access_level:
    description:
    - The name of the role to manage.
    choices: ['none', 'readonly', 'all']
    default: all

  query:
    description:
    - A query for the role. The query must apply to the specified command or directory name.
    - Use double quotes "" for modifying a existing query to none.
    version_added: '2.8'

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """

    - name: Create User Role
      na_ontap_user_role:
        state: present
        name: ansibleRole
        command_directory_name: volume
        access_level: none
        query: show
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Modify User Role
      na_ontap_user_role:
        state: present
        name: ansibleRole
        command_directory_name: volume
        access_level: none
        query: ""
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
from ansible.module_utils.netapp_module import NetAppModule
import ansible.module_utils.netapp as netapp_utils


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapUserRole(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            command_directory_name=dict(required=True, type='str'),
            access_level=dict(required=False, type='str', default='all',
                              choices=['none', 'readonly', 'all']),
            vserver=dict(required=True, type='str'),
            query=dict(required=False, type='str')
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

    def get_role(self):
        """
        Checks if the role exists for specific command-directory-name.

        :return:
            True if role found
            False if role is not found
        :rtype: bool
        """
        options = {'vserver': self.parameters['vserver'],
                   'role-name': self.parameters['name'],
                   'command-directory-name': self.parameters['command_directory_name']}

        security_login_role_get_iter = netapp_utils.zapi.NaElement(
            'security-login-role-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-role-info', **options)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_role_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(
                security_login_role_get_iter, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            # Error 16031 denotes a role not being found.
            if to_native(e.code) == "16031":
                return None
            # Error 16039 denotes command directory not found.
            elif to_native(e.code) == "16039":
                return None
            else:
                self.module.fail_json(msg='Error getting role %s: %s' % (self.name, to_native(e)),
                                      exception=traceback.format_exc())
        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            role_info = result.get_child_by_name('attributes-list').get_child_by_name('security-login-role-info')
            result = {
                'name': role_info['role-name'],
                'access_level': role_info['access-level'],
                'command_directory_name': role_info['command-directory-name'],
                'query': role_info['role-query']
            }
            return result

        return None

    def create_role(self):
        options = {'vserver': self.parameters['vserver'],
                   'role-name': self.parameters['name'],
                   'command-directory-name': self.parameters['command_directory_name'],
                   'access-level': self.parameters['access_level']}
        if self.parameters.get('query'):
            options['role-query'] = self.parameters['query']
        role_create = netapp_utils.zapi.NaElement.create_node_with_children('security-login-role-create', **options)

        try:
            self.server.invoke_successfully(role_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating role %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_role(self):
        role_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-role-delete', **{'vserver': self.parameters['vserver'],
                                             'role-name': self.parameters['name'],
                                             'command-directory-name':
                                                 self.parameters['command_directory_name']})

        try:
            self.server.invoke_successfully(role_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing role %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_role(self, modify):
        options = {'vserver': self.parameters['vserver'],
                   'role-name': self.parameters['name'],
                   'command-directory-name': self.parameters['command_directory_name']}
        if 'access_level' in modify.keys():
            options['access-level'] = self.parameters['access_level']
        if 'query' in modify.keys():
            options['role-query'] = self.parameters['query']

        role_modify = netapp_utils.zapi.NaElement.create_node_with_children('security-login-role-modify', **options)

        try:
            self.server.invoke_successfully(role_modify,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying role %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        self.asup_log_for_cserver('na_ontap_user_role')
        current = self.get_role()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)

        # if desired state specify empty quote query and current query is None, set desired query to None.
        # otherwise na_helper.get_modified_attributes will detect a change.
        if self.parameters.get('query') == '' and current is not None:
            if current['query'] is None:
                self.parameters['query'] = None

        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_role()
                elif cd_action == 'delete':
                    self.delete_role()
                elif modify:
                    self.modify_role(modify)
        self.module.exit_json(changed=self.na_helper.changed)

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        netapp_utils.ems_log_event(event_name, self.server)


def main():
    obj = NetAppOntapUserRole()
    obj.apply()


if __name__ == '__main__':
    main()
