#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_admin_users

short_description: NetApp Element Software Manage Admin Users
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, destroy, or update admin users on SolidFire

options:

    state:
        description:
        - Whether the specified account should exist or not.
        required: true
        choices: ['present', 'absent']

    element_username:
        description:
        - Unique username for this account. (May be 1 to 64 characters in length).
        required: true

    element_password:
        description:
        - The password for the new admin account. Setting the password attribute will always reset your password, even if the password is the same

    acceptEula:
        description:
        - Boolean, true for accepting Eula, False Eula
        type: bool

    access:
        description:
        - A list of type the admin has access to
'''

EXAMPLES = """
    - name: Add admin user
      na_elementsw_admin_users:
        state: present
        username: "{{ admin_user_name }}"
        password: "{{ admin_password }}"
        hostname: "{{ hostname }}"
        element_username: carchi8py
        element_password: carchi8py
        acceptEula: True
        access: accounts,drives

    - name: modify admin user
      na_elementsw_admin_users:
        state: present
        username: "{{ admin_user_name }}"
        password: "{{ admin_password }}"
        hostname: "{{ hostname }}"
        element_username: carchi8py
        element_password: carchi8py12
        acceptEula: True
        access: accounts,drives,nodes

    - name: delete admin user
      na_elementsw_admin_users:
        state: absent
        username: "{{ admin_user_name }}"
        password: "{{ admin_password }}"
        hostname: "{{ hostname }}"
        element_username: carchi8py
"""

RETURN = """

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule


HAS_SF_SDK = netapp_utils.has_sf_sdk()


class NetAppElementSWAdminUser(object):
    """
    Class to set, modify and delete admin users on ElementSW box
    """

    def __init__(self):
        """
        Initialize the NetAppElementSWAdminUser class.
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            element_username=dict(required=True, type='str'),
            element_password=dict(required=False, type='str', no_log=True),
            acceptEula=dict(required=False, type='bool'),
            access=dict(required=False, type='list')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        param = self.module.params
        # set up state variables
        self.state = param['state']
        self.element_username = param['element_username']
        self.element_password = param['element_password']
        self.acceptEula = param['acceptEula']
        self.access = param['access']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_admin_users')

    def does_admin_user_exist(self):
        """
        Checks to see if an admin user exists or not
        :return: True if the user exist, False if it dose not exist
        """
        admins_list = self.sfe.list_cluster_admins()
        for admin in admins_list.cluster_admins:
            if admin.username == self.element_username:
                return True
        return False

    def get_admin_user(self):
        """
        Get the admin user object
        :return: the admin user object
        """
        admins_list = self.sfe.list_cluster_admins()
        for admin in admins_list.cluster_admins:
            if admin.username == self.element_username:
                return admin
        return None

    def modify_admin_user(self):
        """
        Modify a admin user. If a password is set the user will be modified as there is no way to
        compare a new password with an existing one
        :return: if a user was modified or not
        """
        changed = False
        admin_user = self.get_admin_user()
        if self.access is not None and len(self.access) > 0:
            for access in self.access:
                if access not in admin_user.access:
                    changed = True
        if changed:
            self.sfe.modify_cluster_admin(cluster_admin_id=admin_user.cluster_admin_id,
                                          access=self.access,
                                          password=self.element_password,
                                          attributes=self.attributes)

        return changed

    def add_admin_user(self):
        """
        Add's a new admin user to the element cluster
        :return: nothing
        """
        self.sfe.add_cluster_admin(username=self.element_username,
                                   password=self.element_password,
                                   access=self.access,
                                   accept_eula=self.acceptEula,
                                   attributes=self.attributes)

    def delete_admin_user(self):
        """
        Deletes an existing admin user from the element cluster
        :return: nothing
        """
        admin_user = self.get_admin_user()
        self.sfe.remove_cluster_admin(cluster_admin_id=admin_user.cluster_admin_id)

    def apply(self):
        """
        determines which method to call to set, delete or modify admin users
        :return:
        """
        changed = False
        if self.state == "present":
            if self.does_admin_user_exist():
                changed = self.modify_admin_user()
            else:
                self.add_admin_user()
                changed = True
        else:
            if self.does_admin_user_exist():
                self.delete_admin_user()
                changed = True

        self.module.exit_json(changed=changed)


def main():
    v = NetAppElementSWAdminUser()
    v.apply()


if __name__ == '__main__':
    main()
