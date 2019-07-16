#!/usr/bin/python
''' This is an Ansible module for ONTAP, to manage initiators in an Igroup

 (c) 2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''

module: na_ontap_igroup_initiator
short_description: NetApp ONTAP igroup initiator configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Add/Remove initiators from an igroup

options:
  state:
    description:
    - Whether the specified initiator should exist or not in an igroup.
    choices: ['present', 'absent']
    default: present

  names:
    description:
    - List of initiators to manage.
    required: true
    aliases:
    - name

  initiator_group:
    description:
    - Name of the initiator group to which the initiator belongs.
    required: true

  vserver:
    description:
    - The name of the vserver to use.
    required: true

'''

EXAMPLES = '''
    - name: Add initiators to an igroup
      na_ontap_igroup_initiator:
        names: abc.test:def.com,def.test:efg.com
        initiator_group: test_group
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Remove an initiator from an igroup
      na_ontap_igroup_initiator:
        state: absent
        names: abc.test:def.com
        initiator_group: test_group
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


class NetAppOntapIgroupInitiator(object):

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            names=dict(required=True, type='list', aliases=['name']),
            initiator_group=dict(required=True, type='str'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_initiators(self):
        """
        Get the existing list of initiators from an igroup
        :rtype: list() or None
        """
        igroup_info = netapp_utils.zapi.NaElement('igroup-get-iter')
        attributes = dict(query={'initiator-group-info': {'initiator-group-name': self.parameters['initiator_group']}})
        igroup_info.translate_struct(attributes)
        result, current = None, []

        try:
            result = self.server.invoke_successfully(igroup_info, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching igroup info %s: %s' % (self.parameters['initiator_group'],
                                                                             to_native(error)),
                                  exception=traceback.format_exc())

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            igroup_info = result.get_child_by_name('attributes-list').get_child_by_name('initiator-group-info')
            if igroup_info.get_child_by_name('initiators') is not None:
                current = [initiator['initiator-name'] for initiator in igroup_info['initiators'].get_children()]
        return current

    def modify_initiator(self, initiator_name, zapi):
        """
        Add or remove an initiator to/from an igroup
        """
        options = {'initiator-group-name': self.parameters['initiator_group'],
                   'initiator': initiator_name}
        initiator_modify = netapp_utils.zapi.NaElement.create_node_with_children(zapi, **options)

        try:
            self.server.invoke_successfully(initiator_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying igroup initiator %s: %s' % (initiator_name,
                                                                                   to_native(error)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        netapp_utils.ems_log_event("na_ontap_igroup_initiator", self.server)

    def apply(self):
        self.autosupport_log()
        initiators, present = self.get_initiators(), None
        for initiator in self.parameters['names']:
            if initiator in initiators:
                present = True
            cd_action = self.na_helper.get_cd_action(present, self.parameters)
            if self.na_helper.changed:
                if self.module.check_mode:
                    pass
                else:
                    if cd_action == 'create':
                        self.modify_initiator(initiator, 'igroup-add')
                    elif cd_action == 'delete':
                        self.modify_initiator(initiator, 'igroup-remove')
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    obj = NetAppOntapIgroupInitiator()
    obj.apply()


if __name__ == '__main__':
    main()
