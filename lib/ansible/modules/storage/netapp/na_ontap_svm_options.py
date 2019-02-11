#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
short_description: NetApp ONTAP Modify SVM Options
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Modify ONTAP SVM Options
  - Only Options that appear on "vserver options show" can be set
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_svm_options
version_added: "2.7"
options:
  name:
    description:
      - Name of the option.
  value:
    description:
      - Value of the option.
      - Value must be in quote
  vserver:
    description:
      - The name of the vserver to which this option belongs to.
    required: True
'''

EXAMPLES = """
    - name: Set SVM Options
      na_ontap_svm_options:
        vserver: "{{ netapp_vserver_name }}"
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
        name: snmp.enable
        value: 'on'
"""

RETURN = """
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPSvnOptions(object):

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            name=dict(required=False, type="str", default=None),
            value=dict(required=False, type='str', default=None),
            vserver=dict(required=True, type='str')

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
        return

    def set_options(self):
        """
        Set a specific option
        :return: None
        """
        option_obj = netapp_utils.zapi.NaElement("options-set")
        option_obj.add_new_child('name', self.parameters['name'])
        option_obj.add_new_child('value', self.parameters['value'])
        try:
            result = self.server.invoke_successfully(option_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error setting options: %s" % to_native(error), exception=traceback.format_exc())

    def list_options(self):
        """
        List all Options on the Vserver
        :return: None
        """
        option_obj = netapp_utils.zapi.NaElement("options-list-info")
        try:
            result = self.server.invoke_successfully(option_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error getting options: %s" % to_native(error), exception=traceback.format_exc())

    def is_option_set(self):
        """
        Checks to see if an option is set or not
        :return: If option is set return True, else return False
        """
        option_obj = netapp_utils.zapi.NaElement("options-get-iter")
        options_info = netapp_utils.zapi.NaElement("option-info")
        if self.parameters.get('name') is not None:
            options_info.add_new_child("name", self.parameters['name'])
        if self.parameters.get('value') is not None:
            options_info.add_new_child("value", self.parameters['value'])
        if "vserver" in self.parameters.keys():
            if self.parameters['vserver'] is not None:
                options_info.add_new_child("vserver", self.parameters['vserver'])
        query = netapp_utils.zapi.NaElement("query")
        query.add_child_elem(options_info)
        option_obj.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(option_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error finding option: %s" % to_native(error), exception=traceback.format_exc())

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
            return True
        return False

    def apply(self):
        changed = False
        netapp_utils.ems_log_event("na_ontap_svm_options", self.server)
        is_set = self.is_option_set()
        if not is_set:
            self.set_options()
            changed = True
        self.module.exit_json(changed=changed)


def main():
    """
    Execute action from playbook
    :return: none
    """
    cg_obj = NetAppONTAPSvnOptions()
    cg_obj.apply()


if __name__ == '__main__':
    main()
