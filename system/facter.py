#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


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

def main():
    module = AnsibleModule(
        argument_spec = dict()
    )

    facter_path = module.get_bin_path('facter', opt_dirs=['/opt/puppetlabs/bin'])

    cmd = [facter_path, "--puppet", "--json"]

    rc, out, err = module.run_command(cmd, check_rc=True)
    module.exit_json(**json.loads(out))

# import module snippets
from ansible.module_utils.basic import *

main()

