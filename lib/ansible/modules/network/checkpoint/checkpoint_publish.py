#!/usr/bin/python
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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: checkpoint_install_policy
short_description: Install policy on Checkpoint devices over Web Services API
description:
  - Install policy on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  uid:
    description:
      - Session unique identifier. Specify it to publish a different session than the one you currently use.
    type: str
"""

EXAMPLES = """
- name: publish
  checkpoint_publish:
"""

RETURN = """
checkpoint_install_policy:
  description: The checkpoint install policy output.
  returned: always.
  type: str
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import api_command


def main():
    argument_spec = dict(
        uid=dict(type='str')
    )

    user_parameters = list(argument_spec.keys())
    module = AnsibleModule(argument_spec=argument_spec)
    command = "publish"

    api_command(module, command, user_parameters)


if __name__ == '__main__':
    main()
