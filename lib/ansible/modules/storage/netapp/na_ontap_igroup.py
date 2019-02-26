#!/usr/bin/python
''' this is igroup module

 (c) 2018-2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'certified'
}

DOCUMENTATION = '''

module: na_ontap_igroup
short_description: NetApp ONTAP iSCSI or FC igroup configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Create/Delete/Rename Igroups and Modify initiators belonging to an igroup

options:
  state:
    description:
    - Whether the specified Igroup should exist or not.
    choices: ['present', 'absent']
    default: present

  name:
    description:
    - The name of the igroup to manage.
    required: true

  initiator_group_type:
    description:
    - Type of the initiator group.
    - Required when C(state=present).
    choices: ['fcp', 'iscsi', 'mixed']

  from_name:
    description:
    - Name of igroup to rename to name.
    version_added: '2.7'

  ostype:
    description:
    - OS type of the initiators within the group.

  initiators:
    description:
    - List of initiators to be mapped to the igroup.
    - WWPN, WWPN Alias, or iSCSI name of Initiator to add or remove.
    - For a modify operation, this list replaces the exisiting initiators
    - This module does not add or remove specific initiator(s) in an igroup
    aliases:
    - initiator

  bind_portset:
    description:
    - Name of a current portset to bind to the newly created igroup.

  force_remove_initiator:
    description:
    -  Forcibly remove the initiator even if there are existing LUNs mapped to this initiator group.
    type: bool

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = '''
    - name: Create iSCSI Igroup
      na_ontap_igroup:
        state: present
        name: ansibleIgroup3
        initiator_group_type: iscsi
        ostype: linux
        initiators: iqn.1994-05.com.redhat:scspa0395855001.rtp.openenglab.netapp.com,abc.com:redhat.com
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Create FC Igroup
      na_ontap_igroup:
        state: present
        name: ansibleIgroup4
        initiator_group_type: fcp
        ostype: linux
        initiators: 20:00:00:50:56:9f:19:82
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: rename Igroup
      na_ontap_igroup:
        state: present
        from_name: ansibleIgroup3
        name: testexamplenewname
        initiator_group_type: iscsi
        ostype: linux
        initiators: iqn.1994-05.com.redhat:scspa0395855001.rtp.openenglab.netapp.com
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Modify Igroup Initiators (replaces exisiting initiators)
      na_ontap_igroup:
        state: present
        name: ansibleIgroup3
        initiator_group_type: iscsi
        ostype: linux
        initiator: iqn.1994-05.com.redhat:scspa0395855001.rtp.openenglab.netapp.com
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete Igroup
      na_ontap_igroup:
        state: absent
        name: ansibleIgroup3
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
'''

RETURN = '''
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapIgroup(object):

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str', default=None),
            ostype=dict(required=False, type='str'),
            initiator_group_type=dict(required=False, type='str',
                                      choices=['fcp', 'iscsi', 'mixed']),
            initiators=dict(required=False, type='list', aliases=['initiator']),
            vserver=dict(required=True, type='str'),
            force_remove_initiator=dict(required=False, type='bool', default=False),
            bind_portset=dict(required=False, type='str')
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
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_igroup(self, name):
        """
        Return details about the igroup
        :param:
            name : Name of the igroup

        :return: Details about the igroup. None if not found.
        :rtype: dict
        """
        igroup_info = netapp_utils.zapi.NaElement('igroup-get-iter')
        attributes = dict(query={'initiator-group-info': {'initiator-group-name': name}})
        igroup_info.translate_struct(attributes)
        result, current = None, None

        try:
            result = self.server.invoke_successfully(igroup_info, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching igroup info %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            igroup = result.get_child_by_name('attributes-list').get_child_by_name('initiator-group-info')
            initiators = []
            if igroup.get_child_by_name('initiators'):
                current_initiators = igroup['initiators'].get_children()
                for initiator in current_initiators:
                    initiators.append(initiator['initiator-name'])
            current = {
                'initiators': initiators
            }

        return current

    def add_initiators(self):
        """
        Add the list of initiators to igroup
        :return: None
        """
        # don't add if initiators is empty string
        if self.parameters.get('initiators') == [''] or self.parameters.get('initiators') is None:
            return
        for initiator in self.parameters['initiators']:
            self.modify_initiator(initiator, 'igroup-add')

    def remove_initiators(self, initiators):
        """
        Removes all existing initiators from igroup
        :return: None
        """
        for initiator in initiators:
            self.modify_initiator(initiator, 'igroup-remove')

    def modify_initiator(self, initiator, zapi):
        """
        Add or remove an initiator to/from an igroup
        """
        initiator.strip()  # remove leading spaces if any (eg: if user types a space after comma in initiators list)
        options = {'initiator-group-name': self.parameters['name'],
                   'initiator': initiator}

        igroup_modify = netapp_utils.zapi.NaElement.create_node_with_children(zapi, **options)

        try:
            self.server.invoke_successfully(igroup_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying igroup initiator %s: %s' % (self.parameters['name'],
                                                                                   to_native(error)),
                                  exception=traceback.format_exc())

    def create_igroup(self):
        """
        Create the igroup.
        """
        options = {'initiator-group-name': self.parameters['name']}
        if self.parameters.get('ostype') is not None:
            options['os-type'] = self.parameters['ostype']
        if self.parameters.get('initiator_group_type') is not None:
            options['initiator-group-type'] = self.parameters['initiator_group_type']
        if self.parameters.get('bind_portset') is not None:
            options['bind-portset'] = self.parameters['bind_portset']

        igroup_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-create', **options)

        try:
            self.server.invoke_successfully(igroup_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error provisioning igroup %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        self.add_initiators()

    def delete_igroup(self):
        """
        Delete the igroup.
        """
        igroup_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-destroy', **{'initiator-group-name': self.parameters['name'],
                                 'force': 'true' if self.parameters['force_remove_initiator'] else 'false'})

        try:
            self.server.invoke_successfully(igroup_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting igroup %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def rename_igroup(self):
        """
        Rename the igroup.
        """
        igroup_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'igroup-rename', **{'initiator-group-name': self.parameters['from_name'],
                                'initiator-group-new-name': str(self.parameters['name'])})
        try:
            self.server.invoke_successfully(igroup_rename,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming igroup %s: %s' % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        netapp_utils.ems_log_event("na_ontap_igroup", self.server)

    def apply(self):
        self.autosupport_log()
        current = self.get_igroup(self.parameters['name'])
        # rename and create are mutually exclusive
        rename, cd_action, modify = None, None, None
        if self.parameters.get('from_name'):
            rename = self.na_helper.is_rename_action(self.get_igroup(self.parameters['from_name']), current)
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action is None and self.parameters['state'] == 'present':
            modify = self.na_helper.get_modified_attributes(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_igroup()
                elif cd_action == 'create':
                    self.create_igroup()
                elif cd_action == 'delete':
                    self.delete_igroup()
                if modify:
                    self.remove_initiators(current['initiators'])
                    self.add_initiators()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    obj = NetAppOntapIgroup()
    obj.apply()


if __name__ == '__main__':
    main()
