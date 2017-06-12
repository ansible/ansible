#!/usr/bin/python

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
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: lightbulb
short_description: lightbulb for your brainz
description: insane in the membraine
version_added: 2.4
author: James Tanner (@jctanner)
deprecated:
options: {}
requirements: []
'''


EXAMPLES = '''
- name: run lightbulb
  lightbulb:
'''


RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    pass


if __name__ == '__main__':
    main()
