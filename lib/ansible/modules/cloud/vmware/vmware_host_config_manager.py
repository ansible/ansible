#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_host_config_manager
short_description: Manage advance configurations about an ESXi host
description:
- This module can be used to manage advance configuration information about an ESXi host when ESXi hostname or Cluster name is given.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - Settings are applied to every ESXi host system in given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - Settings are applied to this ESXi host system.
    - If C(cluster_name) is not given, this parameter is required.
  options:
    description:
    - A dictionary of advance configuration parameters.
    - Invalid options will cause module to error.
    default: {}
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Manage Log level setting for all ESXi Host in given Cluster
  vmware_host_config_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
    options:
        'Config.HostAgent.log.level': 'info'

- name: Manage Log level setting for an ESXi Host
  vmware_host_config_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    options:
        'Config.HostAgent.log.level': 'verbose'

- name: Manage multiple settings for an ESXi Host
  vmware_host_config_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    options:
        'Config.HostAgent.log.level': 'verbose'
        'Annotations.WelcomeMessage': 'Hello World'
        'Config.HostAgent.plugins.solo.enableMob': false
'''

RETURN = r'''#
'''

try:
    from pyVmomi import vim, vmodl, VmomiSupport
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native
from ansible.module_utils.six import integer_types, string_types


class VmwareConfigManager(PyVmomi):
    def __init__(self, module):
        super(VmwareConfigManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.options = self.params.get('options', dict())
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    @staticmethod
    def is_integer(value, type_of='int'):
        try:
            VmomiSupport.vmodlTypes[type_of](value)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def is_boolean(value):
        if str(value).lower() in ['true', 'on', 'yes', 'false', 'off', 'no']:
            return True
        return False

    @staticmethod
    def is_truthy(value):
        if str(value).lower() in ['true', 'on', 'yes']:
            return True
        return False

    def set_host_configuration_facts(self):
        changed = False
        for host in self.hosts:
            option_manager = host.configManager.advancedOption
            host_facts = {}
            for option in option_manager.QueryOptions():
                host_facts[option.key] = dict(value=option.value)

            for s_option in option_manager.supportedOption:
                host_facts[s_option.key].update(
                    option_type=s_option.optionType,
                )

            change_option_list = []
            for option_key, option_value in self.options.items():
                if option_key in host_facts:
                    # Make sure option_type is defined some values do not have
                    # it defined and appear to be read only.
                    if 'option_type' in host_facts[option_key]:
                        # We handle all supported types here so we can give meaningful errors.
                        option_type = host_facts[option_key]['option_type']
                        if self.is_boolean(option_value) and isinstance(option_type, vim.option.BoolOption):
                            option_value = self.is_truthy(option_value)
                        elif (isinstance(option_value, integer_types) or self.is_integer(option_value))\
                                and isinstance(option_type, vim.option.IntOption):
                            option_value = VmomiSupport.vmodlTypes['int'](option_value)
                        elif (isinstance(option_value, integer_types) or self.is_integer(option_value, 'long'))\
                                and isinstance(option_type, vim.option.LongOption):
                            option_value = VmomiSupport.vmodlTypes['long'](option_value)
                        elif isinstance(option_value, float) and isinstance(option_type, vim.option.FloatOption):
                            pass
                        elif isinstance(option_value, string_types) and isinstance(option_type, (vim.option.StringOption, vim.option.ChoiceOption)):
                            pass
                        else:
                            self.module.fail_json(msg="Provided value is of type %s."
                                                      " Option %s expects: %s" % (type(option_value), option_key, type(option_type)))
                    else:
                        self.module.fail_json(msg="Cannot change read only option %s to %s." % (option_key, option_value))

                    if option_value != host_facts[option_key]['value']:
                        change_option_list.append(vim.option.OptionValue(key=option_key, value=option_value))
                        changed = True
                else:  # Don't silently drop unknown options. This prevents typos from falling through the cracks.
                    self.module.fail_json(msg="Unknown option %s" % option_key)
            if changed:
                try:
                    option_manager.UpdateOptions(changedValue=change_option_list)
                except vmodl.fault.InvalidArgument as e:
                    self.module.fail_json(msg="Failed to update option/s as one or more OptionValue "
                                              "contains an invalid value: %s" % to_native(e.msg))
                except vim.fault.InvalidName as e:
                    self.module.fail_json(msg="Failed to update option/s as one or more OptionValue "
                                              "objects refers to a non-existent option : %s" % to_native(e.msg))

        self.module.exit_json(changed=changed)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        options=dict(type='dict', default=dict(), required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )

    vmware_host_config = VmwareConfigManager(module)
    vmware_host_config.set_host_configuration_facts()


if __name__ == "__main__":
    main()
