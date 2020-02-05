#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# import untangle

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
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

  share_properties:
    description:
      - The list of properties for the CIFS share
    required: false
    version_added: '2.8'

  symlink_properties:
    description:
      - The list of symlink properties for this CIFS share
    required: false
    version_added: '2.8'

  state:
    choices: ['present', 'absent']
    description:
      - "Whether the specified CIFS share should exist or not."
    required: false
    default: present

  vscan_fileop_profile:
    choices: ['no_scan', 'standard', 'strict', 'writes_only']
    description:
      - Profile_set of file_ops to which vscan on access scanning is applicable.
    required: false
    version_added: '2.9'

short_description: NetApp ONTAP Manage cifs-share
version_added: "2.6"

'''

EXAMPLES = """
    - name: Create CIFS share
      na_ontap_cifs:
        state: present
        share_name: cifsShareName
        path: /
        vserver: vserverName
        share_properties: browsable,oplocks
        symlink_properties: read_only,enable
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
        share_properties: show_previous_versions
        symlink_properties: disable
        vscan_fileop_profile: no_scan
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
            vserver=dict(required=True, type='str'),
            share_properties=dict(required=False, type='list'),
            symlink_properties=dict(required=False, type='list'),
            vscan_fileop_profile=dict(required=False, type='str', choices=['no_scan', 'standard', 'strict', 'writes_only'])
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.parameters.get('vserver'))

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
        cifs_info.add_new_child('share-name', self.parameters.get('share_name'))
        cifs_info.add_new_child('vserver', self.parameters.get('vserver'))

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(cifs_info)

        cifs_iter.add_child_elem(query)

        result = self.server.invoke_successfully(cifs_iter, True)

        return_value = None
        # check if query returns the expected cifs-share
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            properties_list = []
            symlink_list = []
            cifs_attrs = result.get_child_by_name('attributes-list').\
                get_child_by_name('cifs-share')
            if cifs_attrs.get_child_by_name('share-properties'):
                properties_attrs = cifs_attrs['share-properties']
                if properties_attrs is not None:
                    properties_list = [property.get_content() for property in properties_attrs.get_children()]
            if cifs_attrs.get_child_by_name('symlink-properties'):
                symlink_attrs = cifs_attrs['symlink-properties']
                if symlink_attrs is not None:
                    symlink_list = [symlink.get_content() for symlink in symlink_attrs.get_children()]
            return_value = {
                'share': cifs_attrs.get_child_content('share-name'),
                'path': cifs_attrs.get_child_content('path'),
                'share_properties': properties_list,
                'symlink_properties': symlink_list
            }
            if cifs_attrs.get_child_by_name('vscan-fileop-profile'):
                return_value['vscan_fileop_profile'] = cifs_attrs['vscan-fileop-profile']

        return return_value

    def create_cifs_share(self):
        """
        Create CIFS share
        """
        options = {'share-name': self.parameters.get('share_name'),
                   'path': self.parameters.get('path')}
        cifs_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-create', **options)
        if self.parameters.get('share_properties'):
            property_attrs = netapp_utils.zapi.NaElement('share-properties')
            cifs_create.add_child_elem(property_attrs)
            for property in self.parameters.get('share_properties'):
                property_attrs.add_new_child('cifs-share-properties', property)
        if self.parameters.get('symlink_properties'):
            symlink_attrs = netapp_utils.zapi.NaElement('symlink-properties')
            cifs_create.add_child_elem(symlink_attrs)
            for symlink in self.parameters.get('symlink_properties'):
                symlink_attrs.add_new_child('cifs-share-symlink-properties', symlink)
        if self.parameters.get('vscan_fileop_profile'):
            fileop_attrs = netapp_utils.zapi.NaElement('vscan-fileop-profile')
            fileop_attrs.set_content(self.parameters['vscan_fileop_profile'])
            cifs_create.add_child_elem(fileop_attrs)

        try:
            self.server.invoke_successfully(cifs_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:

            self.module.fail_json(msg='Error creating cifs-share %s: %s'
                                  % (self.parameters.get('share_name'), to_native(error)),
                                  exception=traceback.format_exc())

    def delete_cifs_share(self):
        """
        Delete CIFS share
        """
        cifs_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-delete', **{'share-name': self.parameters.get('share_name')})

        try:
            self.server.invoke_successfully(cifs_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting cifs-share %s: %s'
                                  % (self.parameters.get('share_name'), to_native(error)),
                                  exception=traceback.format_exc())

    def modify_cifs_share(self):
        """
        modify path for the given CIFS share
        """
        options = {'share-name': self.parameters.get('share_name')}
        cifs_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-share-modify', **options)
        if self.parameters.get('path'):
            cifs_modify.add_new_child('path', self.parameters.get('path'))
        if self.parameters.get('share_properties'):
            property_attrs = netapp_utils.zapi.NaElement('share-properties')
            cifs_modify.add_child_elem(property_attrs)
            for property in self.parameters.get('share_properties'):
                property_attrs.add_new_child('cifs-share-properties', property)
        if self.parameters.get('symlink_properties'):
            symlink_attrs = netapp_utils.zapi.NaElement('symlink-properties')
            cifs_modify.add_child_elem(symlink_attrs)
            for property in self.parameters.get('symlink_properties'):
                symlink_attrs.add_new_child('cifs-share-symlink-properties', property)
        if self.parameters.get('vscan_fileop_profile'):
            fileop_attrs = netapp_utils.zapi.NaElement('vscan-fileop-profile')
            fileop_attrs.set_content(self.parameters['vscan_fileop_profile'])
            cifs_modify.add_child_elem(fileop_attrs)
        try:
            self.server.invoke_successfully(cifs_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying cifs-share %s:%s'
                                  % (self.parameters.get('share_name'), to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Apply action to cifs share'''
        netapp_utils.ems_log_event("na_ontap_cifs", self.server)
        current = self.get_cifs_share()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action is None:
            modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_cifs_share()
                elif cd_action == 'delete':
                    self.delete_cifs_share()
                elif modify:
                    self.modify_cifs_share()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    '''Execute action from playbook'''
    cifs_obj = NetAppONTAPCifsShare()
    cifs_obj.apply()


if __name__ == '__main__':
    main()
