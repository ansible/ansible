# -*- mode: python -*-
# (c) 2017, Dag Wieers <dag@wieers.com>

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

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: wait_for_connection
short_description: Waitis until remote system is reachable
description:
  - You can wait for a set amount of time C(timeout), this is the default if nothing is specified.
  - Waiting until the ansible connection works is useful for when systems are expected to be down and it is essential that the system is reachable before continuing.
  - This module makes use of internal ansible transport (and configuration) and the ping/win_ping module to guarantee correct functioning of transport.
version_added: '2.3'
options:
  connect_timeout:
    description:
      - Maximum number of seconds to wait for a connection to happen before closing and retrying.
    required: false
    default: 5
  sleep:
    description:
      - Number of seconds to sleep between checks.
    required: false
    default: 1
  timeout:
    description:
      - Maximum number of seconds to wait for.
    required: false
    default: 300
author: 'Dag Wieers (@dagwieers)'
'''

EXAMPLES = '''
# Wait for the remote system to be reachable
- wait_for_connection:
    timeout: 120
'''