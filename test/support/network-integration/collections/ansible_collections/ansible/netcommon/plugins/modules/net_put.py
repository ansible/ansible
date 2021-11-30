#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "network",
}


DOCUMENTATION = """module: net_put
author: Deepak Agrawal (@dagrawal)
short_description: Copy a file from Ansible Controller to a network device
description:
- This module provides functionality to copy file from Ansible controller to network
  devices.
extends_documentation_fragment:
- ansible.netcommon.network_agnostic
options:
  src:
    description:
    - Specifies the source file. The path to the source file can either be the full
      path on the Ansible control host or a relative path from the playbook or role
      root directory.
    required: true
  protocol:
    description:
    - Protocol used to transfer file.
    default: scp
    choices:
    - scp
    - sftp
  dest:
    description:
    - Specifies the destination file. The path to destination file can either be the
      full path or relative path as supported by network_os.
    default:
    - Filename from src and at default directory of user shell on network_os.
    required: false
  mode:
    description:
    - Set the file transfer mode. If mode is set to I(text) then I(src) file will
      go through Jinja2 template engine to replace any vars if present in the src
      file. If mode is set to I(binary) then file will be copied as it is to destination
      device.
    default: binary
    choices:
    - binary
    - text
requirements:
- scp
notes:
- Some devices need specific configurations to be enabled before scp can work These
  configuration should be pre-configured before using this module e.g ios - C(ip scp
  server enable).
- User privilege to do scp on network device should be pre-configured e.g. ios - need
  user privilege 15 by default for allowing scp.
- Default destination of source file.
"""

EXAMPLES = """
- name: copy file from ansible controller to a network device
  net_put:
    src: running_cfg_ios1.txt

- name: copy file at root dir of flash in slot 3 of sw1(ios)
  net_put:
    src: running_cfg_sw1.txt
    protocol: sftp
    dest : flash3:/running_cfg_sw1.txt
"""

RETURN = """
"""
