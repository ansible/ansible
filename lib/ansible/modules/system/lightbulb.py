#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Ted Trask <ttrask01@yahoo.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: awall
short_description: Manage awall policies
version_added: "2.4"
author: Ted Trask (@tdtrask) <ttrask01@yahoo.com>
description:
  - This modules allows for enable/disable/activate of I(awall) policies.
    Alpine Wall (I(awall)) generates a firewall configuration from the enabled policy files
    and activates the configuration on the system.
options:
  name:
    description:
      - A policy name, like C(foo), or multiple policies, like C(foo, bar).
    default: null
  state:
    description:
      - The policy(ies) will be C(enabled)
      - The policy(ies) will be C(disabled)
    default: enabled
    choices: [ "enabled", "disabled" ]
  activate:
    description:
      - Activate the new firewall rules. Can be run with other steps or on it's own.
    default: False
'''

EXAMPLES = '''
- name: Hello World


'''

RETURN = ''' # '''

import re
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
    )

    print("hello world")
    module.fail_json(msg="no action defined")

# import module snippets
if __name__ == '__main__':
    main()
