#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: wait_for_connection
short_description: Waits until remote system is reachable/usable
description:
- Waits for a total of C(timeout) seconds.
- Retries the transport connection after a timeout of C(connect_timeout).
- Tests the transport connection every C(sleep) seconds.
- This module makes use of internal ansible transport (and configuration) and the ping/win_ping module to guarantee correct end-to-end functioning.
version_added: "2.3"
options:
  connect_timeout:
    description:
      - Maximum number of seconds to wait for a connection to happen before closing and retrying.
    default: 5
  delay:
    description:
      - Number of seconds to wait before starting to poll.
    default: 0
  sleep:
    default: 1
    description:
      - Number of seconds to sleep between checks.
  timeout:
    description:
      - Maximum number of seconds to wait for.
    default: 300
author: "Dag Wieers (@dagwieers)"
'''

EXAMPLES = '''
# Wait 300 seconds for system's connection to become reachable/usable by Ansible
- wait_for_connection:

# Wait 600 seconds for system's connection, but only start checking after 60 seconds
- wait_for_connection:
    delay: 60
    timeout: 600
'''
