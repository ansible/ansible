#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_system
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage the system attributes on Juniper JUNOS devices
description:
  - This module provides declarative management of node system attributes
    on Juniper JUNOS devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
  domain_name:
    description:
      - Configure the IP domain name
        on the remote device to the provided value. Value
        should be in the dotted name form and will be
        appended to the C(hostname) to create a fully-qualified
        domain name.
  domain_search:
    description:
      - Provides the list of domain suffixes to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers See
        examples.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    type: bool
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
extends_documentation_fragment: junos
"""

EXAMPLES = """
- name: configure hostname and domain name
  junos_system:
    hostname: junos01
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - juniper.com

- name: remove configuration
  junos_system:
    state: absent

- name: configure name servers
  junos_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
          [edit system]
          +  host-name test;
          +  domain-name ansible.com;
          +  domain-search redhat.com;
          [edit system name-server]
              172.26.1.1 { ... }
          +   8.8.8.8;
"""
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.junos.junos import junos_argument_spec
from ansible.module_utils.network.junos.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes, locked_config

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def validate_param_values(module, obj):
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(module.params.get(key), module)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        hostname=dict(),
        domain_name=dict(),
        domain_search=dict(type='list'),
        name_servers=dict(type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
        active=dict(default=True, type='bool')
    )

    argument_spec.update(junos_argument_spec)

    params = ['hostname', 'domain_name', 'domain_search', 'name_servers']
    required_if = [('state', 'present', params, True),
                   ('state', 'absent', params, True),
                   ('state', 'active', params, True),
                   ('state', 'suspend', params, True)]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'system'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('hostname', {'xpath': 'host-name', 'leaf_only': True}),
        ('domain_name', {'xpath': 'domain-name', 'leaf_only': True}),
        ('domain_search', {'xpath': 'domain-search', 'leaf_only': True, 'value_req': True}),
        ('name_servers', {'xpath': 'name-server/name', 'is_key': True})
    ])

    validate_param_values(module, param_to_xpath_map)

    want = map_params_to_obj(module, param_to_xpath_map)
    ele = map_obj_to_ele(module, want, top)

    with locked_config(module):
        diff = load_config(module, tostring(ele), warnings, action='merge')

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
