#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: network_put
version_added: "2.6"
author: "Deepak Agrawal (@dagrawal)"
short_description: copy files from ansibe controller to  network devices
description:
  - This module provides functionlity to copy file from controller to
    network devices. file will be copied at remote filesystem
options:
  src:
    description:
      - path of the config file.
    required: true
  protocol:
    description:
      - protocol used to transfer file
    default: scp
    choices: ['scp', 'sftp']
    required: no
  dest:
    description:
      - destination file name with absolute path
    default: filename from src and at default directory of user shell on
             network_os
    required: no

requirements:
    - "scp"

notes:
   - Some devices need specific configurations to be enabled before scp can work
     These configuration should be pre-configued before using this module
     e.g ios - ip scp server enable
   - User privileage to do scp on network device should be pre-configured
     e.g. ios - need user privileage 15 by default for allowing scp
   - Default destination of source file
"""

EXAMPLES = """
- name: copy file from ansible controller to ios device
  network_put:
    src: running_cfg_ios1.txt

- name: copy file at root dir of flash in slot 3 of sw1(ios)
  network_put:
    src: running_cfg_sw1.txt
    protocol: sftp
    dest : flash3:/running_cfg_sw1.txt
"""

RETURN = """
"""
