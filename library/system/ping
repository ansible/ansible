#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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


DOCUMENTATION = '''
---
module: ping
version_added: historical
short_description: Try to connect to host and return C(pong) on success.
description:
   - A trivial test module, this module always returns C(pong) on successful
     contact. It does not make sense in playbooks, but it is useful from
     C(/usr/bin/ansible)
options: {}
author: Michael DeHaan
'''

EXAMPLES = '''
# Test 'webservers' status
ansible webservers -m ping
'''

import exceptions

def main():
    module = AnsibleModule(
        argument_spec = dict(
            data=dict(required=False, default=None),
        ),
        supports_check_mode = True
    )
    result = dict(ping='pong')
    if module.params['data']:
        if module.params['data'] == 'crash':
            raise exceptions.Exception("boom")
        result['ping'] = module.params['data']
    module.exit_json(**result)

from ansible.module_utils.basic import *

main()

