#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Cisco and/or its affiliates.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'certified'
}

DOCUMENTATION = '''
---
module: nso_verify
extends_documentation_fragment: nso
short_description: Verifies Cisco NSO configuration.
description:
  - This module provides support for verifying Cisco NSO configuration is in
    compliance with specified values.
requirements:
  - Cisco NSO version 3.4.12 or higher, 4.2.7 or higher,
    4.3.8 or higher, 4.4.3 or higher, 4.5 or higher.
author: "Claes Nästén (@cnasten)"
options:
  data:
    description: >
      NSO data in format as C(| display json) converted to YAML. List entries can
      be annotated with a C(__state) entry. Set to in-sync/deep-in-sync for
      services to verify service is in sync with the network. Set to absent in
      list entries to ensure they are deleted if they exist in NSO.
    required: true
version_added: "2.5"
'''

EXAMPLES = '''
- name: Verify interface is up
  nso_config:
    url: http://localhost:8080/jsonrpc
    username: username
    password: password
    data:
      ncs:devices:
        device:
        - name: ce0
          live-status:
            interfaces:
              interface:
                - name: GigabitEthernet0/12
                - state: Up
'''

RETURN = '''
violations:
    description: List of value violations
    returned: failed
    type: complex
    sample:
        - path: /ncs:devices/device{ce0}/description
          expected-value: CE0 example
          value: null
    contains:
        path:
            description: Path to the value in violation
            returned: always
            type: str
        expected-value:
            description: Expected value of path
            returned: always
            type: str
        value:
            description: Current value of path
            returned: always
            type: str
'''

from ansible.module_utils.network.nso.nso import connect, verify_version, nso_argument_spec
from ansible.module_utils.network.nso.nso import normalize_value
from ansible.module_utils.network.nso.nso import State, ValueBuilder
from ansible.module_utils.network.nso.nso import ModuleFailException, NsoException
from ansible.module_utils.basic import AnsibleModule


class NsoVerify(object):
    REQUIRED_VERSIONS = [
        (4, 5),
        (4, 4, 3),
        (4, 3, 8),
        (4, 2, 7),
        (3, 4, 12)
    ]

    def __init__(self, client, data):
        self._client = client
        self._data = data

    def main(self):
        violations = []

        # build list of values from configured data
        value_builder = ValueBuilder(self._client, 'verify')
        for key, value in self._data.items():
            value_builder.build('', key, value)

        for expected_value in value_builder.values:
            if expected_value.state == State.PRESENT:
                violations.append({
                    'path': expected_value.path,
                    'expected-value': 'present',
                    'value': 'absent'
                })
            elif expected_value.state == State.ABSENT:
                violations.append({
                    'path': expected_value.path,
                    'expected-value': 'absent',
                    'value': 'present'
                })
            elif expected_value.state == State.SET:
                try:
                    value = self._client.get_value(expected_value.path)['value']
                except NsoException as ex:
                    if ex.error.get('type', '') == 'data.not_found':
                        value = None
                    else:
                        raise

                # handle different types properly
                n_value = normalize_value(
                    expected_value.value, value, expected_value.path)
                if n_value != expected_value.value:
                    # if the value comparision fails, try mapping identityref
                    value_type = value_builder.get_type(expected_value.path)
                    if value_type is not None and 'identityref' in value_type:
                        n_value, t_value = self.get_prefix_name(value)

                    if expected_value.value != n_value:
                        violations.append({
                            'path': expected_value.path,
                            'expected-value': expected_value.value,
                            'value': n_value
                        })
            else:
                raise ModuleFailException(
                    'value state {0} not supported at {1}'.format(
                        expected_value.state, expected_value.path))

        return violations


def main():
    argument_spec = dict(
        data=dict(required=True, type='dict')
    )
    argument_spec.update(nso_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    p = module.params

    client = connect(p)
    nso_verify = NsoVerify(client, p['data'])
    try:
        verify_version(client, NsoVerify.REQUIRED_VERSIONS)

        violations = nso_verify.main()
        client.logout()

        num_violations = len(violations)
        if num_violations > 0:
            msg = '{0} value{1} differ'.format(
                num_violations, num_violations > 1 and 's' or '')
            module.fail_json(msg=msg, violations=violations)
        else:
            module.exit_json(changed=False)

    except NsoException as ex:
        client.logout()
        module.fail_json(msg=ex.message)
    except ModuleFailException as ex:
        client.logout()
        module.fail_json(msg=ex.message)


if __name__ == '__main__':
    main()
