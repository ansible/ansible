#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: facter
short_description: Runs the discovery program I(facter) on the remote system
description:
     - Runs the I(facter) discovery program
       (U(https://github.com/puppetlabs/facter)) on the remote system, returning
       JSON data that can be useful for inventory purposes.
version_added: "0.2"
options: {}
notes: []
requirements: [ "facter", "ruby-json" ]
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
'''

EXAMPLES = '''
# Example command-line invocation
ansible www.example.net -m facter
'''
import json

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec = dict()
    )

    facter_path = module.get_bin_path('facter', opt_dirs=['/opt/puppetlabs/bin'])

    cmd = [facter_path, "--puppet", "--json"]

    rc, out, err = module.run_command(cmd, check_rc=True)
    module.exit_json(**json.loads(out))


if __name__ == '__main__':
    main()
