#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_user

short_description: NetApp ONTAP user configuration and management
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

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
  applications:
    description:
    - List of application to grant access to.
    required: true
    type: list
    choices: ['console', 'http','ontapi','rsh','snmp','service-processor','sp','ssh','telnet']
    aliases:
      - application
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
    choices: ['community', 'password', 'publickey', 'domain', 'nsswitch', 'usm', 'cert']
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
        applications: ssh,console
        authentication_method: password
        set_password: apn1242183u1298u41
        lock_user: True
        role_name: vsadmin
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete User
      na_ontap_user:
        state: absent
        name: SampleUser
        applications: ssh
        authentication_method: password
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


class NetAppOntapUser(object):
    """
    Common operations to manage users and roles.
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),

            applications=dict(required=True, type='list', aliases=['application'],
                              choices=['console', 'http', 'ontapi', 'rsh', 'snmp',
                                       'sp', 'service-processor', 'ssh', 'telnet'],),
            authentication_method=dict(required=True, type='str',
                                       choices=['community', 'password', 'publickey', 'domain', 'nsswitch', 'usm', 'cert']),
            set_password=dict(required=False, type='str', no_log=True),
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

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_user(self, application=None):
        """
        Checks if the user exists.
        :param: application: application to grant access to
        :return:
            Dictionary if user found
            None if user is not found
        """
        security_login_get_iter = netapp_utils.zapi.NaElement('security-login-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-account-info', **{'vserver': self.parameters['vserver'],
                                              'user-name': self.parameters['name'],
                                              'authentication-method': self.parameters['authentication_method']})
        if application is not None:
            query_details.add_new_child('application', application)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_get_iter.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(security_login_get_iter,
                                                     enable_tunneling=False)
            if result.get_child_by_name('num-records') and \
                    int(result.get_child_content('num-records')) >= 1:
                interface_attributes = result.get_child_by_name('attributes-list').\
                    get_child_by_name('security-login-account-info')
                return_value = {
                    'lock_user': interface_attributes.get_child_content('is-locked'),
                    'role_name': interface_attributes.get_child_content('role-name')
                }
                return return_value
            return None
        except netapp_utils.zapi.NaApiError as error:
            # Error 16034 denotes a user not being found.
            if to_native(error.code) == "16034":
                return None
            # Error 16043 denotes the user existing, but the application missing
            elif to_native(error.code) == "16043":
                return None
            else:
                self.module.fail_json(msg='Error getting user %s: %s' % (self.parameters['name'], to_native(error)),
                                      exception=traceback.format_exc())

    def create_user(self, application):
        """
        creates the user for the given application and authentication_method
        :param: application: application to grant access to
        """
        user_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-create', **{'vserver': self.parameters['vserver'],
                                        'user-name': self.parameters['name'],
                                        'application': application,
                                        'authentication-method': self.parameters['authentication_method'],
                                        'role-name': self.parameters.get('role_name')})
        if self.parameters.get('set_password') is not None:
            user_create.add_new_child('password', self.parameters.get('set_password'))

        try:
            self.server.invoke_successfully(user_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating user %s: %s' % (self.parameters['name'], to_native(error)),
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
            'security-login-lock', **{'vserver': self.parameters['vserver'],
                                      'user-name': self.parameters['name']})

        try:
            self.server.invoke_successfully(user_lock,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error locking user %s: %s' % (self.parameters['name'], to_native(error)),
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
            'security-login-unlock', **{'vserver': self.parameters['vserver'],
                                        'user-name': self.parameters['name']})

        try:
            self.server.invoke_successfully(user_unlock,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == '13114':
                return False
            else:
                self.module.fail_json(msg='Error unlocking user %s: %s' % (self.parameters['name'], to_native(error)),
                                      exception=traceback.format_exc())
        return True

    def delete_user(self, application):
        """
        deletes the user for the given application and authentication_method
        :param: application: application to grant access to
        """
        user_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-delete', **{'vserver': self.parameters['vserver'],
                                        'user-name': self.parameters['name'],
                                        'application': application,
                                        'authentication-method': self.parameters['authentication_method']})

        try:
            self.server.invoke_successfully(user_delete,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error removing user %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def change_password(self):
        """
        Changes the password

        :return:
            True if password updated
            False if password is not updated
        :rtype: bool
        """
        # self.server.set_vserver(self.parameters['vserver'])
        modify_password = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-modify-password', **{
                'new-password': str(self.parameters.get('set_password')),
                'user-name': self.parameters['name']})
        try:
            self.server.invoke_successfully(modify_password,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            if to_native(error.code) == '13114':
                return False
            # if the user give the same password, instead of returning an error, return ok
            if to_native(error.code) == '13214' and \
                    (error.message.startswith('New password must be different than last 6 passwords.')
                     or error.message.startswith('New password must be different than the old password.')):
                return False
            self.module.fail_json(msg='Error setting password for user %s: %s' % (self.parameters['name'], to_native(error)),
                                      exception=traceback.format_exc())

        self.server.set_vserver(None)
        return True

    def modify_user(self, application):
        """
        Modify user
        """
        user_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'security-login-modify', **{'vserver': self.parameters['vserver'],
                                        'user-name': self.parameters['name'],
                                        'application': application,
                                        'authentication-method': self.parameters['authentication_method'],
                                        'role-name': self.parameters.get('role_name')})

        try:
            self.server.invoke_successfully(user_modify,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying user %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        create_delete_decision = {}
        modify_decision = {}

        netapp_utils.ems_log_event("na_ontap_user", self.server)
        for application in self.parameters['applications']:
            current = self.get_user(application)
            if current is not None:
                current['lock_user'] = self.na_helper.get_value_for_bool(True, current['lock_user'])

            cd_action = self.na_helper.get_cd_action(current, self.parameters)

            if cd_action is not None:
                create_delete_decision[application] = cd_action
            else:
                modify_decision[application] = self.na_helper.get_modified_attributes(current, self.parameters)

        if not create_delete_decision and self.parameters.get('state') == 'present':
            if self.parameters.get('set_password') is not None:
                self.na_helper.changed = True

        if self.na_helper.changed:

            if self.module.check_mode:
                pass
            else:
                for application in create_delete_decision:
                    if create_delete_decision[application] == 'create':
                        self.create_user(application)
                    elif create_delete_decision[application] == 'delete':
                        self.delete_user(application)
                lock_user = False
                for application in modify_decision:
                    if 'role_name' in modify_decision[application]:
                        self.modify_user(application)
                    if 'lock_user' in modify_decision[application]:
                        lock_user = True

                if lock_user:
                    if self.parameters.get('lock_user'):
                        self.lock_given_user()
                    else:
                        self.unlock_given_user()
                if not create_delete_decision and self.parameters.get('set_password') is not None:
                    # if change password return false nothing has changed so we need to set changed to False
                    self.na_helper.changed = self.change_password()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    obj = NetAppOntapUser()
    obj.apply()


if __name__ == '__main__':
    main()
