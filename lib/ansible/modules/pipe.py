#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, LoveIsGrief
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: pipe
version_added: "2.11"
short_description: Pipe local command to a remote command
description:
    - The C(pipe) action executes a command locally and pipes the output thereof to a remote host.
options:
  local:
    description:
    - The command to execute on the local machine
    type: str
    required: yes
  remote:
    description:
    - The command to execute on the remote machine.
    - Its input will be the stdoutput of the local command
    type: str
    required: yes
seealso:
- module: ansible.builtin.command
- module: ansible.builtin.script
author:
- LoveIsGrief (@LoveIsGrief)
'''

EXAMPLES = r'''
- name: Copy file with owner and permissions
  ansible.builtin.pipe:
    local: docker save {{ image }}
    remote: docker load
'''

RETURN = r'''
local.rc:
    description: Return code of the local command
    returned: always
    type: int
    sample: 0
remote.rc:
    description: Return code of the remote command
    returned: always
    type: int
    sample: 0
'''
