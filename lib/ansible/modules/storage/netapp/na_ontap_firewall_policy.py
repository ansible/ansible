#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_firewall_policy
short_description: NetApp ONTAP Manage a firewall policy
version_added: '2.7'
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)
description:
  - Manage a firewall policy for an Ontap Cluster
extends_documentation_fragment:
  - netapp.na_ontap
options:
  state:
    description:
      - Whether to set up a fire policy or not
    choices: ['present', 'absent']
    default: present
  allow_list:
    description:
      - A list of IPs and masks to use
  policy:
    description:
      - A policy name for the firewall policy
    required: true
  service:
    description:
      - The service to apply the policy to
    choices: ['http', 'https', 'ntp', 'rsh', 'snmp', 'ssh', 'telnet']
    required: true
  vserver:
    description:
      - The Vserver to apply the policy to.
    required: true
  enable:
    description:
      - enabled firewall
    choices: ['enable', 'disable']
    default: enable
  logging:
    description:
      - enable logging
    choices: ['enable', 'disable']
    default: disable
  node:
    description:
      - The node to run the firewall configuration on
    required: True
'''

EXAMPLES = """
    - name: create firewall Policy
      na_ontap_firewall_policy:
        state: present
        allow_list: [1.2.3.4/24,1.3.3.4/24]
        policy: pizza
        service: http
        vserver: ci_dev
        hostname: "{{ netapp hostname }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        node: laurentn-vsim1

    - name: Modify firewall Policy
      na_ontap_firewall_policy:
        state: present
        allow_list: [1.2.3.4/24,1.3.3.4/24]
        policy: pizza
        service: http
        vserver: ci_dev
        hostname: "{{ netapp hostname }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        node: laurentn-vsim1

    - name: Destory firewall Policy
      na_ontap_firewall_policy:
        state: absent
        policy: pizza
        service: http
        vserver: ci_dev
        hostname: "{{ netapp hostname }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        node: laurentn-vsim1
"""

RETURN = """
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPFirewallPolicy(object):
    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            allow_list=dict(required=False, type="list"),
            policy=dict(required=True, type='str'),
            service=dict(required=True, type='str', choices=['http', 'https', 'ntp', 'rsh', 'snmp', 'ssh', 'telnet']),
            vserver=dict(required=True, type="str"),
            enable=dict(required=False, type="str", choices=['enable', 'disable'], default='enable'),
            logging=dict(required=False, type="str", choices=["enable", 'disable'], default='disable'),
            node=dict(required=True, type="str")
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
        return

    def create_firewall_policy(self):
        """
        Create a firewall policy
        :return: Nothing
        """
        net_firewall_policy_obj = netapp_utils.zapi.NaElement("net-firewall-policy-create")
        net_firewall_policy_obj = self.create_modify_policy(net_firewall_policy_obj)
        try:
            self.server.invoke_successfully(net_firewall_policy_obj, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error creating Firewall Policy: %s" % (to_native(error)), exception=traceback.format_exc())

    def destroy_firewall_policy(self):
        """
        Destroy a Firewall Policy
        :return: None
        """
        net_firewall_policy_obj = netapp_utils.zapi.NaElement("net-firewall-policy-destroy")
        net_firewall_policy_obj.add_new_child('policy', self.parameters['policy'])
        net_firewall_policy_obj.add_new_child('service', self.parameters['service'])
        net_firewall_policy_obj.add_new_child('vserver', self.parameters['vserver'])
        try:
            self.server.invoke_successfully(net_firewall_policy_obj, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error destroying Firewall Policy: %s" % (to_native(error)), exception=traceback.format_exc())

    def get_firewall_policy(self):
        """
        Get a firewall policy
        :return: returns a firewall policy object, or returns False if there are none
        """
        net_firewall_policy_obj = netapp_utils.zapi.NaElement("net-firewall-policy-get-iter")
        net_firewall_policy_info = netapp_utils.zapi.NaElement("net-firewall-policy-info")
        query = netapp_utils.zapi.NaElement('query')
        net_firewall_policy_info.add_new_child('policy', self.parameters['policy'])
        query.add_child_elem(net_firewall_policy_info)
        net_firewall_policy_obj.add_child_elem(query)
        result = self.server.invoke_successfully(net_firewall_policy_obj, True)
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            return result
        return False

    def modify_firewall_policy(self):
        """
        Modify a firewall Policy
        :return: none
        """
        net_firewall_policy_obj = netapp_utils.zapi.NaElement("net-firewall-policy-modify")
        net_firewall_policy_obj = self.create_modify_policy(net_firewall_policy_obj)
        try:
            self.server.invoke_successfully(net_firewall_policy_obj, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error modifying Firewall Policy: %s" % (to_native(error)), exception=traceback.format_exc())

    def create_modify_policy(self, net_firewall_policy_obj):
        """
        Set up the parameters for creating or modifying a policy
        :param net_firewall_policy_obj: The Firewall policy to modify
        :return:
        """
        net_firewall_policy_obj.add_new_child('policy', self.parameters['policy'])
        net_firewall_policy_obj.add_new_child('service', self.parameters['service'])
        net_firewall_policy_obj.add_new_child('vserver', self.parameters['vserver'])
        allow_ip_list = netapp_utils.zapi.NaElement("allow-list")
        for each in self.parameters['allow_list']:
            net_firewall_policy_ip = netapp_utils.zapi.NaElement("ip-and-mask")
            net_firewall_policy_ip.set_content(each)
            allow_ip_list.add_child_elem(net_firewall_policy_ip)
        net_firewall_policy_obj.add_child_elem(allow_ip_list)
        return net_firewall_policy_obj

    def get_firewall_config(self):
        """
        Get a firewall configuration
        :return: the firewall configuration
        """
        net_firewall_config_obj = netapp_utils.zapi.NaElement("net-firewall-config-get")
        net_firewall_config_obj.add_new_child('node-name', self.parameters['node'])
        try:
            result = self.server.invoke_successfully(net_firewall_config_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error getting Firewall Configuration: %s" % (to_native(error)), exception=traceback.format_exc())
        return result

    def check_policy(self, policy):
        """
        Check to see if a policy has been changed or not
        :param policy: policy to check
        :return: True if the policy has changed, False if there are no changes
        """
        changed = False
        attributes_list = policy.get_child_by_name('attributes-list')
        policy_info = attributes_list.get_child_by_name('net-firewall-policy-info')
        allow_list = policy_info.get_child_by_name('allow-list')
        for each in allow_list.get_children():
            if each.get_content() not in self.parameters['allow_list']:
                changed = True
        if self.parameters['service'] != policy_info.get_child_by_name('service').get_content():
            changed = True
        if self.parameters['policy'] != policy_info.get_child_by_name('policy').get_content():
            changed = True
        return changed

    def modify_firewall_config(self):
        """
        Modify the configuration of a firewall
        :return: none
        """
        net_firewall_config_obj = netapp_utils.zapi.NaElement("net-firewall-config-modify")
        net_firewall_config_obj.add_new_child('node-name', self.parameters['node'])
        net_firewall_config_obj.add_new_child('is-enabled', self.parameters['enable'])
        net_firewall_config_obj.add_new_child('is-logging', self.parameters['logging'])
        try:
            self.server.invoke_successfully(net_firewall_config_obj, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error modifying Firewall Config: %s" % (to_native(error)), exception=traceback.format_exc())

    def check_config(self, config):
        """
        check to see if a firewall configuration has changed or not
        :param config: The configuration to check
        :return: true if it has changed, false if it has not
        """
        changed = False
        attributes_list = config.get_child_by_name('attributes')
        firewall_info = attributes_list.get_child_by_name('net-firewall-config-info')
        enable = firewall_info.get_child_by_name('is-enabled')
        logging = firewall_info.get_child_by_name('is-logging')
        if self.parameters['enable'] == 'enable':
            is_enable = "true"
        else:
            is_enable = "false"
        if enable != is_enable:
            changed = True
        if self.parameters['logging'] == 'logging':
            is_logging = "true"
        else:
            is_logging = "false"
        if logging != is_logging:
            changed = True
        return changed

    def apply(self):
        changed = False
        if self.parameters['state'] == 'present':
            policy = self.get_firewall_policy()
            if not policy:
                self.create_firewall_policy()
                if not self.check_config(self.get_firewall_config()):
                    self.modify_firewall_config()
                changed = True
            else:
                if self.check_policy(policy):
                    self.modify_firewall_policy()
                    changed = True
                if not self.check_config(self.get_firewall_config()):
                    self.modify_firewall_config()
                    changed = True
        else:
            if self.get_firewall_policy():
                self.destroy_firewall_policy()
                if not self.check_config(self.get_firewall_config()):
                    self.modify_firewall_config()
                changed = True
            else:
                if not self.check_config(self.get_firewall_config()):
                    self.modify_firewall_config()
                    changed = True
        self.module.exit_json(changed=changed)


def main():
    """
    Execute action from playbook
    :return: nothing
    """
    cg_obj = NetAppONTAPFirewallPolicy()
    cg_obj.apply()


if __name__ == '__main__':
    main()
