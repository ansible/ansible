#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: shutdown
short_description: Shutdown a machine
notes:
  - C(PATH) is ignored on the remote node when searching for the C(shutdown) command. Use C(search_paths)
    to specify locations to search if the default paths do not work.
  - Extension of the M(reboot) action.
description:
    - Shutdown a machine
    - For Windows targets, use the M(win_shutdown) module instead.
version_added: "2.8"
options:
  pre_reboot_delay:
    description:
      - Seconds to wait before reboot. Passed as a parameter to the reboot command.
      - On Linux, macOS and OpenBSD, this is converted to minutes and rounded down. If less than 60, it will be set to 0.
      - On Solaris and FreeBSD, this will be seconds.
    type: int
    default: 0
  post_reboot_delay:
    description:
      - Seconds to wait after the reboot command was successful before attempting to validate the system rebooted successfully.
      - This is useful if you want wait for something to settle despite your connection already working.
    type: int
    default: 0
  reboot_timeout:
    description:
      - Maximum seconds to wait for machine to reboot and respond to a test command.
      - This timeout is evaluated separately for both reboot verification and test command success so the
        maximum execution time for the module is twice this amount.
    type: int
    default: 600
  connect_timeout:
    description:
      - Maximum seconds to wait for a successful connection to the managed hosts before trying again.
      - If unspecified, the default setting for the underlying connection plugin is used.
    type: int
  test_command:
    description:
      - Command to run on the rebooted host and expect success from to determine the machine is ready for
        further tasks.
    type: str
    default: whoami
  msg:
    description:
      - Message to display to users before reboot.
    type: str
    default: Reboot initiated by Ansible

  search_paths:
    description:
      - Paths to search on the remote machine for the C(shutdown) command.
      - I(Only) these paths will be searched for the C(shutdown) command. C(PATH) is ignored in the remote node when searching for the C(shutdown) command.
    type: list
    default: ['/sbin', '/usr/sbin', '/usr/local/sbin']
    version_added: '2.8'
seealso:
- module: win_reboot
author:
    - Matt Davis (@nitzmahone)
    - Sam Doran (@samdoran)
'''

EXAMPLES = r'''
- name: Unconditionally shutdown the machine with all defaults
  shutdown:
'''
