#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'certified'
}

DOCUMENTATION = '''
---

module: na_ontap_ucadapter
short_description: NetApp ONTAP UC adapter configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - modify the UC adapter mode and type taking pending type and mode into account.

options:
  state:
    description:
    - Whether the specified adapter should exist.
    required: false
    choices: ['present']
    default: 'present'

  adapter_name:
    description:
    - Specifies the adapter name.
    required: true

  node_name:
    description:
    - Specifies the adapter home node.
    required: true

  mode:
    description:
    - Specifies the mode of the adapter.

  type:
    description:
    - Specifies the fc4 type of the adapter.

'''

EXAMPLES = '''
    - name: Modify adapter
      na_ontap_adapter:
        state: present
        adapter_name: data2
        node_name: laurentn-vsim1
        mode: fc
        type: target
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


class NetAppOntapadapter(object):
    ''' object to describe  adapter info '''

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present'], default='present'),
            adapter_name=dict(required=True, type='str'),
            node_name=dict(required=True, type='str'),
            mode=dict(required=False, type='str'),
            type=dict(required=False, type='str'),
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
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_adapter(self):
        """
        Return details about the adapter
        :param:
            name : Name of the name of the adapter

        :return: Details about the adapter. None if not found.
        :rtype: dict
        """
        adapter_info = netapp_utils.zapi.NaElement('ucm-adapter-get')
        adapter_info.add_new_child('adapter-name', self.parameters['adapter_name'])
        adapter_info.add_new_child('node-name', self.parameters['node_name'])
        try:
            result = self.server.invoke_successfully(adapter_info, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching ucadapter details: %s: %s'
                                      % (self.parameters['node_name'], to_native(error)),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('attributes'):
            adapter_attributes = result.get_child_by_name('attributes').\
                get_child_by_name('uc-adapter-info')
            return_value = {
                'mode': adapter_attributes.get_child_content('mode'),
                'pending-mode': adapter_attributes.get_child_content('pending-mode'),
                'type': adapter_attributes.get_child_content('fc4-type'),
                'pending-type': adapter_attributes.get_child_content('pending-fc4-type'),
                'status': adapter_attributes.get_child_content('status'),
            }
            return return_value
        return None

    def modify_adapter(self):
        """
        Modify the adapter.
        """
        params = {'adapter-name': self.parameters['adapter_name'],
                  'node-name': self.parameters['node_name']}
        if self.parameters['type'] is not None:
            params['fc4-type'] = self.parameters['type']
        if self.parameters['mode'] is not None:
            params['mode'] = self.parameters['mode']
        adapter_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'ucm-adapter-modify', ** params)
        try:
            self.server.invoke_successfully(adapter_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying adapter %s: %s' % (self.parameters['adapter_name'], to_native(e)),
                                  exception=traceback.format_exc())

    def online_or_offline_adapter(self, status):
        """
        Bring a Fibre Channel target adapter offline/online.
        """
        if status == 'down':
            adapter = netapp_utils.zapi.NaElement('fcp-adapter-config-down')
        elif status == 'up':
            adapter = netapp_utils.zapi.NaElement('fcp-adapter-config-up')
        adapter.add_new_child('fcp-adapter', self.parameters['adapter_name'])
        adapter.add_new_child('node', self.parameters['node_name'])
        try:
            self.server.invoke_successfully(adapter,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error trying to %s fc-adapter %s: %s' % (status, self.parameters['adapter_name'], to_native(e)),
                                  exception=traceback.format_exc())

    def autosupport_log(self):
        """
        Autosupport log for ucadater
        :return:
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_ucadapter", cserver)

    def apply(self):
        ''' calling all adapter features '''
        changed = False
        adapter_detail = self.get_adapter()

        def need_to_change(expected, pending, current):
            if expected is None:
                return False
            elif pending is not None:
                return pending != expected
            elif current is not None:
                return current != expected
            return False

        if adapter_detail:
            changed = need_to_change(self.parameters.get('type'), adapter_detail['pending-type'],
                                     adapter_detail['type']) or need_to_change(self.parameters.get('mode'),
                                                                               adapter_detail['pending-mode'],
                                                                               adapter_detail['mode'])

        if changed:
            if self.module.check_mode:
                pass
            else:
                self.online_or_offline_adapter('down')
                self.modify_adapter()
                self.online_or_offline_adapter('up')

        self.module.exit_json(changed=changed)


def main():
    adapter = NetAppOntapadapter()
    adapter.apply()


if __name__ == '__main__':
    main()
