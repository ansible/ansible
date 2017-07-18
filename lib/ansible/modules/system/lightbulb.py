#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Sean Sullivan <blank@stuff.com>
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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: filament
short_description: Print Hello World
version_added: "2.4"
author: Sean S <blank@stuff.com>
description:
  - This modules outputs Hello World
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import pdb
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            foo=dict(default='bar'),
        ),
        supports_check_mode=True
    )
    epdb.st()

    if module.params['state'] == 'absent':
        module.exit_json(changed=False)

    module.exit_json(changed=True, filament="hello world")


if __name__ == '__main__':
    main()
