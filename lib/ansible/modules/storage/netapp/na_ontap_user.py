#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_user

short_description: useradmin configuration and management
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy users.

options:

  state:
    description:
    - Whether the specified user should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - The name of the user to manage.
    required: true

  application:
    description:
    - Application to grant access to.
    required: true
    choices: ['console', 'http','ontapi','rsh','snmp','sp','ssh','telnet']

  authentication_method:
    description:
    - Authentication method for the application.
    - Not all authentication methods are valid for an application.
    - Valid authentication methods for each application are as denoted in I(authentication_choices_description).
    - Password for console application
    - Password, domain, nsswitch, cert for http application.
    - Password, domain, nsswitch, cert for ontapi application.
    - Community for snmp application (when creating SNMPv1 and SNMPv2 users).
    - The usm and community for snmp application (when creating SNMPv3 users).
    - Password for sp application.
    - Password for rsh application.
    - Password for telnet application.
    - Password, publickey, domain, nsswitch for ssh application.
    required: true
    choices: ['community', 'password', 'publickey', 'domain', 'nsswitch', 'usm']

  set_password:
    description:
    - Password for the user account.
    - It is ignored for creating snmp users, but is required for creating non-snmp users.
    - For an existing user, this value will be used as the new password.

  role_name:
    description:
    - The name of the role. Required when C(state=present)

  lock_user:
    description:
    - Whether the specified user account is locked.
    type: bool

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = """

    - name: Create User
      na_ontap_user:
        state: present
        name: SampleUser
        application: ssh
        authentication_method: password
        set_password: apn1242183u1298u41
        lock_user: True
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


class NetAppOntapUser(object):
    """
    Common operations to manage users and roles.
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),

            application=dict(required=True, type='str', choices=[
                'console', 'http', 'ontapi', 'rsh',
                'snmp', 'sp', 'ssh', 'telnet']),
            authentication_method=dict(required=True, type='str',
                                       choices=['community', 'password',
                                                'publickey', 'domain',
                                                'nsswitch', 'usm']),
            set_password=dict(required=False, type='str'),
            role_name=dict(required=False, type='str'),
            lock_user=dict(required=False, type='bool'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['role_name'])
            ],
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.name = parameters['name']
        self.application = parameters['application']
        self.authentication_method = parameters['authentication_method']
        self.set_password = parameters['set_password']
        self.role_name = parameters['role_name']
        self.lock_user = parameters['lock_user']
        self.vserver = parameters['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

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
        return_value = None
        try:
            result = self.server.invoke_successfully(security_login_get_iter,
                                                     enable_tunneling=False)
            if result.get_child_by_name('num-records') and \
                    int(result.get_child_content('num-records')) >= 1:
                interface_attributes = result.get_child_by_name('attributes-list').\
                    get_child_by_name('security-login-account-info')
                return_value = {
                    'is_locked': interface_attributes.get_child_content('is-locked')
                }
            return return_value
        except netapp_utils.zapi.NaApiError as error:
            # Error 16034 denotes a user not being found.
            if to_native(error.code) == "16034":
                return False
            else:
                self.module.fail_json(msg='Error getting user %s: %s' % (self.name, to_native(error)),
                                      exception=traceback.format_exc())

    def get_user_lock_info(self):
        """
        gets details of the user.
        """
        security_login_get_iter = netapp_utils.zapi.NaElement('security-login-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-account-info', **{'vserver': self.vserver,
                                              'user-name': self.name,
                                              'application': self.application,
                                              # 'role-name': self.role_name,
                                              'authentication-method':
                                                  self.authentication_method})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_get_iter.add_child_elem(query)

        result = self.server.invoke_successfully(security_login_get_iter, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            interface_attributes = result.get_child_by_name('attributes-list').\
                get_child_by_name('security-login-account-info')
            return_value = {
                'is_locked': interface_attributes.get_child_content('is-locked')
            }
        return return_value

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
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating user %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def lock_given_user(self):
        """
        locks the user

        :return:
            True if user locked
            False if lock user is not performed
        :rtype: bool
        """
        user_lock = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-lock', **{'vserver': self.vserver,
                                      'user-name': self.name})

        try:
            self.server.invoke_successfully(user_lock,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error locking user %s: %s' % (self.name, to_native(error)),
                                  exception=traceback.format_exc())

    def unlock_given_user(self):
        """
        unlocks the user

        :return:
            True if user unlocked
            False if unlock user is not performed
        :rtype: bool
        """
        user_unlock = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-unlock', **{'vserver': self.vserver,
                                        'user-name': self.name})

        try:
            self.server.invoke_successfully(user_unlock,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == '13114':
                return False
            else:
                self.module.fail_json(msg='Error unlocking user %s: %s' % (self.name, to_native(error)),
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
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing user %s: %s' % (self.name, to_native(error)),
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
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == '13114':
                return False
            else:
                self.module.fail_json(msg='Error setting password for user %s: %s' % (self.name, to_native(error)),
                                      exception=traceback.format_exc())

        self.server.set_vserver(None)
        return True

    def apply(self):
        property_changed = False
        password_changed = False
        lock_user_changed = False
        netapp_utils.ems_log_event("na_ontap_user", self.server)
        user_exists = self.get_user()

        if user_exists:
            if self.state == 'absent':
                property_changed = True
            elif self.state == 'present':
                if self.set_password is not None:
                    password_changed = True
                if self.lock_user is not None:
                    if self.lock_user is True and user_exists['is_locked'] != 'true':
                        lock_user_changed = True
                    elif self.lock_user is False and user_exists['is_locked'] != 'false':
                        lock_user_changed = True
        else:
            if self.state == 'present':
                # Check if anything needs to be updated
                property_changed = True

        changed = property_changed or password_changed or lock_user_changed

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not user_exists:
                        self.create_user()
                    else:
                        if password_changed:
                            self.change_password()
                        if lock_user_changed:
                            if self.lock_user:
                                self.lock_given_user()
                            else:
                                self.unlock_given_user()
                elif self.state == 'absent':
                    self.delete_user()
        self.module.exit_json(changed=changed)


def main():
    obj = NetAppOntapUser()
    obj.apply()


if __name__ == '__main__':
    main()
