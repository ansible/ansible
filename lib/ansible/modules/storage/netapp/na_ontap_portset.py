#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
short_description: NetApp ONTAP Create/Delete portset
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Create/Delete ONTAP portset.
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_portset
options:
  state:
    description:
      - If you want to create a portset.
    default: present
  vserver:
    required: true
    description:
      - Name of the SVM.
  name:
    required: true
    description:
      - Name of the port set to create.
  type:
    required: true
    description:
      - Protocols accepted for this portset.
    choices: ['fcp', 'iscsi', 'mixed']
  force:
    description:
      - If 'false' or not specified, the request will fail if there are any igroups bound to this portset.
      - If 'true', forcibly destroy the portset, even if there are existing igroup bindings.
    type: bool
    default: False
version_added: "2.8"

'''

EXAMPLES = """
    - name: Create Portset
      na_ontap_portset:
        state: present
        vserver: vserver_name
        name: portset_name
        type: "{{ protocol type }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"

    - name: Delete Portset
      na_ontap_portset:
        state: absent
        vserver: ansible_test
        name: test
        force: True
        type: "{{ protocol type }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"
"""

RETURN = """
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPPortset(object):
    """
    Methods to create or delete portset
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, default='present'),
            vserver=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            type=dict(required=True, type='str', choices=[
                'fcp', 'iscsi', 'mixed']),
            force=dict(required=False, type='bool', default=False)
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
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.parameters['vserver'])

    def portset_get_iter(self):
        """
        Compose NaElement object to query current portset using vserver, portset-name and portset-type parameters
        :return: NaElement object for portset-get-iter with query
        """
        portset_get = netapp_utils.zapi.NaElement('portset-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        portset_info = netapp_utils.zapi.NaElement('portset-info')
        portset_info.add_new_child('vserver', self.parameters['vserver'])
        portset_info.add_new_child('portset-name', self.parameters['name'])
        portset_info.add_new_child('portset-type', self.parameters['type'])
        query.add_child_elem(portset_info)
        portset_get.add_child_elem(query)
        return portset_get

    def portset_get(self):
        """
        Get current portset info
        :return: Dictionary of current portset details if query successful, else return None
        """
        portset_get_iter = self.portset_get_iter()
        portset_info = dict()
        try:
            result = self.server.invoke_successfully(portset_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching portset %s: %s'
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())
        # return portset details
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) > 0:
            porset_get_info = result.get_child_by_name('attributes-list').get_child_by_name('portset-info')
            portset_info['vserver'] = porset_get_info.get_child_content('vserver')
            portset_info['portset_name'] = porset_get_info.get_child_content('portset-name')
            portset_info['portset_type'] = porset_get_info.get_child_content('portset-type')
            return portset_info
        return None

    def create_portset(self):
        """
        Create a portset
        """
        portset_info = netapp_utils.zapi.NaElement("portset-create")
        portset_info.add_new_child("portset-name", self.parameters['name'])
        portset_info.add_new_child("portset-type", self.parameters['type'])
        try:
            self.server.invoke_successfully(
                portset_info, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error creating portset %s: %s" %
                                      (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_portset(self):
        """
        Delete a portset
        """
        portset_info = netapp_utils.zapi.NaElement("portset-destroy")
        portset_info.add_new_child("portset-name", self.parameters['name'])
        if self.parameters.get('force'):
            portset_info.add_new_child("force", str(self.parameters['force']))
        try:
            self.server.invoke_successfully(
                portset_info, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error deleting portset %s: %s" %
                                      (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Applies action from playbook
        """
        netapp_utils.ems_log_event("na_ontap_autosupport", self.server)
        current = self.portset_get()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)
        if cd_action == 'create':
            self.create_portset()
        elif cd_action == 'delete':
            self.delete_portset()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Execute action from playbook
    """
    portset_obj = NetAppONTAPPortset()
    portset_obj.apply()


if __name__ == '__main__':
    main()
