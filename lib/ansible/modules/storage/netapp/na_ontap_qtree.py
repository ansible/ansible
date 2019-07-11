#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_qtree

short_description: NetApp ONTAP manage qtrees
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create or destroy Qtrees.

options:

  state:
    description:
    - Whether the specified qtree should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - The name of the qtree to manage.
    required: true
    type: str

  from_name:
    description:
    - Name of the qtree to be renamed.
    version_added: '2.7'
    type: str

  flexvol_name:
    description:
    - The name of the FlexVol the qtree should exist on. Required when C(state=present).
    required: true
    type: str

  vserver:
    description:
    - The name of the vserver to use.
    required: true
    type: str

  export_policy:
    description:
    - The name of the export policy to apply.
    version_added: '2.9'
    type: str

  security_style:
    description:
    - The security style for the qtree.
    choices: ['unix', 'ntfs', 'mixed']
    version_added: '2.9'

  oplocks:
    description:
    - Whether the oplocks should be enabled or not for the qtree.
    choices: ['enabled', 'disabled']
    version_added: '2.9'

  unix_permissions:
    description:
    - File permissions bits of the qtree.
    version_added: '2.9'
    type: str

'''

EXAMPLES = """
- name: Create Qtrees
  na_ontap_qtree:
    state: present
    name: ansibleQTree
    flexvol_name: ansibleVolume
    export_policy: policyName
    security_style: mixed
    oplocks: disabled
    unix_permissions:
    vserver: ansibleVServer
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Rename Qtrees
  na_ontap_qtree:
    state: present
    from_name: ansibleQTree_rename
    name: ansibleQTree
    flexvol_name: ansibleVolume
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


class NetAppOntapQTree(object):
    '''Class with qtree operations'''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False,
                       choices=['present', 'absent'],
                       default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            flexvol_name=dict(type='str'),
            vserver=dict(required=True, type='str'),
            export_policy=dict(required=False, type='str'),
            security_style=dict(required=False, choices=['unix', 'ntfs', 'mixed']),
            oplocks=dict(required=False, choices=['enabled', 'disabled']),
            unix_permissions=dict(required=False, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['flexvol_name'])
            ],
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.parameters['vserver'])

    def get_qtree(self, name=None):
        """
        Checks if the qtree exists.
        :param:
            name : qtree name
        :return:
            Details about the qtree
            False if qtree is not found
        :rtype: bool
        """
        if name is None:
            name = self.parameters['name']

        qtree_list_iter = netapp_utils.zapi.NaElement('qtree-list-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-info', **{'vserver': self.parameters['vserver'],
                             'volume': self.parameters['flexvol_name'],
                             'qtree': name})
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        qtree_list_iter.add_child_elem(query)
        result = self.server.invoke_successfully(qtree_list_iter,
                                                 enable_tunneling=True)
        return_q = None
        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return_q = {'export_policy': result['attributes-list']['qtree-info']['export-policy'],
                        'unix_permissions': result['attributes-list']['qtree-info']['mode'],
                        'oplocks': result['attributes-list']['qtree-info']['oplocks'],
                        'security_style': result['attributes-list']['qtree-info']['security-style']}

        return return_q

    def create_qtree(self):
        """
        Create a qtree
        """
        options = {'qtree': self.parameters['name'], 'volume': self.parameters['flexvol_name']}
        if self.parameters.get('export_policy'):
            options['export-policy'] = self.parameters['export_policy']
        if self.parameters.get('security_style'):
            options['security-style'] = self.parameters['security_style']
        if self.parameters.get('oplocks'):
            options['oplocks'] = self.parameters['oplocks']
        if self.parameters.get('unix_permissions'):
            options['mode'] = self.parameters['unix_permissions']
        qtree_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-create', **options)
        try:
            self.server.invoke_successfully(qtree_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error provisioning qtree %s: %s"
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_qtree(self):
        """
        Delete a qtree
        """
        path = '/vol/%s/%s' % (self.parameters['flexvol_name'], self.parameters['name'])
        qtree_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-delete', **{'qtree': path})

        try:
            self.server.invoke_successfully(qtree_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error deleting qtree %s: %s" % (path, to_native(error)),
                                  exception=traceback.format_exc())

    def rename_qtree(self):
        """
        Rename a qtree
        """
        path = '/vol/%s/%s' % (self.parameters['flexvol_name'], self.parameters['from_name'])
        new_path = '/vol/%s/%s' % (self.parameters['flexvol_name'], self.parameters['name'])
        qtree_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-rename', **{'qtree': path,
                               'new-qtree-name': new_path})

        try:
            self.server.invoke_successfully(qtree_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error renaming qtree %s: %s"
                                  % (self.parameters['from_name'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_qtree(self):
        """
        Modify a qtree
        """
        options = {'qtree': self.parameters['name'], 'volume': self.parameters['flexvol_name']}
        if self.parameters.get('export_policy'):
            options['export-policy'] = self.parameters['export_policy']
        if self.parameters.get('security_style'):
            options['security-style'] = self.parameters['security_style']
        if self.parameters.get('oplocks'):
            options['oplocks'] = self.parameters['oplocks']
        if self.parameters.get('unix_permissions'):
            options['mode'] = self.parameters['unix_permissions']
        qtree_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'qtree-modify', **options)
        try:
            self.server.invoke_successfully(qtree_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying qtree %s: %s'
                                  % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        '''Call create/delete/modify/rename operations'''
        netapp_utils.ems_log_event("na_ontap_qtree", self.server)
        current = self.get_qtree()
        rename, cd_action, modify = None, None, None
        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_qtree(self.parameters['from_name']), current)
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action is None and self.parameters['state'] == 'present':
            modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_qtree()
                if cd_action == 'create':
                    self.create_qtree()
                elif cd_action == 'delete':
                    self.delete_qtree()
                elif modify:
                    self.modify_qtree()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    '''Apply qtree operations from playbook'''
    qtree_obj = NetAppOntapQTree()
    qtree_obj.apply()


if __name__ == '__main__':
    main()
