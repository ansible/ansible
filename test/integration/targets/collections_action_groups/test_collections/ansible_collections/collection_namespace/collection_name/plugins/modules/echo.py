#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: echo
short_description: an echo module
version_added: "2.10"
description: a module that returns the options provided
options:
'''

import json

from ansible.module_utils import basic
from ansible.module_utils.basic import _load_params, AnsibleModule

def main():
    p = _load_params()
    d = json.loads(basic._ANSIBLE_ARGS)
    d['ANSIBLE_MODULE_ARGS'] = {}
    basic._ANSIBLE_ARGS = json.dumps(d).encode('utf-8')

    module = AnsibleModule(argument_spec={})
    module.exit_json(args_in=p)


if __name__ == '__main__':
    main()
