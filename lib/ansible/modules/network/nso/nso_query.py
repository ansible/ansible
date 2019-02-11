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
module: nso_query
extends_documentation_fragment: nso
short_description: Query data from Cisco NSO.
description:
  - This module provides support for querying data from Cisco NSO using XPath.
requirements:
  - Cisco NSO version 3.4 or higher.
author: "Claes Nästén (@cnasten)"
options:
  xpath:
    description: XPath selection relative to the root.
    required: true
  fields:
    description: >
      List of fields to select from matching nodes.
    required: true
version_added: "2.5"
'''

EXAMPLES = '''
- name: Select device name and description
  nso_query:
    url: http://localhost:8080/jsonrpc
    username: username
    password: password
    xpath: /ncs:devices/device
    fields:
    - name
    - description
'''

RETURN = '''
output:
  description: Value of matching nodes
  returned: success
  type: list
'''

from ansible.module_utils.network.nso.nso import connect, verify_version, nso_argument_spec
from ansible.module_utils.network.nso.nso import ModuleFailException, NsoException
from ansible.module_utils.basic import AnsibleModule


class NsoQuery(object):
    REQUIRED_VERSIONS = [
        (3, 4)
    ]

    def __init__(self, check_mode, client, xpath, fields):
        self._check_mode = check_mode
        self._client = client
        self._xpath = xpath
        self._fields = fields

    def main(self):
        if self._check_mode:
            return []
        else:
            return self._client.query(self._xpath, self._fields)


def main():
    argument_spec = dict(
        xpath=dict(required=True, type='str'),
        fields=dict(required=True, type='list')
    )
    argument_spec.update(nso_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    p = module.params

    client = connect(p)
    nso_query = NsoQuery(
        module.check_mode, client,
        p['xpath'], p['fields'])
    try:
        verify_version(client, NsoQuery.REQUIRED_VERSIONS)

        output = nso_query.main()
        client.logout()
        module.exit_json(changed=False, output=output)
    except NsoException as ex:
        client.logout()
        module.fail_json(msg=ex.message)
    except ModuleFailException as ex:
        client.logout()
        module.fail_json(msg=ex.message)


if __name__ == '__main__':
    main()
