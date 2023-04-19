# -*- coding: utf-8 -*-

# Copyright 2021 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re

from __future__ import absolute_import, division, print_function
__metaclass__ = type

def validate_mac_address(mac):
    """
    Validates a MAC address in the format xx:xx:xx:xx:xx:xx, where x is a hexadecimal digit.
    """
    pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    return bool(re.match(pattern, mac))

def validate_ipv4_address(ip):
    """
    Validates an IPv4 address in dotted decimal notation.
    """
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    return bool(re.match(pattern, ip))

def validate_ipv6_address(ip):
    """
    Validates an IPv6 address in hexadecimal notation.
    """
    pattern = r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$"
    return bool(re.match(pattern, ip, re.I))

def validate_ipv4_prefix(prefix):
    """
    Validates an IPv4 prefix in CIDR notation.
    """
    pattern = r"^(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
    return bool(re.match(pattern, prefix))

def validate_ipv6_prefix(prefix):
    """
    Validates an IPv6 prefix in CIDR notation.
    """
    pattern = r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}/\d{1,3}$"
    return bool(re.match(pattern, prefix, re.I))



DOCUMENTATION = r'''
---
module: validate_argument_spec
short_description: Validate role argument specs.
description:
     - This module validates role arguments with a defined argument specification.
version_added: "2.11"
options:
  argument_spec:
    description:
        - A dictionary like AnsibleModule argument_spec
    required: true
  provided_arguments:
    description:
        - A dictionary of the arguments that will be validated according to argument_spec
author:
    - Ansible Core Team
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.conn
    - action_common_attributes.flow
attributes:
    action:
        support: full
    async:
        support: none
    become:
        support: none
    bypass_host_loop:
        support: none
    connection:
        support: none
    check_mode:
        support: full
    delegation:
        support: none
    diff_mode:
        support: none
    platform:
        platforms: all
'''

EXAMPLES = r'''
- name: verify vars needed for this task file are present when included
  ansible.builtin.validate_argument_spec:
        argument_spec: '{{required_data}}'
  vars:
    required_data:
        # unlike spec file, just put the options in directly
        stuff:
            description: stuff
            type: str
            choices: ['who', 'knows', 'what']
            default: what
        but:
            description: i guess we need one
            type: str
            required: true


- name: verify vars needed for this task file are present when included, with spec from a spec file
  ansible.builtin.validate_argument_spec:
        argument_spec: "{{(lookup('ansible.builtin.file', 'myargspec.yml') | from_yaml )['specname']['options']}}"


- name: verify vars needed for next include and not from inside it, also with params i'll only define there
  block:
    - ansible.builtin.validate_argument_spec:
        argument_spec: "{{lookup('ansible.builtin.file', 'nakedoptions.yml'}}"
        provided_arguments:
            but: "that i can define on the include itself, like in it's C(vars:) keyword"

    - name: the include itself
      vars:
        stuff: knows
        but: nobuts!
'''

RETURN = r'''
argument_errors:
  description: A list of arg validation errors.
  returned: failure
  type: list
  elements: str
  sample:
    - "error message 1"
    - "error message 2"

argument_spec_data:
  description: A dict of the data from the 'argument_spec' arg.
  returned: failure
  type: dict
  sample:
    some_arg:
      type: "str"
    some_other_arg:
      type: "int"
      required: true

validate_args_context:
  description: A dict of info about where validate_args_spec was used
  type: dict
  returned: always
  sample:
    name: my_role
    type: role
    path: /home/user/roles/my_role/
    argument_spec_name: main
'''
