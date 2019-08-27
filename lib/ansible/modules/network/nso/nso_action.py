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
module: nso_action
extends_documentation_fragment: nso
short_description: Executes Cisco NSO actions and verifies output.
description:
  - This module provides support for executing Cisco NSO actions and then
    verifying that the output is as expected.
requirements:
  - Cisco NSO version 3.4 or higher.
author: "Claes Nästén (@cnasten)"
options:
  path:
    description: Path to NSO action.
    required: true
  input:
    description: >
      NSO action parameters.
  output_required:
     description: >
       Required output parameters.
  output_invalid:
     description: >
       List of result parameter names that will cause the task to fail if they
       are present.
  validate_strict:
     description: >
       If set to true, the task will fail if any output parameters not in
       output_required is present in the output.
     type: bool
version_added: "2.5"
'''

EXAMPLES = '''
- name: Sync NSO device
  nso_action:
    url: http://localhost:8080/jsonrpc
    username: username
    password: password
    path: /ncs:devices/device{ce0}/sync-from
    input: {}
'''

RETURN = '''
output:
  description: Action output
  returned: success
  type: dict
  sample:
    result: true
'''

from ansible.module_utils.network.nso.nso import connect, verify_version, nso_argument_spec
from ansible.module_utils.network.nso.nso import normalize_value
from ansible.module_utils.network.nso.nso import ModuleFailException, NsoException
from ansible.module_utils.basic import AnsibleModule


class NsoAction(object):
    REQUIRED_VERSIONS = [
        (3, 4)
    ]

    def __init__(self, check_mode, client,
                 path, input,
                 output_required, output_invalid, validate_strict):
        self._check_mode = check_mode
        self._client = client
        self._path = path
        self._input = input
        self._output_required = output_required
        self._output_invalid = output_invalid
        self._validate_strict = validate_strict

    def main(self):
        schema = self._client.get_schema(path=self._path)
        if schema['data']['kind'] != 'action':
            raise ModuleFailException('{0} is not an action'.format(self._path))

        input_schema = [c for c in schema['data']['children']
                        if c.get('is_action_input', False)]

        for key, value in self._input.items():
            child = next((c for c in input_schema if c['name'] == key), None)
            if child is None:
                raise ModuleFailException('no parameter {0}'.format(key))

            # implement type validation in the future

        if self._check_mode:
            return {}
        else:
            return self._run_and_verify()

    def _run_and_verify(self):
        output = self._client.run_action(None, self._path, self._input)
        for key, value in self._output_required.items():
            if key not in output:
                raise ModuleFailException('{0} not in result'.format(key))

            n_value = normalize_value(value, output[key], key)
            if value != n_value:
                msg = '{0} value mismatch. expected {1} got {2}'.format(
                    key, value, n_value)
                raise ModuleFailException(msg)

        for key in self._output_invalid.keys():
            if key in output:
                raise ModuleFailException('{0} not allowed in result'.format(key))

        if self._validate_strict:
            for name in output.keys():
                if name not in self._output_required:
                    raise ModuleFailException('{0} not allowed in result'.format(name))

        return output


def main():
    argument_spec = dict(
        path=dict(required=True),
        input=dict(required=False, type='dict', default={}),
        output_required=dict(required=False, type='dict', default={}),
        output_invalid=dict(required=False, type='dict', default={}),
        validate_strict=dict(required=False, type='bool', default=False)
    )
    argument_spec.update(nso_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    p = module.params

    client = connect(p)
    nso_action = NsoAction(
        module.check_mode, client,
        p['path'],
        p['input'],
        p['output_required'],
        p['output_invalid'],
        p['validate_strict'])
    try:
        verify_version(client, NsoAction.REQUIRED_VERSIONS)

        output = nso_action.main()
        client.logout()
        module.exit_json(changed=True, output=output)
    except NsoException as ex:
        client.logout()
        module.fail_json(msg=ex.message)
    except ModuleFailException as ex:
        client.logout()
        module.fail_json(msg=ex.message)


if __name__ == '__main__':
    main()
