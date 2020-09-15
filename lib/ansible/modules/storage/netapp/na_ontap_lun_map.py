#!/usr/bin/python

""" this is lun mapping module

 (c) 2018-2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = """

module: na_ontap_lun_map

short_description: NetApp ONTAP LUN maps
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Map and unmap LUNs on NetApp ONTAP.

options:

  state:
    description:
    - Whether the specified LUN should exist or not.
    choices: ['present', 'absent']
    default: present

  initiator_group_name:
    description:
    - Initiator group to map to the given LUN.
    required: true

  path:
    description:
    - Path of the LUN..
    required: true

  vserver:
    required: true
    description:
    - The name of the vserver to use.

  lun_id:
    description:
    - LUN ID assigned for the map.


"""

EXAMPLES = """
- name: Create LUN mapping
  na_ontap_lun_map:
    state: present
    initiator_group_name: ansibleIgroup3234
    path: /vol/iscsi_path/iscsi_lun
    vserver: ci_dev
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Unmap LUN
  na_ontap_lun_map:
    state: absent
    initiator_group_name: ansibleIgroup3234
    path: /vol/iscsi_path/iscsi_lun
    vserver: ci_dev
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"
"""

RETURN = """
lun_node:
    description: NetApp controller that is hosting the LUN.
    returned: success
    type: str
    sample: node01
lun_ostype:
    description: Specifies the OS of the host accessing the LUN.
    returned: success
    type: str
    sample: vmware
lun_serial:
    description: A unique, 12-byte, ASCII string used to identify the LUN.
    returned: success
    type: str
    sample: 80E7/]LZp1Tt
lun_naa_id:
    description: The Network Address Authority (NAA) identifier for the LUN.
    returned: success
    type: str
    sample: 600a0980383045372f5d4c5a70315474
lun_state:
    description: Online or offline status of the LUN.
    returned: success
    type: str
    sample: online
lun_size:
    description: Size of the LUN in bytes.
    returned: success
    type: int
    sample: 2199023255552
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
import codecs
from ansible.module_utils._text import to_text, to_bytes

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapLUNMap(object):

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            initiator_group_name=dict(required=True, type='str'),
            path=dict(required=True, type='str'),
            vserver=dict(required=True, type='str'),
            lun_id=dict(required=False, type='str', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['path'])
            ],
            supports_check_mode=True
        )

        self.result = dict(
            changed=False,
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.initiator_group_name = p['initiator_group_name']
        self.path = p['path']
        self.vserver = p['vserver']
        self.lun_id = p['lun_id']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_lun_map(self):
        """
        Return details about the LUN map

        :return: Details about the lun map
        :rtype: dict
        """
        lun_info = netapp_utils.zapi.NaElement('lun-map-list-info')
        lun_info.add_new_child('path', self.path)
        result = self.server.invoke_successfully(lun_info, True)
        return_value = None
        igroups = result.get_child_by_name('initiator-groups')
        if igroups:
            for igroup_info in igroups.get_children():
                initiator_group_name = igroup_info.get_child_content('initiator-group-name')
                lun_id = igroup_info.get_child_content('lun-id')
                if initiator_group_name == self.initiator_group_name:
                    return_value = {
                        'lun_id': lun_id
                    }
                    break

        return return_value

    def get_lun(self):
        """
        Return details about the LUN

        :return: Details about the lun
        :rtype: dict
        """
        # build the lun query
        query_details = netapp_utils.zapi.NaElement('lun-info')
        query_details.add_new_child('path', self.path)

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)

        lun_query = netapp_utils.zapi.NaElement('lun-get-iter')
        lun_query.add_child_elem(query)

        # find lun using query
        result = self.server.invoke_successfully(lun_query, True)
        return_value = None
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            lun = result.get_child_by_name('attributes-list').get_child_by_name('lun-info')

            # extract and assign lun information to return value
            hexlify = codecs.getencoder('hex')
            naa_hex = to_text(hexlify(to_bytes(lun.get_child_content('serial-number')))[0])
            return_value = {
                'lun_node': lun.get_child_content('node'),
                'lun_ostype': lun.get_child_content('multiprotocol-type'),
                'lun_serial': lun.get_child_content('serial-number'),
                'lun_naa_id': '600a0980' + naa_hex,
                'lun_state': lun.get_child_content('state'),
                'lun_size': lun.get_child_content('size'),
            }

        return return_value

    def create_lun_map(self):
        """
        Create LUN map
        """
        options = {'path': self.path, 'initiator-group': self.initiator_group_name}
        if self.lun_id is not None:
            options['lun-id'] = self.lun_id
        lun_map_create = netapp_utils.zapi.NaElement.create_node_with_children('lun-map', **options)

        try:
            self.server.invoke_successfully(lun_map_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error mapping lun %s of initiator_group_name %s: %s" %
                                  (self.path, self.initiator_group_name, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_lun_map(self):
        """
        Unmap LUN map
        """
        lun_map_delete = netapp_utils.zapi.NaElement.create_node_with_children('lun-unmap', **{'path': self.path, 'initiator-group': self.initiator_group_name})

        try:
            self.server.invoke_successfully(lun_map_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error unmapping lun %s of initiator_group_name %s: %s" %
                                  (self.path, self.initiator_group_name, to_native(e)),
                                  exception=traceback.format_exc())

    def apply(self):
        netapp_utils.ems_log_event("na_ontap_lun_map", self.server)
        lun_details = self.get_lun()
        lun_map_details = self.get_lun_map()

        if self.state == 'present' and lun_details:
            self.result.update(lun_details)

        if self.state == 'present' and not lun_map_details:
            self.result['changed'] = True
            if not self.module.check_mode:
                self.create_lun_map()
        elif self.state == 'absent' and lun_map_details:
            self.result['changed'] = True
            if not self.module.check_mode:
                self.delete_lun_map()

        self.module.exit_json(**self.result)


def main():
    v = NetAppOntapLUNMap()
    v.apply()


if __name__ == '__main__':
    main()
