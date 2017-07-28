#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_user

short_description: useradmin configuration and management
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy users.

options:

  state:
    description:
    - Whether the specified user should exist or not.
    required: true
    choices: ['present', 'absent']

  name:
    description:
    - The name of the user to manage.
    required: true

  application:
    description:
    - Applications to grant access to.
    required: true
    choices: ['console', 'http','ontapi','rsh','snmp','sp','ssh','telnet']

  authentication_method:
    description:
    - Authentication method for the application.
    - Not all authentication methods are valid for an application.
    - Valid authentication methods for each application are as denoted in I(authentication_choices_description).
    - password for console application
    - password, domain, nsswitch, cert for http application.
    - password, domain, nsswitch, cert for ontapi application.
    - community for snmp application (when creating SNMPv1 and SNMPv2 users).
    - usm and community for snmp application (when creating SNMPv3 users).
    - password for sp application.
    - password for rsh application.
    - password for telnet application.
    - password, publickey, domain, nsswitch for ssh application.
    required: true
    choices: ['community', 'password', 'publickey', 'domain', 'nsswitch', 'usm']

  set_password:
    description:
    - Password for the user account.
    - It is ignored for creating snmp users, but is required for creating non-snmp users.
    - For an existing user, this value will be used as the new password.
    default: None

  role_name:
    description:
    - The name of the role. Required when C(state=present)


  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """

    - name: Create User
      na_cdot_user:
        state: present
        name: SampleUser
        application: ssh
        authentication_method: password
        set_password: apn1242183u1298u41
        role_name: vsadmin
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


class NetAppCDOTUser(object):
    """
    Common operations to manage users and roles.
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),

            application=dict(required=True, type='str', choices=[
                'console', 'http', 'ontapi', 'rsh',
                'snmp', 'sp', 'ssh', 'telnet']),
            authentication_method=dict(required=True, type='str',
                                       choices=['community', 'password',
                                                'publickey', 'domain',
                                                'nsswitch', 'usm']),
            set_password=dict(required=False, type='str', default=None),
            role_name=dict(required=False, type='str'),

            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['role_name'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']

        self.application = p['application']
        self.authentication_method = p['authentication_method']
        self.set_password = p['set_password']
        self.role_name = p['role_name']

        self.vserver = p['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def get_user(self):
        """
        Checks if the user exists.

        :return:
            True if user found
            False if user is not found
        :rtype: bool
        """

        security_login_get_iter = netapp_utils.zapi.NaElement('security-login-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-account-info', **{'vserver': self.vserver,
                                              'user-name': self.name,
                                              'application': self.application,
                                              'authentication-method':
                                                  self.authentication_method})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(security_login_get_iter,
                                                     enable_tunneling=False)

            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                return True
            else:
                return False

        except netapp_utils.zapi.NaApiError as e:
            # Error 16034 denotes a user not being found.
            if to_native(e.code) == "16034":
                return False
            else:
                self.module.fail_json(msg='Error getting user %s: %s' % (self.name, to_native(e)),
                                      exception=traceback.format_exc())

    def create_user(self):
        user_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-create', **{'vserver': self.vserver,
                                        'user-name': self.name,
                                        'application': self.application,
                                        'authentication-method':
                                            self.authentication_method,
                                        'role-name': self.role_name})
        if self.set_password is not None:
            user_create.add_new_child('password', self.set_password)

        try:
            self.server.invoke_successfully(user_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error creating user %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_user(self):
        user_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-delete', **{'vserver': self.vserver,
                                        'user-name': self.name,
                                        'application': self.application,
                                        'authentication-method':
                                            self.authentication_method})

        try:
            self.server.invoke_successfully(user_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error removing user %s: %s' % (self.name, to_native(e)),
                                  exception=traceback.format_exc())

    def change_password(self):
        """
        Changes the password

        :return:
            True if password updated
            False if password is not updated
        :rtype: bool
        """
        self.server.set_vserver(self.vserver)
        modify_password = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-modify-password', **{
                'new-password': str(self.set_password),
                'user-name': self.name})
        try:
            self.server.invoke_successfully(modify_password,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            if to_native(e.code) == '13114':
                return False
            else:
                self.module.fail_json(msg='Error setting password for user %s: %s' % (self.name, to_native(e)),
                                      exception=traceback.format_exc())

        self.server.set_vserver(None)
        return True

    def apply(self):
        property_changed = False
        password_changed = False
        user_exists = self.get_user()

        if user_exists:
            if self.state == 'absent':
                property_changed = True

            elif self.state == 'present':
                if self.set_password is not None:
                    password_changed = self.change_password()
        else:
            if self.state == 'present':
                # Check if anything needs to be updated
                property_changed = True

        if property_changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not user_exists:
                        self.create_user()

                    # Add ability to update parameters.

                elif self.state == 'absent':
                    self.delete_user()

        changed = property_changed or password_changed
        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTUser()
    v.apply()

if __name__ == '__main__':
    main()
