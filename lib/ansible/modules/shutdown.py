#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
module: shutdown
short_description: Shut down a machine
notes:
  - C(PATH) is ignored on the remote node when searching for the C(shutdown) command. Use C(search_paths)
    to specify locations to search if the default paths do not work.
description:
    - Shut downs a machine.
version_added: "2.11"
options:
  pre_shutdown_delay:
    description:
      - Seconds to wait before shutdown. Passed as a parameter to the shutdown command.
      - On Linux, macOS and OpenBSD, this is converted to minutes and rounded down. If less than 60, it will be set to 0.
      - On Solaris and FreeBSD, this will be seconds.
    type: int
    default: 0
  connect_timeout:
    description:
      - Maximum seconds to wait for a successful connection to the managed hosts before trying again.
      - If unspecified, the default setting for the underlying connection plugin is used.
    type: int
  msg:
    description:
      - Message to display to users before shutdown.
    type: str
    default: Shut down initiated by Ansible

  search_paths:
    description:
      - Paths to search on the remote machine for the C(shutdown) command.
      - I(Only) these paths will be searched for the C(shutdown) command. C(PATH) is ignored in the remote node when searching for the C(shutdown) command.
    type: list
    default: ['/sbin', '/usr/sbin', '/usr/local/sbin']

author:
    - Matt Davis (@nitzmahone)
    - Sam Doran (@samdoran)
    - Amin Vakil (@aminvakil)
'''

EXAMPLES = r'''
- name: Unconditionally shut down the machine with all defaults
  shutdown:

- name: Delay shutting down the remote node
  shutdown:
    pre_shutdown_delay: 60

- name: Shut down a machine with shutdown command in unusual place
  shutdown:
    search_paths:
     - '/lib/molly-guard'
'''

RETURN = r'''
shutdown:
  description: true if the machine has shut down
  returned: always
  type: bool
  sample: true
'''
