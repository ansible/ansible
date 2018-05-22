#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
author: "Archana Ganesan (garchana@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)"
description:
  - "Create or destroy or modify cifs-share-access-controls on ONTAP"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_cifs_acl
options:
  permission:
    choices: ['no_access', 'read', 'change', 'full_control']
    description:
      -"The access rights that the user or group has on the defined CIFS share."
  share_name:
    description:
      - "The name of the cifs-share-access-control to manage."
    required: true
  state:
    choices: ['present', 'absent']
    description:
      - "Whether the specified CIFS share acl should exist or not."
    default: present
  vserver:
    description:
    - Name of the vserver to use.
    required: true
  user_or_group:
    description:
      - "The user or group name for which the permissions are listed."
    required: true
short_description: "Manage NetApp cifs-share-access-control"
version_added: "2.6"

'''

EXAMPLES = """
    - name: Create CIFS share acl
      na_ontap_cifs_acl:
        state: present
        share_name: cifsShareName
        user_or_group: Everyone
        permission: read
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Modify CIFS share acl permission
      na_ontap_cifs_acl:
        state: present
        share_name: cifsShareName
        permission: change
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


class NetAppONTAPCifsAcl(object):
    """
    Methods to create/delete/modify CIFS share/user access-control
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            share_name=dict(required=True, type='str'),
            user_or_group=dict(required=True, type='str'),
            permission=dict(required=False, type='str', choices=['no_access', 'read', 'change', 'full_control'])
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['share_name', 'user_or_group', 'permission'])
            ],
            supports_check_mode=True
        )
        parameters = self.module.params
        # set up state variables
        self.state = parameters['state']
        self.vserver = parameters['vserver']
        self.share_name = parameters['share_name']
        self.user_or_group = parameters['user_or_group']
        self.permission = parameters['permission']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_cifs_acl(self):
        """
        Return details about the cifs-share-access-control
        :param:
            name : Name of the cifs-share-access-control
        :return: Details about the cifs-share-access-control. None if not found.
        :rtype: dict
        """
        cifs_acl_iter = netapp_utils.zapi.NaElement('cifs-share-access-control-get-iter')
        cifs_acl_info = netapp_utils.zapi.NaElement('cifs-share-access-control')
        cifs_acl_info.add_new_child('share', self.share_name)
        cifs_acl_info.add_new_child('user-or-group', self.user_or_group)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(cifs_acl_info)
        cifs_acl_iter.add_child_elem(query)
        result = self.server.invoke_successfully(cifs_acl_iter, True)
        return_value = None
        # check if query returns the expected cifs-share-access-control
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            cifs_acl = result.get_child_by_name('attributes-list').get_child_by_name('cifs-share-access-control')
            return_value = {
                'share': cifs_acl.get_child_content('share'),
                'user-or-group': cifs_acl.get_child_content('user-or-group'),
                'permission': cifs_acl.get_child_content('permission')
            }

        return return_value

    def create_cifs_acl(self):
        """
        Create access control for the given CIFS share/user-group
        """
        cifs_acl_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-access-control-create', **{'share': self.share_name,
                                                   'user-or-group': self.user_or_group,
                                                   'permission': self.permission})
        try:
            self.server.invoke_successfully(cifs_acl_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:

            self.module.fail_json(msg='Error creating cifs-share-access-control %s: %s'
                                  % (self.share_name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_cifs_acl(self):
        """
        Delete access control for the given CIFS share/user-group
        """
        cifs_acl_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-access-control-delete', **{'share': self.share_name,
                                                   'user-or-group': self.user_or_group})
        try:
            self.server.invoke_successfully(cifs_acl_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting cifs-share-access-control %s: %s'
                                  % (self.share_name, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_cifs_acl_permission(self):
        """
        Change permission for the given CIFS share/user-group
        """
        cifs_acl_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-access-control-modify', **{'share': self.share_name,
                                                   'user-or-group': self.user_or_group,
                                                   'permission': self.permission})
        try:
            self.server.invoke_successfully(cifs_acl_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying cifs-share-access-control permission %s:%s'
                                  % (self.share_name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to cifs-share-access-control
        """
        changed = False
        cifs_acl_exists = False
        netapp_utils.ems_log_event("na_ontap_cifs_acl", self.server)
        cifs_acl_details = self.get_cifs_acl()
        if cifs_acl_details:
            cifs_acl_exists = True
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present':
                if cifs_acl_details['permission'] != self.permission:  # rename
                    changed = True
        else:
            if self.state == 'present':  # create
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute create
                    if not cifs_acl_exists:
                        self.create_cifs_acl()
                    else:  # execute modify
                        self.modify_cifs_acl_permission()
                elif self.state == 'absent':  # execute delete
                    self.delete_cifs_acl()

        self.module.exit_json(changed=changed)


def main():
    """
    Execute action from playbook
    """
    cifs_acl = NetAppONTAPCifsAcl()
    cifs_acl.apply()


if __name__ == '__main__':
    main()
