#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
module: reboot
short_description: Reboot a \*nix machine
description:
     - Reboot a \*nix machine, wait for it to go down, come back up, and respond to commands.
version_added: "2.7"
options:
  pre_reboot_delay:
    description:
      - Minutes for shutdown to wait before requesting reboot
    default: 0
  post_reboot_delay:
    description:
      - Seconds to wait after the reboot was successful and the connection was re-established
      - This is useful if you want wait for something to settle despite your connection already working
    default: 0
  reboot_timeout:
    description:
      - Maximum seconds to wait for machine to reboot and respond to a test command
      - This timeout is evaluated separately for both network connection and test command success so the
        maximum execution time for the module is twice this amount.
    default: 600
  connect_timeout:
    description:
      - Maximum seconds to wait for a single successful TCP connection to the managed hosts before trying again
      - This defaults to None which means the default setting for the underlying connection plugin is used.
    default: None
  test_command:
    description:
      - Command to run on the rebooted host and expect success from to determine the machine is ready for
        further tasks.
    default: whoami
  msg:
    description:
      - Message to display to users
    default: Reboot initiated by Ansible
author:
    - Matt Davis (@nitzmahone)
    - Sam Doran (@samdoran)
'''

EXAMPLES = r'''
# Unconditionally reboot the machine with all defaults
- reboot:

# Reboot a slow machine that might have lots of updates to apply
- reboot:
    reboot_timeout: 3600
'''

RETURN = r'''
rebooted:
  description: true if the machine was rebooted
  returned: always
  type: boolean
  sample: true
elapsed:
  description: The number of seconds that elapsed waiting for the system to be rebooted.
  returned: always
  type: int
  sample: 23
'''
