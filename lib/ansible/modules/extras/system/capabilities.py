#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Nate Coraor <nate@bx.psu.edu>
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
module: capabilities
short_description: Manage Linux capabilities
description:
    - This module manipulates files privileges using the Linux capabilities(7) system.
version_added: "1.6"
options:
    path:
        description:
            - Specifies the path to the file to be managed.
        required: true
        default: null
    capability:
        description:
            - Desired capability to set (with operator and flags, if state is C(present)) or remove (if state is C(absent))
        required: true
        default: null
        aliases: [ 'cap' ]
    state:
        description:
            - Whether the entry should be present or absent in the file's capabilities.
        choices: [ "present", "absent" ]
        default: present
notes:
    - The capabilities system will automatically transform operators and flags
      into the effective set, so (for example, cap_foo=ep will probably become
      cap_foo+ep). This module does not attempt to determine the final operator
      and flags to compare, so you will want to ensure that your capabilities
      argument matches the final capabilities.
requirements: []
author: "Nate Coraor (@natefoo)"
'''

EXAMPLES = '''
# Set cap_sys_chroot+ep on /foo
- capabilities: path=/foo capability=cap_sys_chroot+ep state=present

# Remove cap_net_bind_service from /bar
- capabilities: path=/bar capability=cap_net_bind_service state=absent
'''


OPS = ( '=', '-', '+' )

# ==============================================================

import os
import tempfile
import re

class CapabilitiesModule(object):

    platform = 'Linux'
    distribution = None

    def __init__(self, module):
        self.module         = module 
        self.path           = module.params['path'].strip()
        self.capability     = module.params['capability'].strip().lower()
        self.state          = module.params['state']
        self.getcap_cmd     = module.get_bin_path('getcap', required=True)
        self.setcap_cmd     = module.get_bin_path('setcap', required=True)
        self.capability_tup = self._parse_cap(self.capability, op_required=self.state=='present')

        self.run()

    def run(self):

        current = self.getcap(self.path)
        caps = [ cap[0] for cap in current ]

        if self.state == 'present' and self.capability_tup not in current:
            # need to add capability
            if self.module.check_mode:
                self.module.exit_json(changed=True, msg='capabilities changed')
            else:
                # remove from current cap list if it's already set (but op/flags differ)
                current = filter(lambda x: x[0] != self.capability_tup[0], current)
                # add new cap with correct op/flags
                current.append( self.capability_tup )
                self.module.exit_json(changed=True, state=self.state, msg='capabilities changed', stdout=self.setcap(self.path, current))
        elif self.state == 'absent' and self.capability_tup[0] in caps:
            # need to remove capability
            if self.module.check_mode:
                self.module.exit_json(changed=True, msg='capabilities changed')
            else:
                # remove from current cap list and then set current list
                current = filter(lambda x: x[0] != self.capability_tup[0], current)
                self.module.exit_json(changed=True, state=self.state, msg='capabilities changed', stdout=self.setcap(self.path, current))
        self.module.exit_json(changed=False, state=self.state)

    def getcap(self, path):
        rval = []
        cmd = "%s -v %s" % (self.getcap_cmd, path)
        rc, stdout, stderr = self.module.run_command(cmd)    
        # If file xattrs are set but no caps are set the output will be:
        #   '/foo ='
        # If file xattrs are unset the output will be:
        #   '/foo'
        # If the file does not eixst the output will be (with rc == 0...):
        #   '/foo (No such file or directory)'
        if rc != 0 or (stdout.strip() != path and stdout.count(' =') != 1):
            self.module.fail_json(msg="Unable to get capabilities of %s" % path, stdout=stdout.strip(), stderr=stderr)
        if stdout.strip() != path:
            caps = stdout.split(' =')[1].strip().split()
            for cap in caps:
                cap = cap.lower()
                # getcap condenses capabilities with the same op/flags into a
                # comma-separated list, so we have to parse that
                if ',' in cap:
                    cap_group = cap.split(',')
                    cap_group[-1], op, flags = self._parse_cap(cap_group[-1])
                    for subcap in cap_group:
                        rval.append( ( subcap, op, flags ) )
                else:
                    rval.append(self._parse_cap(cap))
        return rval

    def setcap(self, path, caps):
        caps = ' '.join([ ''.join(cap) for cap in caps ])
        cmd = "%s '%s' %s" % (self.setcap_cmd, caps, path)
        rc, stdout, stderr = self.module.run_command(cmd)    
        if rc != 0:
            self.module.fail_json(msg="Unable to set capabilities of %s" % path, stdout=stdout, stderr=stderr)
        else:
            return stdout

    def _parse_cap(self, cap, op_required=True):
        opind = -1
        try:
            i = 0
            while opind == -1:
                opind = cap.find(OPS[i])
                i += 1
        except:
            if op_required:
                self.module.fail_json(msg="Couldn't find operator (one of: %s)" % str(OPS))
            else:
                return (cap, None, None)
        op = cap[opind]
        cap, flags = cap.split(op)
        return (cap, op, flags)

# ==============================================================
# main

def main():

    # defining module
    module = AnsibleModule(
        argument_spec = dict(
            path = dict(aliases=['key'], required=True),
            capability = dict(aliases=['cap'], required=True),
            state = dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    CapabilitiesModule(module)


# import module snippets
from ansible.module_utils.basic import *
main()
