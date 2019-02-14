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
module: nso_show
extends_documentation_fragment: nso
short_description: Displays data from Cisco NSO.
description:
  - This module provides support for displaying data from Cisco NSO.
requirements:
  - Cisco NSO version 3.4.12 or higher, 4.1.9 or higher, 4.2.6 or higher,
    4.3.7 or higher, 4.4.5 or higher, 4.5 or higher.
author: "Claes Nästén (@cnasten)"
options:
  path:
    description: Path to NSO data.
    required: true
  operational:
    description: >
      Controls whether or not operational data is included in the result.
    type: bool
    default: false
version_added: "2.5"
'''

EXAMPLES = '''
- name: Show devices including operational data
  nso_show:
    url: http://localhost:8080/jsonrpc
    username: username
    password: password
    path: /ncs:devices/device
    operational: true
'''

RETURN = '''
output:
  description: Configuration
  returned: success
  type: dict
'''

from ansible.module_utils.network.nso.nso import connect, verify_version, nso_argument_spec
from ansible.module_utils.network.nso.nso import ModuleFailException, NsoException
from ansible.module_utils.basic import AnsibleModule


class NsoShow(object):
    REQUIRED_VERSIONS = [
        (4, 5),
        (4, 4, 5),
        (4, 3, 7),
        (4, 2, 6),
        (4, 1, 9),
        (3, 4, 12)
    ]

    def __init__(self, check_mode, client, path, operational):
        self._check_mode = check_mode
        self._client = client
        self._path = path
        self._operational = operational

    def main(self):
        if self._check_mode:
            return {}
        else:
            return self._client.show_config(self._path, self._operational)


def main():
    argument_spec = dict(
        path=dict(required=True, type='str'),
        operational=dict(required=False, type='bool', default=False)
    )
    argument_spec.update(nso_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    p = module.params

    client = connect(p)
    nso_show = NsoShow(
        module.check_mode, client,
        p['path'], p['operational'])
    try:
        verify_version(client, NsoShow.REQUIRED_VERSIONS)

        output = nso_show.main()
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
