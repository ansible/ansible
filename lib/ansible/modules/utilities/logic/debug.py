#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: debug
short_description: Print statements during execution
description:
     - This module prints statements during execution and can be useful
       for debugging variables or expressions without necessarily halting
       the playbook. Useful for debugging together with the 'when:' directive.
     - This module is also supported for Windows targets.
version_added: "0.8"
options:
  msg:
    description:
      - The customized message that is printed. If omitted, prints a generic
        message.
    required: false
    default: "Hello world!"
  var:
    description:
      - A variable name to debug.  Mutually exclusive with the 'msg' option.
  verbosity:
    description:
      - A number that controls when the debug is run, if you set to 3 it will only run debug when -vvv or above
    required: False
    default: 0
    version_added: "2.1"
notes:
    - This module is also supported for Windows targets.
author:
    - "Dag Wieers (@dagwieers)"
    - "Michael DeHaan"
'''

EXAMPLES = '''
# Example that prints the loopback address and gateway for each host
- debug:
    msg: "System {{ inventory_hostname }} has uuid {{ ansible_product_uuid }}"

- debug:
    msg: "System {{ inventory_hostname }} has gateway {{ ansible_default_ipv4.gateway }}"
  when: ansible_default_ipv4.gateway is defined

- shell: /usr/bin/uptime
  register: result

- debug:
    var: result
    verbosity: 2

- name: Display all variables/facts known for a host
  debug:
    var: hostvars[inventory_hostname]
    verbosity: 4
'''
