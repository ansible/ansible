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
module: qradar_test_httpapi
short_description: Test QRadar httpapi
description:
  - Test QRadar httpapi
version_added: "2.8"
author: "Ansible by Red Hat (@maxamillion)"
options:
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def main():
    argument_spec = dict(
        log_source_type=dict(type='str', default=None, required=False)
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)

    code, response = connection.send_request('GET', '/api/config/event_sources/log_source_management/log_sources')
    if code == 200:
        module.exit_json(ansible_facts=dict(qradar_test_data=response))
    else:
        module.fail_json(msg='QRadar appliance returned error {0} with message {1}'.format(code, response))


if __name__ == '__main__':
    main()
