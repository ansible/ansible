#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_lldp_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage LLDP interfaces configuration on Juniper JUNOS network devices
description:
  - This module provides declarative management of LLDP interfaces
    configuration on Juniper JUNOS network devices.
options:
  name:
    description:
      - Name of the interface LLDP should be configured on.
  aggregate:
    description: List of interfaces LLDP should be configured on.
  purge:
    description:
      - Purge interfaces not defined in the aggregate parameter.
    default: no
  state:
    description:
      - Value of C(present) ensures given LLDP configured on given I(interfaces)
        and is enabled, for value of C(absent) LLDP configuration on given I(interfaces) deleted.
        Value C(enabled) ensures LLDP protocol is enabled on given I(interfaces) and
         for value of C(disabled) it ensures LLDP is disabled on given I(interfaces).
    default: present
    choices: ['present', 'absent', 'enabled', 'disabled']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    choices: [True, False]
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- name: Configure LLDP on specific interfaces
  junos_lldp_interface:
    name: ge-0/0/5
    state: present

- name: Disable LLDP on specific interfaces
  junos_lldp_interface:
    name: ge-0/0/5
    state: disabled

- name: Enable LLDP on specific interfaces
  junos_lldp_interface:
    name: ge-0/0/5
    state: enabled

- name: Delete LLDP configuration on specific interfaces
  junos_lldp_interface:
    name: ge-0/0/5
    state: present

- name: Deactivate LLDP on specific interfaces
  junos_lldp_interface:
    name: ge-0/0/5
    state: present
    active: False

- name: Activate LLDP on specific interfaces
  junos_lldp_interface:
    name: ge-0/0/5
    state: present
    active: True
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
        [edit protocols lldp]
        +    interface ge-0/0/5;
"""
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent', 'enabled', 'disabled']),
        active=dict(default=True, type='bool')
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'protocols/lldp/interface'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True}),
        ('disable', {'xpath': 'disable', 'tag_only': True})
    ])

    state = module.params.get('state')
    module.params['disable'] = True if state in ('disabled', 'absent') else False

    if state in ('enabled', 'disabled'):
        module.params['state'] = 'present'

    want = map_params_to_obj(module, param_to_xpath_map)
    ele = map_obj_to_ele(module, want, top)

    with locked_config(module):
        diff = load_config(module, tostring(ele), warnings, action='replace')

        commit = not module.check_mode
        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)
            result['changed'] = True

            if module._diff:
                result['diff'] = {'prepared': diff}

    module.exit_json(**result)

if __name__ == "__main__":
    main()
