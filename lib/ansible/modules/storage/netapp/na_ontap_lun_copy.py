#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_ontap_lun_copy

short_description: NetApp ONTAP copy LUNs
extends_documentation_fragment:
  - netapp.na_ontap
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Copy LUNs on NetApp ONTAP.

options:

  state:
    description:
    - Whether the specified LUN should exist or not.
    choices: ['present']
    default: present

  destination_vserver:
    description:
    - the name of the Vserver that will host the new LUN.
    required: true

  destination_path:
    description:
    - Specifies the full path to the new LUN.
    required: true

  source_path:
    description:
    - Specifies the full path to the source LUN.
    required: true

  source_vserver:
    description:
    - Specifies the name of the vserver hosting the LUN to be copied.

  '''
EXAMPLES = """
- name: Copy LUN
  na_ontap_lun_copy:
    destination_vserver: ansible
    destination_path: /vol/test/test_copy_dest_dest_new
    source_path: /vol/test/test_copy_1
    source_vserver: ansible
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
"""

RETURN = """

"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.netapp_module import NetAppModule
import ansible.module_utils.netapp as netapp_utils


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapLUNCopy(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present'], default='present'),
            destination_vserver=dict(required=True, type='str'),
            destination_path=dict(required=True, type='str'),
            source_path=dict(required=True, type='str'),
            source_vserver=dict(required=False, type='str'),

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
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['destination_vserver'])

    def get_lun(self):
        """
           Check if the LUN exists

        :return: true is it exists, false otherwise
        :rtype: bool
        """

        return_value = False
        lun_info = netapp_utils.zapi.NaElement('lun-get-iter')
        query_details = netapp_utils.zapi.NaElement('lun-info')

        query_details.add_new_child('path', self.parameters['destination_path'])
        query_details.add_new_child('vserver', self.parameters['destination_vserver'])

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)

        lun_info.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(lun_info, True)

        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error getting lun  info %s for  verver %s: %s" %
                                      (self.parameters['destination_path'], self.parameters['destination_vserver'], to_native(e)),
                                  exception=traceback.format_exc())

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            return_value = True
        return return_value

    def copy_lun(self):
        """
        Copy LUN with requested path and vserver
        """
        lun_copy = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-copy-start', **{'source-vserver': self.parameters['source_vserver']})

        path_obj = netapp_utils.zapi.NaElement('paths')
        pair = netapp_utils.zapi.NaElement('lun-path-pair')
        pair.add_new_child('destination-path', self.parameters['destination_path'])
        pair.add_new_child('source-path', self.parameters['source_path'])
        path_obj.add_child_elem(pair)
        lun_copy.add_child_elem(path_obj)

        try:
            self.server.invoke_successfully(lun_copy, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error copying lun from %s to  vserver %s: %s" %
                                      (self.parameters['source_vserver'], self.parameters['destination_vserver'], to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):

        netapp_utils.ems_log_event("na_ontap_lun_copy", self.server)
        if self.get_lun():  # lun already exists at destination
            changed = False
        else:
            changed = True
            if self.module.check_mode:
                pass
            else:
                # need to copy lun
                if self.parameters['state'] == 'present':
                    self.copy_lun()

        self.module.exit_json(changed=changed)


def main():
    v = NetAppOntapLUNCopy()
    v.apply()


if __name__ == '__main__':
    main()
