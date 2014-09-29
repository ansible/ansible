#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Derek Carter<goozbach@friocorte.com>
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

DOCUMENTATION = '''
---
module: selinux
short_description: Change policy and state of SELinux
description:
  - Configures the SELinux mode and policy. A reboot may be required after usage. Ansible will not issue this reboot but will let you know when it is required.
version_added: "0.7"
options:
  policy:
    description:
      - "name of the SELinux policy to use (example: C(targeted)) will be required if state is not C(disabled)"
    required: false
    default: null
  state:
    description:
      - The SELinux mode
    required: true
    default: null
    choices: [ "enforcing", "permissive", "disabled" ]
  conf:
    description:
      - path to the SELinux configuration file, if non-standard
    required: false
    default: "/etc/selinux/config"
notes:
   - Not tested on any debian based system
requirements: [ libselinux-python ]
author: Derek Carter <goozbach@friocorte.com>
'''

EXAMPLES = '''
- selinux: policy=targeted state=enforcing
- selinux: policy=targeted state=permissive
- selinux: state=disabled
'''

import os
import re
import sys

try:
    import selinux
except ImportError:
    print "failed=True msg='libselinux-python required for this module'"
    sys.exit(1)

# getter subroutines
def get_config_state(configfile):
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    for line in lines:
        stateline = re.match('^SELINUX=.*$', line)
        if (stateline):
            return(line.split('=')[1].strip())

def get_config_policy(configfile):
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    for line in lines:
        stateline = re.match('^SELINUXTYPE=.*$', line)
        if (stateline):
            return(line.split('=')[1].strip())

# setter subroutines
def set_config_state(state, configfile):
    #SELINUX=permissive
    # edit config file with state value
    stateline='SELINUX=%s' % state
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    myfile = open(configfile, "w")
    for line in lines:
        myfile.write(re.sub(r'^SELINUX=.*', stateline, line))
    myfile.close()

def set_state(state):
    if (state == 'enforcing'):
        selinux.security_setenforce(1)
    elif (state == 'permissive'):
        selinux.security_setenforce(0)
    elif (state == 'disabled'):
        pass
    else:
        msg = 'trying to set invalid runtime state %s' % state
        module.fail_json(msg=msg)

def set_config_policy(policy, configfile):
    # edit config file with state value
    #SELINUXTYPE=targeted
    policyline='SELINUXTYPE=%s' % policy
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    myfile = open(configfile, "w")
    for line in lines:
        myfile.write(re.sub(r'^SELINUXTYPE=.*', policyline, line))
    myfile.close()

def main():

    module = AnsibleModule(
        argument_spec = dict(
            policy=dict(required=False),
            state=dict(choices=['enforcing', 'permissive', 'disabled'], required=True),
            configfile=dict(aliases=['conf','file'], default='/etc/selinux/config')
        ),
        supports_check_mode=True
    )

    # global vars
    changed=False
    msgs                  = []
    configfile            = module.params['configfile']
    policy                = module.params['policy']
    state                 = module.params['state']
    runtime_enabled       = selinux.is_selinux_enabled()
    runtime_policy        = selinux.selinux_getpolicytype()[1]
    runtime_state         = 'disabled'
    if (runtime_enabled):
        # enabled means 'enforcing' or 'permissive'
        if (selinux.security_getenforce()):
            runtime_state = 'enforcing'
        else:
            runtime_state = 'permissive'
    config_policy         = get_config_policy(configfile)
    config_state          = get_config_state(configfile)

    # check to see if policy is set if state is not 'disabled'
    if (state != 'disabled'):
        if not policy:
            module.fail_json(msg='policy is required if state is not \'disabled\'')
    else:
        if not policy:
            policy = config_policy

    # check changed values and run changes
    if (policy != runtime_policy):
        if module.check_mode:
            module.exit_json(changed=True)
        # cannot change runtime policy
        msgs.append('reboot to change the loaded policy')
        changed=True

    if (policy != config_policy):
        if module.check_mode:
            module.exit_json(changed=True)
        msgs.append('config policy changed from \'%s\' to \'%s\'' % (config_policy, policy))
        set_config_policy(policy, configfile)
        changed=True

    if (state != runtime_state):
        if module.check_mode:
            module.exit_json(changed=True)
        if (runtime_enabled):
            if (state == 'disabled'):
                if (runtime_state != 'permissive'):
                    # Temporarily set state to permissive
                    set_state('permissive')
                    msgs.append('runtime state temporarily changed from \'%s\' to \'permissive\', state change will take effect next reboot' % (runtime_state))
                else:
                    msgs.append('state change will take effect next reboot')
            else:
                set_state(state)
                msgs.append('runtime state changed from \'%s\' to \'%s\'' % (runtime_state, state))
        else:
            msgs.append('state change will take effect next reboot')
        changed=True

    if (state != config_state):
        if module.check_mode:
            module.exit_json(changed=True)
        msgs.append('config state changed from \'%s\' to \'%s\'' % (config_state, state))
        set_config_state(state, configfile)
        changed=True

    module.exit_json(changed=changed, msg=', '.join(msgs),
        configfile=configfile,
        policy=policy, state=state)

#################################################
# import module snippets
from ansible.module_utils.basic import *

main()

