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
  - Create/Delete NVMe Service
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_nvme
options:
  state:
    choices: ['present', 'absent']
    description:
      - Whether the specified NVMe should exist or not.
    default: present
  vserver:
    description:
      - Name of the vserver to use.
    required: true
  status_admin:
    description:
      - Whether the status of NVMe should be up or down
    type: bool
short_description: "NetApp ONTAP Manage NVMe Service"
version_added: "2.8"
'''

EXAMPLES = """

    - name: Create NVMe
      na_ontap_nvme:
        state: present
        status_admin: False
        vserver: "{{ vserver }}"
        hostname: "{{ hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"

    - name: Modify NVMe
      na_ontap_nvme:
        state: present
        status_admin: True
        vserver: "{{ vserver }}"
        hostname: "{{ hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"

    - name: Delete NVMe
      na_ontap_nvme:
        state: absent
        vserver: "{{ vserver }}"
        hostname: "{{ hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPNVMe(object):
    """
    Class with NVMe service methods
    """

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            vserver=dict(required=True, type='str'),
            status_admin=dict(required=False, type='bool')
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

    def get_nvme(self):
        """
        Get current nvme details
        :return: dict if nvme exists, None otherwise
        """
        nvme_get = netapp_utils.zapi.NaElement('nvme-get-iter')
        query = {
            'query': {
                'nvme-target-service-info': {
                    'vserver': self.parameters['vserver']
                }
            }
        }
        nvme_get.translate_struct(query)
        try:
            result = self.server.invoke_successfully(nvme_get, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching nvme info: %s' % to_native(error),
                                  exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            attributes_list = result.get_child_by_name('attributes-list')
            nvme_info = attributes_list.get_child_by_name('nvme-target-service-info')
            return_value = {'status_admin': nvme_info.get_child_content('is-available')}
            return return_value
        return None

    def create_nvme(self):
        """
        Create NVMe service
        """
        nvme_create = netapp_utils.zapi.NaElement('nvme-create')
        if self.parameters.get('status_admin') is not None:
            options = {'is-available': self.parameters['status_admin']}
            nvme_create.translate_struct(options)
        try:
            self.server.invoke_successfully(nvme_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating nvme for vserver %s: %s'
                                  % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_nvme(self):
        """
        Delete NVMe service
        """
        nvme_delete = netapp_utils.zapi.NaElement('nvme-delete')
        try:
            self.server.invoke_successfully(nvme_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting nvme for vserver %s: %s'
                                  % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def modify_nvme(self, status=None):
        """
        Modify NVMe service
        """
        if status is None:
            status = self.parameters['status_admin']
        options = {'is-available': status}
        nvme_modify = netapp_utils.zapi.NaElement('nvme-modify')
        nvme_modify.translate_struct(options)
        try:
            self.server.invoke_successfully(nvme_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying nvme for vserver %s: %s'
                                  % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Apply action to NVMe service
        """
        netapp_utils.ems_log_event("na_ontap_nvme", self.server)
        current = self.get_nvme()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if self.parameters.get('status_admin') is not None:
            self.parameters['status_admin'] = self.na_helper.get_value_for_bool(False, self.parameters['status_admin'])
            if cd_action is None and self.parameters['state'] == 'present':
                modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_nvme()
                elif cd_action == 'delete':
                    # NVMe status_admin needs to be down before deleting it
                    self.modify_nvme('false')
                    self.delete_nvme()
                elif modify:
                    self.modify_nvme()

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    community_obj = NetAppONTAPNVMe()
    community_obj.apply()


if __name__ == '__main__':
    main()
