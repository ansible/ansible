#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_user_role

short_description: useradmin configuration and management
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy user roles

options:

  state:
    description:
    - Whether the specified user should exist or not.
    required: true
    choices: ['present', 'absent']

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
    default: 'all'

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """

    - name: Create User Role
      na_cdot_user_role:
        state: present
        name: ansibleRole
        command_directory_name: DEFAULT
        access_level: none
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


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppCDOTUserRole(object):

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),

            command_directory_name=dict(required=True, type='str'),
            access_level=dict(required=False, type='str', default='all',
                              choices=['none', 'readonly', 'all']),

            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']

        self.command_directory_name = p['command_directory_name']
        self.access_level = p['access_level']

        self.vserver = p['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def get_role(self):
        """
        Checks if the role exists for specific command-directory-name.

        :return:
            True if role found
            False if role is not found
        :rtype: bool
        """

        security_login_role_get_iter = netapp_utils.zapi.NaElement(
            'security-login-role-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-role-info', **{'vserver': self.vserver,
                                           'role-name': self.name,
                                           'command-directory-name':
                                               self.command_directory_name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_role_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(
                security_login_role_get_iter, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            # Error 16031 denotes a role not being found.
            if to_native(e.code) == "16031":
                return False
            else:
                self.module.fail_json(msg='Error getting role %s: %s' % (self.name, to_native(e)),
                                      exception=traceback.format_exc())

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_role(self):
        role_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-role-create', **{'vserver': self.vserver,
                                             'role-name': self.name,
                                             'command-directory-name':
                                                 self.command_directory_name,
                                             'access-level':
                                                 self.access_level})

        try:
            self.server.invoke_successfully(role_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error creating role %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_role(self):
        role_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-role-delete', **{'vserver': self.vserver,
                                             'role-name': self.name,
                                             'command-directory-name':
                                                 self.command_directory_name})

        try:
            self.server.invoke_successfully(role_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error removing role %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = False
        role_exists = self.get_role()

        if role_exists:
            if self.state == 'absent':
                changed = True

            # Check if properties need to be updated
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not role_exists:
                        self.create_role()

                    # Update properties

                elif self.state == 'absent':
                    self.delete_role()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTUserRole()
    v.apply()

if __name__ == '__main__':
    main()
