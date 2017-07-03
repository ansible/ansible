#!/usr/bin/python
# -*- coding: utf-8 -*-

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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_reboot
short_description: Reboot a windows machine
description:
     - Reboot a Windows machine, wait for it to go down, come back up, and respond to commands.
version_added: "2.1"
options:
  pre_reboot_delay_sec:
    description:
    - Seconds for shutdown to wait before requesting reboot
    default: 2
  shutdown_timeout_sec:
    description:
    - Maximum seconds to wait for shutdown to occur
    - Increase this timeout for very slow hardware, large update applications, etc
    default: 600
  reboot_timeout_sec:
    description:
    - Maximum seconds to wait for machine to re-appear on the network and respond to a test command
    - This timeout is evaluated separately for both network appearance and test command success (so maximum clock time is actually twice this value)
    default: 600
  connect_timeout_sec:
    description:
    - Maximum seconds to wait for a single successful TCP connection to the WinRM endpoint before trying again
    default: 5
  test_command:
    description:
    - Command to expect success for to determine the machine is ready for management
    default: whoami
  msg:
    description:
    - Message to display to users
    default: Reboot initiated by Ansible
notes:
- If a shutdown was already scheduled on the system, C(win_reboot) will abort the scheduled shutdown and enforce its own shutdown.
author:
    - Matt Davis (@nitzmahone)
'''

EXAMPLES = r'''
# Unconditionally reboot the machine with all defaults
- win_reboot:

# Apply updates and reboot if necessary
- win_updates:
  register: update_result
- win_reboot:
  when: update_result.reboot_required

# Reboot a slow machine that might have lots of updates to apply
- win_reboot:
    shutdown_timeout_sec: 3600
    reboot_timeout_sec: 3600
'''

RETURN = r'''
rebooted:
    description: true if the machine was rebooted
    returned: always
    type: boolean
    sample: true
'''
