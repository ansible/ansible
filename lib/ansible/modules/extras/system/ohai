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
module: ohai
short_description: Returns inventory data from I(Ohai)
description:
     - Similar to the M(facter) module, this runs the I(Ohai) discovery program
       (U(http://wiki.opscode.com/display/chef/Ohai)) on the remote host and 
       returns JSON inventory data.
       I(Ohai) data is a bit more verbose and nested than I(facter).
version_added: "0.6"
options: {}
notes: []
requirements: [ "ohai" ]
author: Michael DeHaan
'''

EXAMPLES = '''
# Retrieve (ohai) data from all Web servers and store in one-file per host
ansible webservers -m ohai --tree=/tmp/ohaidata
'''

def main():
    module = AnsibleModule(
        argument_spec = dict()
    )
    cmd = ["/usr/bin/env", "ohai"]
    rc, out, err = module.run_command(cmd, check_rc=True)
    module.exit_json(**json.loads(out))

# import module snippets
from ansible.module_utils.basic import *

main()


