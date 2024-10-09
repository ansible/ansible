#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

from __future__ import annotations

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: ping
version_added: historical
short_description: Try to connect to host, verify a usable python and return C(pong) on success.
description:
   - A trivial test module, this module always returns C(pong) on successful
     contact. It does not make sense in playbooks, but it is useful from
     C(/usr/bin/ansible) to verify the ability to login and that a usable python is configured.
   - This is NOT ICMP ping, this is just a trivial test module.
options: {}
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
"""

EXAMPLES = """
# Test we can logon to 'webservers' and execute python with json lib.
ansible webservers -m ping
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            data=dict(required=False, default=None),
        ),
        supports_check_mode=True
    )
    result = dict(ping='pong')
    if module.params['data']:
        if module.params['data'] == 'crash':
            raise Exception("boom")
        result['ping'] = module.params['data']
    result['location'] = 'role: foo'
    module.exit_json(**result)


if __name__ == '__main__':
    main()
