#!/usr/bin/python
"""
create Autosupport module to enable, disable or modify
"""

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - "Enable/Disable Autosupport"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_autosupport
options:
  state:
    description:
    - Specifies whether the AutoSupport daemon is present or absent.
    - When this setting is absent, delivery of all AutoSupport messages is turned off.
    choices: ['present', 'absent']
    default: present
  node_name:
    description:
    - The name of the filer that owns the AutoSupport Configuration.
    required: true
  transport:
    description:
    - The name of the transport protocol used to deliver AutoSupport messages
    choices: ['http', 'https', 'smtp']
  noteto:
    description:
    - Specifies up to five recipients of short AutoSupport e-mail messages.
  post_url:
    description:
    - The URL used to deliver AutoSupport messages via HTTP POST
  mail_hosts:
    description:
    - List of mail server(s) used to deliver AutoSupport messages via SMTP.
    - Both host names and IP addresses may be used as valid input.
  support:
    description:
    - Specifies whether AutoSupport notification to technical support is enabled.
    type: bool
  from_address:
    description:
    - specify the e-mail address from which the node sends AutoSupport messages
    version_added: 2.8
  partner_addresses:
    description:
    - Specifies up to five partner vendor recipients of full AutoSupport e-mail messages.
    version_added: 2.8
  to_addresses:
    description:
    - Specifies up to five recipients of full AutoSupport e-mail messages.
    version_added: 2.8
  proxy_url:
    description:
    - specify an HTTP or HTTPS proxy if the 'transport' parameter is set to HTTP or HTTPS and your organization uses a proxy
    version_added: 2.8
  hostname_in_subject:
    description:
    - Specify whether the hostname of the node is included in the subject line of the AutoSupport message.
    type: bool
    version_added: 2.8
short_description: NetApp ONTAP Autosupport
version_added: "2.7"

"""

EXAMPLES = """
    - name: Enable autosupport
      na_ontap_autosupport:
        hostname: "{{ hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"
        state: present
        node_name: test
        transport: https
        noteto: abc@def.com,def@ghi.com
        mail_hosts: 1.2.3.4,5.6.7.8
        support: False
        post_url: url/1.0/post

    - name: Disable autosupport
      na_ontap_autosupport:
        hostname: "{{ hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"
        state: absent
        node_name: test

"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPasup(object):
    """Class with autosupport methods"""

    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            node_name=dict(required=True, type='str'),
            transport=dict(required=False, type='str', choices=['smtp', 'http', 'https']),
            noteto=dict(required=False, type='list'),
            post_url=dict(reuired=False, type='str'),
            support=dict(required=False, type='bool'),
            mail_hosts=dict(required=False, type='list'),
            from_address=dict(required=False, type='str'),
            partner_addresses=dict(required=False, type='list'),
            to_addresses=dict(required=False, type='list'),
            proxy_url=dict(required=False, type='str'),
            hostname_in_subject=dict(required=False, type='bool'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # present or absent requires modifying state to enabled or disabled
        self.parameters['service_state'] = 'started' if self.parameters['state'] == 'present' else 'stopped'
        self.set_playbook_zapi_key_map()

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def set_playbook_zapi_key_map(self):
        self.na_helper.zapi_string_keys = {
            'node_name': 'node-name',
            'transport': 'transport',
            'post_url': 'post-url',
            'from_address': 'from',
            'proxy_url': 'proxy-url'
        }
        self.na_helper.zapi_list_keys = {
            'noteto': ('noteto', 'mail-address'),
            'mail_hosts': ('mail-hosts', 'string'),
            'partner_addresses': ('partner-address', 'mail-address'),
            'to_addresses': ('to', 'mail-address'),
        }
        self.na_helper.zapi_bool_keys = {
            'support': 'is-support-enabled',
            'hostname_in_subject': 'is-node-in-subject'
        }

    def get_autosupport_config(self):
        """
        Invoke zapi - get current autosupport details
        :return: dict()
        """
        asup_details = netapp_utils.zapi.NaElement('autosupport-config-get')
        asup_details.add_new_child('node-name', self.parameters['node_name'])
        asup_info = dict()
        try:
            result = self.server.invoke_successfully(asup_details, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='%s' % to_native(error),
                                  exception=traceback.format_exc())
        # zapi invoke successful
        asup_attr_info = result.get_child_by_name('attributes').get_child_by_name('autosupport-config-info')
        asup_info['service_state'] = 'started' if asup_attr_info['is-enabled'] == 'true' else 'stopped'
        for item_key, zapi_key in self.na_helper.zapi_string_keys.items():
            asup_info[item_key] = asup_attr_info[zapi_key]
        for item_key, zapi_key in self.na_helper.zapi_bool_keys.items():
            asup_info[item_key] = self.na_helper.get_value_for_bool(from_zapi=True,
                                                                    value=asup_attr_info[zapi_key])
        for item_key, zapi_key in self.na_helper.zapi_list_keys.items():
            parent, dummy = zapi_key
            asup_info[item_key] = self.na_helper.get_value_for_list(from_zapi=True,
                                                                    zapi_parent=asup_attr_info.get_child_by_name(parent)
                                                                    )
        return asup_info

    def modify_autosupport_config(self, modify):
        """
        Invoke zapi - modify autosupport config
        @return: NaElement object / FAILURE with an error_message
        """
        asup_details = {'node-name': self.parameters['node_name']}
        if modify.get('service_state'):
            asup_details['is-enabled'] = 'true' if modify.get('service_state') == 'started' else 'false'
        asup_config = netapp_utils.zapi.NaElement('autosupport-config-modify')
        for item_key in modify:
            if item_key in self.na_helper.zapi_string_keys:
                zapi_key = self.na_helper.zapi_string_keys.get(item_key)
                asup_details[zapi_key] = modify[item_key]
            elif item_key in self.na_helper.zapi_bool_keys:
                zapi_key = self.na_helper.zapi_bool_keys.get(item_key)
                asup_details[zapi_key] = self.na_helper.get_value_for_bool(from_zapi=False,
                                                                           value=modify[item_key])
            elif item_key in self.na_helper.zapi_list_keys:
                parent_key, child_key = self.na_helper.zapi_list_keys.get(item_key)
                asup_config.add_child_elem(self.na_helper.get_value_for_list(from_zapi=False,
                                                                             zapi_parent=parent_key,
                                                                             zapi_child=child_key,
                                                                             data=modify.get(item_key)))
        asup_config.translate_struct(asup_details)
        try:
            return self.server.invoke_successfully(asup_config, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='%s' % to_native(error), exception=traceback.format_exc())

    def autosupport_log(self):
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_autosupport", cserver)

    def apply(self):
        """
        Apply action to autosupport
        """
        current = self.get_autosupport_config()
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                self.modify_autosupport_config(modify)
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """Execute action"""
    asup_obj = NetAppONTAPasup()
    asup_obj.apply()


if __name__ == '__main__':
    main()
