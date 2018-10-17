#!/usr/bin/python

""" this is lun mapping module

 (c) 2018, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """

module: na_ontap_lun_map

short_description: Manage NetApp Ontap lun maps
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: chhaya gunawat (chhayag@netapp.com)

description:
- Map and unmap luns on NetApp Ontap.

options:

  state:
    description:
    - Whether the specified lun should exist or not.
    choices: ['present', 'absent']
    default: present

  initiator_group_name:
    description:
    - Initiator group to map to the given LUN.
    required: true

  path:
    description:
    - Path of the LUN..
    - Required when C(state=present).

  vserver:
    required: true
    description:
    - The name of the vserver to use.

  lun_id:
    description:
    - LUN ID assigned for the map.


"""

EXAMPLES = """
- name: Create lun mapping
  na_ontap_lun_map:
    state: present
    initiator_group_name: ansibleIgroup3234
    path: /vol/iscsi_path/iscsi_lun
    vserver: ci_dev
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Unmap Lun
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

"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapLUNMap(object):

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            initiator_group_name=dict(required=True, type='str'),
            path=dict(type='str'),
            vserver=dict(required=True, type='str'),
            lun_id=dict(required=False, type='str', default=None)),
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['path'])
            ],
            supports_check_mode=True
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
        property_changed = False
        lun_map_exists = False
        netapp_utils.ems_log_event("na_ontap_lun_map", self.server)
        lun_map_detail = self.get_lun_map()

        if lun_map_detail:
            lun_map_exists = True

            if self.state == 'absent':
                property_changed = True

            elif self.state == 'present':
                pass

        else:
            if self.state == 'present':
                property_changed = True

        if property_changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    # TODO delete this line in next release
                    if not lun_map_exists:
                        self.create_lun_map()

                elif self.state == 'absent':
                    self.delete_lun_map()

        changed = property_changed
        # TODO: include other details about the lun (size, etc.)
        self.module.exit_json(changed=changed)


def main():
    v = NetAppOntapLUNMap()
    v.apply()


if __name__ == '__main__':
    main()
