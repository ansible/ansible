#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, James Cammarata <jcammarata@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: accelerate
short_description: Enable accelerated mode on remote node
deprecated:
  removed_in: "2.4"
  why: Replaced by ControlPersist
  alternative: Use SSH with ControlPersist instead.
  removed: True
description:
     - This module has been removed, this file is kept for historical documentation purposes.
     - This modules launches an ephemeral I(accelerate) daemon on the remote node which
       Ansible can use to communicate with nodes at high speed.
     - The daemon listens on a configurable port for a configurable amount of time.
     - Fireball mode is AES encrypted
version_added: "1.3"
options:
  port:
    description:
      - TCP port for the socket connection
    required: false
    default: 5099
    aliases: []
  timeout:
    description:
      - The number of seconds the socket will wait for data. If none is received when the timeout value is reached, the connection will be closed.
    required: false
    default: 300
    aliases: []
  minutes:
    description:
      - The I(accelerate) listener daemon is started on nodes and will stay around for
        this number of minutes before turning itself off.
    required: false
    default: 30
  ipv6:
    description:
      - The listener daemon on the remote host will bind to the ipv6 localhost socket
        if this parameter is set to true.
    required: false
    default: false
  multi_key:
    description:
      - When enabled, the daemon will open a local socket file which can be used by future daemon executions to
        upload a new key to the already running daemon, so that multiple users can connect using different keys.
        This access still requires an ssh connection as the uid for which the daemon is currently running.
    required: false
    default: no
    version_added: "1.6"
notes:
    - See the advanced playbooks chapter for more about using accelerated mode.
requirements:
    - "python >= 2.4"
    - "python-keyczar"
author: "James Cammarata (@jimi-c)"
'''

EXAMPLES = '''
# To use accelerate mode, simply add "accelerate: true" to your play. The initial
# key exchange and starting up of the daemon will occur over SSH, but all commands and
# subsequent actions will be conducted over the raw socket connection using AES encryption

- hosts: devservers
  accelerate: true
  tasks:
      - command: /usr/bin/anything
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
