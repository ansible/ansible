#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---

module: na_ontap_ucadapter
short_description: ONTAP UC adapter configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: chhaya gunawat (chhayag@netapp.com)

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

        params = self.module.params

        # set up state variables
        self.state = params['state']
        self.adapter_name = params['adapter_name']
        self.node_name = params['node_name']
        self.mode = params['mode']
        self.type = params['type']

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
        adapter_info.add_new_child('adapter-name', self.adapter_name)
        adapter_info.add_new_child('node-name', self.node_name)
        result = self.server.invoke_successfully(adapter_info, True)
        return_value = None
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

    def modify_adapter(self):
        """
        Modify the adapter.
        """
        params = {'adapter-name': self.adapter_name,
                  'node-name': self.node_name}
        if self.type is not None:
            params['fc4-type'] = self.type
        if self.mode is not None:
            params['mode'] = self.mode
        adapter_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'ucm-adapter-modify', ** params)
        try:
            self.server.invoke_successfully(adapter_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying adapter %s: %s' % (self.adapter_name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        ''' calling all adapter features '''
        changed = False
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_ucadapter", cserver)
        adapter_detail = self.get_adapter()

        def need_to_change(expected, pending, current):
            if expected is None:
                return False
            if pending is not None:
                return pending != expected
            if current is not None:
                return current != expected
            return False

        if adapter_detail:
            changed = need_to_change(self.type, adapter_detail['pending-type'], adapter_detail['type']) or \
                need_to_change(self.mode, adapter_detail['pending-mode'], adapter_detail['mode'])

        if changed:
            if self.module.check_mode:
                pass
            else:
                self.modify_adapter()

        self.module.exit_json(changed=changed)


def main():
    adapter = NetAppOntapadapter()
    adapter.apply()


if __name__ == '__main__':
    main()
