#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# import untangle

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
author: "Archana Ganesan (garchana@netapp.com), Suhas Bangalore Shekar (bsuhas@netapp.com)"
description:
  - "Create or destroy or modify(path) cifs-share on ONTAP"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_cifs
options:
  path:
    description:
      The file system path that is shared through this CIFS share. The path is the full, user visible path relative
      to the vserver root, and it might be crossing junction mount points. The path is in UTF8 and uses forward
      slash as directory separator
    required: false
  vserver:
    description:
      - "Vserver containing the CIFS share."
    required: true
  share_name:
    description:
      The name of the CIFS share. The CIFS share name is a UTF-8 string with the following characters being
      illegal; control characters from 0x00 to 0x1F, both inclusive, 0x22 (double quotes)
    required: true
  state:
    choices: ['present', 'absent']
    description:
      - "Whether the specified CIFS share should exist or not."
    required: false
    default: present
short_description: "Manage NetApp cifs-share"
version_added: "2.6"

'''

EXAMPLES = """
    - name: Create CIFS share
      na_ontap_cifs:
        state: present
        share_name: cifsShareName
        path: /
        vserver: vserverName
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Delete CIFS share
      na_ontap_cifs:
        state: absent
        share_name: cifsShareName
        vserver: vserverName
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: Modify path CIFS share
      na_ontap_cifs:
        state: present
        share_name: pb_test
        vserver: vserverName
        path: /
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


class NetAppONTAPCifsShare(object):
    """
    Methods to create/delete/modify(path) CIFS share
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=[
                       'present', 'absent'], default='present'),
            share_name=dict(required=True, type='str'),
            path=dict(required=False, type='str'),
            vserver=dict(required=True, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['share_name', 'path'])
            ],
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        self.state = parameters['state']
        self.share_name = parameters['share_name']
        self.path = parameters['path']
        self.vserver = parameters['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)

    def get_cifs_share(self):
        """
        Return details about the cifs-share
        :param:
            name : Name of the cifs-share
        :return: Details about the cifs-share. None if not found.
        :rtype: dict
        """
        cifs_iter = netapp_utils.zapi.NaElement('cifs-share-get-iter')
        cifs_info = netapp_utils.zapi.NaElement('cifs-share')
        cifs_info.add_new_child('share-name', self.share_name)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(cifs_info)

        cifs_iter.add_child_elem(query)

        result = self.server.invoke_successfully(cifs_iter, True)

        return_value = None
        print(result.to_string())
        # check if query returns the expected cifs-share
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:

            cifs_acl = result.get_child_by_name('attributes-list').\
                get_child_by_name('cifs-share')
            return_value = {
                'share': cifs_acl.get_child_content('share-name'),
                'path': cifs_acl.get_child_content('path'),
            }

        return return_value

    def create_cifs_share(self):
        """
        Create CIFS share
        """
        cifs_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-create', **{'share-name': self.share_name,
                                    'path': self.path})

        try:
            self.server.invoke_successfully(cifs_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:

            self.module.fail_json(msg='Error creating cifs-share %s: %s'
                                  % (self.share_name, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_cifs_share(self):
        """
        Delete CIFS share
        """
        cifs_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-delete', **{'share-name': self.share_name})

        try:
            self.server.invoke_successfully(cifs_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting cifs-share %s: %s'
                                  % (self.share_name, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_cifs_share(self):
        """
        modilfy path for the given CIFS share
        """
        cifs_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-modify', **{'share-name': self.share_name,
                                    'path': self.path})
        try:
            self.server.invoke_successfully(cifs_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying cifs-share %s:%s'
                                  % (self.share_name, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Apply action to cifs share'''
        changed = False
        cifs_exists = False
        netapp_utils.ems_log_event("na_ontap_cifs", self.server)
        cifs_details = self.get_cifs_share()
        if cifs_details:
            cifs_exists = True
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present':
                if cifs_details['path'] != self.path:  # modify path
                    changed = True
        else:
            if self.state == 'present':  # create
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute create
                    if not cifs_exists:
                        self.create_cifs_share()
                    else:  # execute modify path
                        self.modify_cifs_share()
                elif self.state == 'absent':  # execute delete
                    self.delete_cifs_share()

        self.module.exit_json(changed=changed)


def main():
    '''Execute action from playbook'''
    cifs_obj = NetAppONTAPCifsShare()
    cifs_obj.apply()


if __name__ == '__main__':
    main()
