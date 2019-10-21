#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Create/Delete NVME subsystem
  - Associate(modify) host/map to NVME subsystem
  - NVMe service should be existing in the data vserver with NVMe protocol as a pre-requisite
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_nvme_subsystem
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified subsystem should exist or not.
    default: present
  vserver:
    description:
      - Name of the vserver to use.
    required: true
  subsystem:
    description:
      - Specifies the subsystem
    required: true
  ostype:
    description:
      - Specifies the ostype for initiators
    choices: ['windows', 'linux', 'vmware', 'xen', 'hyper_v']
  skip_host_check:
    description:
      - Skip host check
      - Required to delete an NVMe Subsystem with attached NVMe namespaces
    default: false
    type: bool
  skip_mapped_check:
    description:
      - Skip mapped namespace check
      - Required to delete an NVMe Subsystem with attached NVMe namespaces
    default: false
    type: bool
  hosts:
    description:
      - List of host NQNs (NVMe Qualification Name) associated to the controller.
    type: list
  paths:
    description:
      - List of Namespace paths to be associated with the subsystem.
    type: list
short_description: "NetApp ONTAP Manage NVME Subsystem"
version_added: "2.8"
'''

EXAMPLES = """

    - name: Create NVME Subsystem
      na_ontap_nvme_subsystem:
        state: present
        subsystem: test_sub
        vserver: test_dest
        ostype: linux
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete NVME Subsystem
      na_ontap_nvme_subsystem:
        state: absent
        subsystem: test_sub
        vserver: test_dest
        skip_host_check: True
        skip_mapped_check: True
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Associate NVME Subsystem host/map
      na_ontap_nvme_subsystem:
        state: present
        subsystem: "{{ subsystem }}"
        ostype: linux
        hosts: nqn.1992-08.com.netapp:sn.3017cfc1e2ba11e89c55005056b36338:subsystem.ansible
        paths: /vol/ansible/test,/vol/ansible/test1
        vserver: "{{ vserver }}"
        hostname: "{{ hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"

    - name: Modify NVME subsystem map
      na_ontap_nvme_subsystem:
        state: present
        subsystem: test_sub
        vserver: test_dest
        skip_host_check: True
        skip_mapped_check: True
        paths: /vol/ansible/test
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


class NetAppONTAPNVMESubsystem(object):
    """
    Class with NVME subsytem methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            subsystem=dict(required=True, type='str'),
            ostype=dict(required=False, type='str', choices=['windows', 'linux', 'vmware', 'xen', 'hyper_v']),
            skip_host_check=dict(required=False, type='bool', default=False),
            skip_mapped_check=dict(required=False, type='bool', default=False),
            hosts=dict(required=False, type='list'),
            paths=dict(required=False, type='list')
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

    def get_subsystem(self):
        """
        Get current subsystem details
        :return: dict if subsystem exists, None otherwise
        """
        subsystem_get = netapp_utils.zapi.NaElement('nvme-subsystem-get-iter')
        query = {
            'query': {
                'nvme-subsytem-info': {
                    'subsystem': self.parameters.get('subsystem')
                }
            }
        }
        subsystem_get.translate_struct(query)
        try:
            result = self.server.invoke_successfully(subsystem_get, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching subsystem info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            return True
        return None

    def create_subsystem(self):
        """
        Create a NVME Subsystem
        """
        if self.parameters.get('ostype') is None:
            self.module.fail_json(msg="Error: Missing required parameter 'os_type' for creating subsystem")
        options = {'subsystem': self.parameters['subsystem'],
                   'ostype': self.parameters['ostype']
                   }
        subsystem_create = netapp_utils.zapi.NaElement('nvme-subsystem-create')
        subsystem_create.translate_struct(options)
        try:
            self.server.invoke_successfully(subsystem_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating subsystem for %s: %s'
                                  % (self.parameters.get('subsystem'), to_native(error)),
                                  exception=traceback.format_exc())

    def delete_subsystem(self):
        """
        Delete a NVME subsystem
        """
        options = {'subsystem': self.parameters['subsystem'],
                   'skip-host-check': 'true' if self.parameters.get('skip_host_check') else 'false',
                   'skip-mapped-check': 'true' if self.parameters.get('skip_mapped_check') else 'false',
                   }
        subsystem_delete = netapp_utils.zapi.NaElement.create_node_with_children('nvme-subsystem-delete', **options)
        try:
            self.server.invoke_successfully(subsystem_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting subsystem for %s: %s'
                                      % (self.parameters.get('subsystem'), to_native(error)),
                                  exception=traceback.format_exc())

    def get_subsystem_host_map(self, type):
        """
        Get current subsystem host details
        :return: list if host exists, None otherwise
        """
        if type == 'hosts':
            zapi_get, zapi_info, zapi_type = 'nvme-subsystem-host-get-iter', 'nvme-target-subsystem-host-info',\
                                             'host-nqn'
        elif type == 'paths':
            zapi_get, zapi_info, zapi_type = 'nvme-subsystem-map-get-iter', 'nvme-target-subsystem-map-info', 'path'
        subsystem_get = netapp_utils.zapi.NaElement(zapi_get)
        query = {
            'query': {
                zapi_info: {
                    'subsystem': self.parameters.get('subsystem')
                }
            }
        }
        subsystem_get.translate_struct(query)
        try:
            result = self.server.invoke_successfully(subsystem_get, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching subsystem info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            attrs_list = result.get_child_by_name('attributes-list')
            return_list = []
            for item in attrs_list.get_children():
                return_list.append(item[zapi_type])
            return {type: return_list}
        return None

    def add_subsystem_host_map(self, data, type):
        """
        Add a NVME Subsystem host/map
        :param: data: list of hosts/paths to be added
        :param: type: hosts/paths
        """
        if type == 'hosts':
            zapi_add, zapi_type = 'nvme-subsystem-host-add', 'host-nqn'
        elif type == 'paths':
            zapi_add, zapi_type = 'nvme-subsystem-map-add', 'path'

        for item in data:
            options = {'subsystem': self.parameters['subsystem'],
                       zapi_type: item
                       }
            subsystem_add = netapp_utils.zapi.NaElement.create_node_with_children(zapi_add, **options)
            try:
                self.server.invoke_successfully(subsystem_add, enable_tunneling=True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error adding %s for subsystem %s: %s'
                                      % (item, self.parameters.get('subsystem'), to_native(error)),
                                      exception=traceback.format_exc())

    def remove_subsystem_host_map(self, data, type):
        """
        Remove a NVME Subsystem host/map
        :param: data: list of hosts/paths to be added
        :param: type: hosts/paths
        """
        if type == 'hosts':
            zapi_remove, zapi_type = 'nvme-subsystem-host-remove', 'host-nqn'
        elif type == 'paths':
            zapi_remove, zapi_type = 'nvme-subsystem-map-remove', 'path'

        for item in data:
            options = {'subsystem': self.parameters['subsystem'],
                       zapi_type: item
                       }
            subsystem_remove = netapp_utils.zapi.NaElement.create_node_with_children(zapi_remove, **options)
            try:
                self.server.invoke_successfully(subsystem_remove, enable_tunneling=True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error removing %s for subsystem %s: %s'
                                          % (item, self.parameters.get('subsystem'), to_native(error)),
                                      exception=traceback.format_exc())

    def associate_host_map(self, types):
        """
        Check if there are hosts or paths to be associated with the subsystem
        """
        action_add_dict = {}
        action_remove_dict = {}
        for type in types:
            if self.parameters.get(type):
                current = self.get_subsystem_host_map(type)
                if current:
                    add_items = self.na_helper.\
                        get_modified_attributes(current, self.parameters, get_list_diff=True).get(type)
                    remove_items = [item for item in current[type] if item not in self.parameters.get(type)]
                else:
                    add_items = self.parameters[type]
                    remove_items = {}
                if add_items:
                    action_add_dict[type] = add_items
                    self.na_helper.changed = True
                if remove_items:
                    action_remove_dict[type] = remove_items
                    self.na_helper.changed = True
        return action_add_dict, action_remove_dict

    def modify_host_map(self, add_host_map, remove_host_map):
        for type, data in add_host_map.items():
            self.add_subsystem_host_map(data, type)
        for type, data in remove_host_map.items():
            self.remove_subsystem_host_map(data, type)

    def apply(self):
        """
        Apply action to NVME subsystem
        """
        netapp_utils.ems_log_event("na_ontap_nvme_subsystem", self.server)
        types = ['hosts', 'paths']
        current = self.get_subsystem()
        add_host_map, remove_host_map = dict(), dict()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action != 'delete' and self.parameters['state'] == 'present':
            add_host_map, remove_host_map = self.associate_host_map(types)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_subsystem()
                    self.modify_host_map(add_host_map, remove_host_map)
                elif cd_action == 'delete':
                    self.delete_subsystem()
                elif cd_action is None:
                    self.modify_host_map(add_host_map, remove_host_map)

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    community_obj = NetAppONTAPNVMESubsystem()
    community_obj.apply()


if __name__ == '__main__':
    main()
